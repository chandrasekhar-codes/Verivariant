from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config import Settings, get_settings
from app.models import GenomeBuild, Report, Variant
from app.parsing.vcf_parser import ParseResult

_lock = threading.Lock()
_jobs: dict[str, JobRecord] = {}
_reports: dict[str, Report] = {}


@dataclass
class JobRecord:
    job_id: str
    created_at: datetime
    genome_build: GenomeBuild
    genome_build_source: str
    vcf_path: Path
    variants: list[Variant]
    warnings: list[str] = field(default_factory=list)
    status: str = "uploaded"
    report: Report | None = None

    def to_meta(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "created_at": self.created_at.isoformat(),
            "genome_build": self.genome_build.value,
            "genome_build_source": self.genome_build_source,
            "vcf_path": str(self.vcf_path),
            "variant_count": len(self.variants),
            "warnings": self.warnings,
            "status": self.status,
            "has_report": self.report is not None,
        }


def new_job_id() -> str:
    return uuid4().hex


def save_job(record: JobRecord) -> None:
    with _lock:
        _jobs[record.job_id] = record
    try:
        meta_path = record.vcf_path.with_suffix(record.vcf_path.suffix + ".meta.json")
        if record.vcf_path.name.endswith(".vcf.gz"):
            meta_path = Path(str(record.vcf_path) + ".meta.json")
        meta_path.write_text(json.dumps(record.to_meta(), indent=2), encoding="utf-8")
        variants_path = Path(str(record.vcf_path) + ".variants.json")
        variants_path.write_text(
            json.dumps([v.model_dump(mode="json") for v in record.variants], indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def save_report(job_id: str, report: Report) -> None:
    with _lock:
        _reports[job_id] = report
        job = _jobs.get(job_id)
        if job:
            job.report = report
            job.status = "completed"
    if job:
        try:
            report_path = Path(str(job.vcf_path) + ".report.json")
            report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        except OSError:
            pass


def get_job(job_id: str) -> JobRecord | None:
    with _lock:
        return _jobs.get(job_id)


def get_report(job_id: str) -> Report | None:
    with _lock:
        if job_id in _reports:
            return _reports[job_id]
        job = _jobs.get(job_id)
        if job and job.report:
            return job.report
    # Try reading from disk if server restarted
    settings = get_settings()
    disk_path = settings.uploads_dir / f"{job_id}.vcf.report.json"
    if disk_path.exists():
        try:
            data = json.loads(disk_path.read_text(encoding="utf-8"))
            rep = Report.model_validate(data)
            with _lock:
                _reports[job_id] = rep
            return rep
        except Exception:
            pass
    return None


def update_job_status(job_id: str, status: str) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if job:
            job.status = status


def clear_jobs() -> None:
    with _lock:
        _jobs.clear()
        _reports.clear()


def purge_expired(settings: Settings | None = None) -> int:
    settings = settings or get_settings()
    cutoff = datetime.now(UTC) - timedelta(hours=settings.upload_ttl_hours)
    removed = 0
    with _lock:
        expired = [jid for jid, rec in _jobs.items() if rec.created_at < cutoff]
        for jid in expired:
            rec = _jobs.pop(jid)
            _reports.pop(jid, None)
            _delete_job_files(rec.vcf_path)
            removed += 1
    return removed


def _delete_job_files(vcf_path: Path) -> None:
    for path in (
        vcf_path,
        Path(str(vcf_path) + ".meta.json"),
        Path(str(vcf_path) + ".variants.json"),
        Path(str(vcf_path) + ".report.json"),
        vcf_path.with_suffix(vcf_path.suffix + ".meta.json"),
    ):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def record_from_parse(
    *,
    job_id: str,
    vcf_path: Path,
    parsed: ParseResult,
) -> JobRecord:
    return JobRecord(
        job_id=job_id,
        created_at=datetime.now(UTC),
        genome_build=parsed.genome_build,
        genome_build_source=parsed.genome_build_source,
        vcf_path=vcf_path,
        variants=parsed.variants,
        warnings=parsed.warnings,
        status="uploaded",
    )
