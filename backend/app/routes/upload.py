from __future__ import annotations

import shutil
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.config import DISCLAIMER, get_settings
from app.jobs import new_job_id, purge_expired, record_from_parse, save_job
from app.models import GenomeBuild, Variant
from app.parsing.vcf_parser import VCFParseError, parse_vcf

router = APIRouter()


class UploadResponse(BaseModel):
    job_id: str
    genome_build: GenomeBuild
    genome_build_source: str
    variant_count: int
    variants: list[Variant]
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = DISCLAIMER


def _is_allowed_name(name: str) -> bool:
    lower = name.lower()
    return lower.endswith((".vcf", ".vcf.gz"))


@router.post("/upload", response_model=UploadResponse)
async def upload_vcf(
    file: Annotated[UploadFile | None, File()] = None,
    demo: bool = Query(False),
    genome_build: GenomeBuild | None = Query(default=None),
) -> UploadResponse:
    settings = get_settings()
    purge_expired(settings)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)

    job_id = new_job_id()
    if demo:
        source = settings.sample_data_dir / "demo.vcf"
        if not source.exists():
            raise HTTPException(
                status_code=404,
                detail=(
                    "Demo VCF is not installed yet. It is built from public records in a later "
                    "phase (scripts/build_demo_vcf.py)."
                ),
            )
        dest = settings.uploads_dir / f"{job_id}.vcf"
        shutil.copyfile(source, dest)
    else:
        if file is None or not file.filename:
            raise HTTPException(status_code=400, detail="Upload a .vcf or .vcf.gz file.")
        original_name = file.filename
        if not _is_allowed_name(original_name):
            raise HTTPException(status_code=400, detail="Only .vcf and .vcf.gz files are accepted.")
        suffix = ".vcf.gz" if original_name.lower().endswith(".vcf.gz") else ".vcf"
        dest = settings.uploads_dir / f"{job_id}{suffix}"
        max_bytes = settings.max_upload_mb * 1024 * 1024
        written = 0
        try:
            with dest.open("wb") as out:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_bytes:
                        out.close()
                        dest.unlink(missing_ok=True)
                        raise HTTPException(
                            status_code=413,
                            detail=f"File exceeds the {settings.max_upload_mb} MB upload limit.",
                        )
                    out.write(chunk)
        finally:
            await file.close()
        if written == 0:
            dest.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        parsed = parse_vcf(
            dest,
            genome_build=genome_build,
            max_variants=settings.max_variants,
        )
    except VCFParseError as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    record = record_from_parse(job_id=job_id, vcf_path=dest, parsed=parsed)
    save_job(record)
    return UploadResponse(
        job_id=job_id,
        genome_build=parsed.genome_build,
        genome_build_source=parsed.genome_build_source,
        variant_count=len(parsed.variants),
        variants=parsed.variants,
        warnings=parsed.warnings,
        disclaimer=DISCLAIMER,
    )
