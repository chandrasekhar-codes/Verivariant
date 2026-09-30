"""GENESIS Analysis and Multi-Agent API Routes.

Implements:
- POST /api/analyze-vcf
- GET /api/analysis/{analysis_id}
- GET /api/variant/{analysis_id}/{variant_id}
- POST /api/verify
- GET /api/report/{analysis_id}
- POST /api/demo
"""

from __future__ import annotations

import shutil
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.agents.verification_agent import verify_single_claim
from app.config import DISCLAIMER, get_settings
from app.jobs import (
    get_job,
    get_report,
    new_job_id,
    purge_expired,
    record_from_parse,
    save_job,
    save_report,
)
from app.models import (
    Claim,
    ClaimVerification,
    EvidenceItem,
    GenomeBuild,
    Report,
    Variant,
    VariantReport,
)
from app.parsing.vcf_parser import VCFParseError, parse_vcf
from app.pipeline import run_analysis_pipeline

router = APIRouter()


class VerifyRequest(BaseModel):
    claim: Claim
    evidence_items: list[EvidenceItem]


class VerifyResponse(BaseModel):
    claim_id: str
    verification: ClaimVerification
    disclaimer: str = DISCLAIMER


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str
    variant_count: int
    genome_build: str
    variants: list[Variant]
    has_report: bool
    disclaimer: str = DISCLAIMER


def _is_allowed_name(name: str) -> bool:
    lower = name.lower()
    return lower.endswith((".vcf", ".vcf.gz", ".bgz")) or (lower.endswith(".gz") and ".vcf" in lower)


@router.post("/analyze-vcf", response_model=Report)
async def analyze_vcf(
    file: Annotated[UploadFile | None, File()] = None,
    demo: bool = Query(False),
    genome_build: str | None = Query(default=None),
) -> Report:
    """Upload a VCF or use demo data, parse variants, and run the full multi-agent pipeline."""
    settings = get_settings()
    purge_expired(settings)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)

    job_id = new_job_id()

    if demo:
        source = settings.sample_data_dir / "demo.vcf"
        if not source.exists():
            raise HTTPException(
                status_code=404,
                detail="Demo VCF file not found at sample_data/demo.vcf",
            )
        dest = settings.uploads_dir / f"{job_id}.vcf"
        shutil.copyfile(source, dest)
    else:
        if file is None or not file.filename:
            raise HTTPException(status_code=400, detail="Please upload a .vcf or .vcf.gz file.")
        if not _is_allowed_name(file.filename):
            raise HTTPException(status_code=400, detail="Only .vcf and .vcf.gz files are accepted.")

        lower_name = file.filename.lower()
        suffix = ".vcf.gz" if lower_name.endswith((".vcf.gz", ".gz", ".bgz")) else ".vcf"
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
                            detail=f"File exceeds {settings.max_upload_mb} MB upload limit.",
                        )
                    out.write(chunk)
        finally:
            await file.close()

        if written == 0:
            dest.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    target_build: GenomeBuild | None = None
    if genome_build:
        gb_clean = genome_build.strip().lower()
        if "37" in gb_clean or "19" in gb_clean:
            target_build = GenomeBuild.grch37
        elif "38" in gb_clean:
            target_build = GenomeBuild.grch38

    # Parse VCF
    try:
        parsed = parse_vcf(
            dest,
            genome_build=target_build,
            max_variants=settings.max_variants,
            cap_variants=True,
        )
    except VCFParseError as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not parsed.variants:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="No valid genomic variants found in VCF file.")

    record = record_from_parse(job_id=job_id, vcf_path=dest, parsed=parsed)
    record.status = "analyzing"
    save_job(record)

    # Run multi-agent pipeline
    report = await run_analysis_pipeline(
        job_id=job_id,
        variants=parsed.variants,
        genome_build=parsed.genome_build,
        is_demo=demo,
    )

    save_report(job_id, report)
    return report


@router.post("/demo", response_model=Report)
async def run_demo_analysis(
    genome_build: GenomeBuild | None = Query(default=None),
) -> Report:
    """Instant 1-click endpoint to execute full demo analysis on bundled clinically annotated VCF."""
    build_val = genome_build if isinstance(genome_build, GenomeBuild) else None
    return await analyze_vcf(demo=True, genome_build=build_val)


@router.get("/analysis/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str) -> AnalysisStatusResponse:
    """Retrieve status and parsed variants of an analysis job."""
    job = get_job(analysis_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found.")

    return AnalysisStatusResponse(
        analysis_id=job.job_id,
        status=job.status,
        variant_count=len(job.variants),
        genome_build=job.genome_build.value,
        variants=job.variants,
        has_report=job.report is not None,
        disclaimer=DISCLAIMER,
    )


@router.get("/report/{analysis_id}", response_model=Report)
async def get_analysis_report(analysis_id: str) -> Report:
    """Retrieve generated multi-agent report for an analysis ID."""
    report = get_report(analysis_id)
    if not report:
        job = get_job(analysis_id)
        if job and job.status == "analyzing":
            raise HTTPException(status_code=202, detail="Analysis currently in progress.")
        raise HTTPException(status_code=404, detail="Report not found for this analysis ID.")
    return report


@router.get("/variant/{analysis_id}/{variant_id}", response_model=VariantReport)
async def get_variant_details(analysis_id: str, variant_id: str) -> VariantReport:
    """Retrieve detailed evidence, claims, and verification for a specific variant within an analysis."""
    report = get_report(analysis_id)
    if not report:
        raise HTTPException(status_code=404, detail="Analysis report not found.")

    clean_var_id = variant_id.strip()
    for vr in report.variants:
        if (
            vr.variant.id == clean_var_id
            or vr.variant.key == clean_var_id
            or vr.variant.rsid == clean_var_id
        ):
            return vr

    raise HTTPException(status_code=404, detail=f"Variant '{variant_id}' not found in report.")


@router.post("/verify", response_model=VerifyResponse)
async def verify_claim_endpoint(req: VerifyRequest) -> VerifyResponse:
    """Independent Verification Agent endpoint to check a claim against evidence."""
    verification = verify_single_claim(req.claim, req.evidence_items)
    return VerifyResponse(
        claim_id=req.claim.id,
        verification=verification,
        disclaimer=DISCLAIMER,
    )


@router.get("/jobs")
async def list_analysis_jobs(limit: int = Query(20, ge=1, le=100)) -> dict:
    """List recent analysis jobs from Supabase."""
    from app.database import is_enabled, list_jobs

    if not is_enabled():
        return {
            "database": "not_configured",
            "jobs": [],
            "message": "Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY in .env.",
        }

    jobs = list_jobs(limit=limit)
    return {
        "database": "supabase",
        "jobs": jobs,
        "total": len(jobs),
    }


@router.get("/db-status")
async def database_status() -> dict:
    """Check Supabase database connectivity."""
    from app.database import is_enabled

    return {
        "database": "supabase" if is_enabled() else "file_only",
        "connected": is_enabled(),
        "message": (
            "Connected to Supabase"
            if is_enabled()
            else "Supabase not configured — using file-based persistence"
        ),
    }
