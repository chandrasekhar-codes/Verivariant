"""Supabase database service layer.

Provides persistent storage for analysis jobs, variants, evidence,
claims, and reports. Gracefully falls back to no-op if Supabase
is not configured (demo mode still works via file-based persistence).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supabase client singleton
# ---------------------------------------------------------------------------

_client = None
_enabled = False


def _get_client():
    """Lazy-init and return the Supabase client, or None if not configured."""
    global _client, _enabled

    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")

    if not url or not key:
        logger.info("Supabase not configured — using file-based persistence only.")
        _enabled = False
        return None

    try:
        from supabase import Client, create_client

        _client = create_client(url, key)
        _enabled = True
        logger.info("Supabase connected: %s", url)
        return _client
    except Exception as exc:
        logger.warning("Supabase init failed (falling back to file): %s", exc)
        _enabled = False
        return None


def is_enabled() -> bool:
    """Return True if Supabase is configured and connected."""
    _get_client()
    return _enabled


# ---------------------------------------------------------------------------
# Analysis Jobs
# ---------------------------------------------------------------------------


def create_job(
    job_id: str,
    filename: str,
    genome_build: str,
    is_demo: bool = False,
) -> dict[str, Any] | None:
    """Insert a new analysis job record."""
    client = _get_client()
    if not client:
        return None

    try:
        row = {
            "id": job_id,
            "filename": filename,
            "genome_build": genome_build,
            "status": "pending",
            "is_demo": is_demo,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = client.table("analysis_jobs").insert(row).execute()
        logger.debug("Job created in Supabase: %s", job_id)
        return result.data[0] if result.data else row
    except Exception as exc:
        logger.warning("Failed to create job in Supabase: %s", exc)
        return None


def update_job_status(
    job_id: str,
    status: str,
    total_variants: int = 0,
    total_claims: int = 0,
    supported_claims: int = 0,
    unsupported_claims: int = 0,
) -> dict[str, Any] | None:
    """Update an existing job's status and counts."""
    client = _get_client()
    if not client:
        return None

    try:
        updates: dict[str, Any] = {"status": status}
        if total_variants:
            updates["total_variants"] = total_variants
        if total_claims:
            updates["total_claims"] = total_claims
        if supported_claims:
            updates["supported_claims"] = supported_claims
        if unsupported_claims:
            updates["unsupported_claims"] = unsupported_claims
        if status in ("completed", "failed"):
            updates["completed_at"] = datetime.now(timezone.utc).isoformat()

        result = (
            client.table("analysis_jobs")
            .update(updates)
            .eq("id", job_id)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as exc:
        logger.warning("Failed to update job status: %s", exc)
        return None


def get_job(job_id: str) -> dict[str, Any] | None:
    """Fetch a single job by ID."""
    client = _get_client()
    if not client:
        return None

    try:
        result = (
            client.table("analysis_jobs")
            .select("*")
            .eq("id", job_id)
            .single()
            .execute()
        )
        return result.data
    except Exception as exc:
        logger.warning("Failed to get job: %s", exc)
        return None


def list_jobs(limit: int = 20) -> list[dict[str, Any]]:
    """List recent analysis jobs."""
    client = _get_client()
    if not client:
        return []

    try:
        result = (
            client.table("analysis_jobs")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.warning("Failed to list jobs: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Variants
# ---------------------------------------------------------------------------


def insert_variants(
    job_id: str,
    variants: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Batch-insert parsed variants for a job."""
    client = _get_client()
    if not client:
        return []

    try:
        rows = []
        for v in variants:
            rows.append(
                {
                    "id": v.get("id", str(uuid4())),
                    "job_id": job_id,
                    "chrom": v.get("chrom", ""),
                    "pos": v.get("pos", 0),
                    "ref_allele": v.get("ref", ""),
                    "alt_allele": v.get("alt", ""),
                    "rsid": v.get("rsid"),
                    "gene": v.get("gene"),
                    "variant_key": v.get("key", f"{v.get('chrom')}:{v.get('pos')}"),
                    "clinvar_sig": v.get("clinvar_sig"),
                    "gnomad_af": v.get("gnomad_af"),
                    "consequence": v.get("consequence"),
                    "genome_build": v.get("genome_build", "GRCh38"),
                    "info": json.dumps(v.get("info", {})),
                }
            )

        result = client.table("variants").insert(rows).execute()
        logger.debug("Inserted %d variants for job %s", len(rows), job_id)
        return result.data or rows
    except Exception as exc:
        logger.warning("Failed to insert variants: %s", exc)
        return []


def get_variants_for_job(job_id: str) -> list[dict[str, Any]]:
    """Fetch all variants belonging to a job."""
    client = _get_client()
    if not client:
        return []

    try:
        result = (
            client.table("variants")
            .select("*")
            .eq("job_id", job_id)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.warning("Failed to get variants: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Evidence Items
# ---------------------------------------------------------------------------


def insert_evidence(
    variant_id: str,
    evidence_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Batch-insert evidence items for a variant."""
    client = _get_client()
    if not client:
        return []

    try:
        rows = []
        for e in evidence_items:
            rows.append(
                {
                    "id": str(uuid4()),
                    "variant_id": variant_id,
                    "source": e.get("source", "unknown"),
                    "status": e.get("status", "success"),
                    "url": e.get("url"),
                    "data": json.dumps(e.get("data", {})),
                    "retrieved_at": e.get(
                        "retrieved_at",
                        datetime.now(timezone.utc).isoformat(),
                    ),
                    "is_demo_data": e.get("is_demo_data", False),
                    "error_message": e.get("error_message"),
                }
            )

        result = client.table("evidence_items").insert(rows).execute()
        logger.debug(
            "Inserted %d evidence items for variant %s", len(rows), variant_id
        )
        return result.data or rows
    except Exception as exc:
        logger.warning("Failed to insert evidence: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Claims
# ---------------------------------------------------------------------------


def insert_claims(
    variant_id: str,
    claims: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Batch-insert claims for a variant."""
    client = _get_client()
    if not client:
        return []

    try:
        rows = []
        for c in claims:
            verification = c.get("verification", {}) or {}
            rows.append(
                {
                    "id": c.get("claim_id", str(uuid4())),
                    "variant_id": variant_id,
                    "claim_text": c.get("claim", ""),
                    "source": c.get("source", ""),
                    "source_url": c.get("source_url"),
                    "confidence": c.get("confidence", 0.0),
                    "verification_verdict": verification.get("verdict"),
                    "verification_reasoning": verification.get("reasoning"),
                    "verification_confidence": verification.get("confidence"),
                }
            )

        result = client.table("claims").insert(rows).execute()
        logger.debug("Inserted %d claims for variant %s", len(rows), variant_id)
        return result.data or rows
    except Exception as exc:
        logger.warning("Failed to insert claims: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


def insert_report(
    job_id: str,
    report: dict[str, Any],
) -> dict[str, Any] | None:
    """Insert a completed report for a job."""
    client = _get_client()
    if not client:
        return None

    try:
        row = {
            "id": str(uuid4()),
            "job_id": job_id,
            "summary": report.get("summary", ""),
            "disclaimer": report.get("disclaimer", ""),
            "total_variants": report.get("total_variants", 0),
            "total_claims": report.get("total_claims", 0),
            "supported_claims": report.get("supported_claims", 0),
            "unsupported_claims": report.get("unsupported_claims", 0),
            "conflicts": json.dumps(report.get("conflicts", [])),
            "sources_used": report.get("sources_used", []),
            "limitations": report.get("limitations", []),
        }

        result = client.table("reports").insert(row).execute()
        logger.debug("Report saved for job %s", job_id)
        return result.data[0] if result.data else row
    except Exception as exc:
        logger.warning("Failed to insert report: %s", exc)
        return None


def insert_variant_summaries(
    report_id: str,
    variant_reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Insert per-variant summaries linked to a report."""
    client = _get_client()
    if not client:
        return []

    try:
        rows = []
        for vr in variant_reports:
            variant = vr.get("variant", {})
            rows.append(
                {
                    "id": str(uuid4()),
                    "report_id": report_id,
                    "variant_id": variant.get("id", str(uuid4())),
                    "summary": vr.get("summary", ""),
                    "conflicts": json.dumps(vr.get("conflicts", [])),
                }
            )

        result = client.table("variant_summaries").insert(rows).execute()
        return result.data or rows
    except Exception as exc:
        logger.warning("Failed to insert variant summaries: %s", exc)
        return []


def get_report_for_job(job_id: str) -> dict[str, Any] | None:
    """Fetch the report for a given job."""
    client = _get_client()
    if not client:
        return None

    try:
        result = (
            client.table("reports")
            .select("*")
            .eq("job_id", job_id)
            .single()
            .execute()
        )
        return result.data
    except Exception as exc:
        logger.warning("Failed to get report: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Full pipeline persistence helper
# ---------------------------------------------------------------------------


def persist_full_analysis(
    job_id: str,
    report_dict: dict[str, Any],
) -> bool:
    """Persist the entire analysis result to Supabase.

    Called after the pipeline completes. Takes the full report dict
    (matching the Report Pydantic model) and saves everything.

    Returns True if successful, False if Supabase is not configured
    or if any step fails (pipeline still succeeds via file fallback).
    """
    if not is_enabled():
        return False

    try:
        # 1. Update job status
        update_job_status(
            job_id=job_id,
            status="completed",
            total_variants=report_dict.get("total_variants", 0),
            total_claims=report_dict.get("total_claims", 0),
            supported_claims=report_dict.get("supported_claims", 0),
            unsupported_claims=report_dict.get("unsupported_claims", 0),
        )

        # 2. Insert variants, evidence, and claims
        for vr in report_dict.get("variants", []):
            variant = vr.get("variant", {})
            variant_id = variant.get("id", str(uuid4()))

            # Insert variant
            insert_variants(job_id, [variant])

            # Insert evidence for this variant
            evidence = vr.get("evidence", [])
            if evidence:
                insert_evidence(variant_id, evidence)

            # Insert claims for this variant
            claims = vr.get("claims", [])
            if claims:
                insert_claims(variant_id, claims)

        # 3. Insert the report
        report_row = insert_report(job_id, report_dict)

        # 4. Insert variant summaries
        if report_row:
            report_id = report_row.get("id", str(uuid4()))
            insert_variant_summaries(
                report_id, report_dict.get("variants", [])
            )

        logger.info(
            "Full analysis persisted to Supabase for job %s", job_id
        )
        return True

    except Exception as exc:
        logger.warning(
            "Failed to persist full analysis to Supabase: %s", exc
        )
        return False
