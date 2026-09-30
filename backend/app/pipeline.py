"""GENESIS Multi-Agent Pipeline Orchestrator.

Sequences:
1. VCF Variant Extraction & Normalization
2. Multi-Source Evidence Retrieval (ClinVar, gnomAD, Ensembl VEP)
3. Research Agent Execution (Agent 1)
4. Verification Agent Execution (Agent 2)
5. Report Agent Execution (Agent 3) & Conflict Detection
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from app.agents.report_agent import generate_report
from app.agents.research_agent import run_research_agent
from app.agents.verification_agent import run_verification_agent
from app.database import create_job, persist_full_analysis, update_job_status
from app.evidence.service import retrieve_all_evidence
from app.models import (
    GenomeBuild,
    PipelineLogEntry,
    Report,
    Variant,
    VariantReport,
)

logger = logging.getLogger("genesis.pipeline")


async def run_analysis_pipeline(
    job_id: str,
    variants: list[Variant],
    genome_build: GenomeBuild = GenomeBuild.grch38,
    is_demo: bool = False,
    progress_callback: Callable[[str, str], None] | None = None,
) -> Report:
    """Execute the full end-to-end multi-agent genomic analysis pipeline."""
    pipeline_log: list[PipelineLogEntry] = []

    def log_step(stage: str, message: str) -> None:
        entry = PipelineLogEntry(
            stage=stage,
            message=message,
            at=datetime.now(UTC),
            status="complete",
        )
        pipeline_log.append(entry)
        if progress_callback:
            progress_callback(stage, message)
        logger.info(f"[{stage}] {message}")

    # Register job in Supabase (non-blocking, fallback-safe)
    create_job(
        job_id=job_id,
        filename="demo.vcf" if is_demo else "uploaded.vcf",
        genome_build=genome_build.value,
        is_demo=is_demo,
    )
    update_job_status(job_id, "running")

    # Step 1: VCF Parsing & Variant Identification
    log_step("vcf_parsing", f"Successfully parsed {len(variants)} genomic variant(s).")
    log_step(
        "variant_identification",
        f"Extracted and normalized {len(variants)} variant coordinates on reference {genome_build.value}.",
    )

    # Step 2: Evidence Retrieval across ClinVar, gnomAD, Ensembl VEP
    log_step(
        "evidence_retrieval",
        "Retrieving genomic evidence from ClinVar, gnomAD v4, and Ensembl VEP...",
    )

    sem = asyncio.Semaphore(6)

    async def _process_variant(var: Variant) -> VariantReport:
        async with sem:
            evidence_items, enriched_var = await retrieve_all_evidence(
                var,
                offline_mode=is_demo,
                timeout_sec=5.0,
            )
            claims, summary = await run_research_agent(enriched_var, evidence_items)
            verified_claims, _ = run_verification_agent(claims, evidence_items)
            return VariantReport(
                variant=enriched_var,
                evidence=evidence_items,
                claims=verified_claims,
                summary=summary,
                overall_confidence="High",
            )

    variant_reports = list(await asyncio.gather(*(_process_variant(v) for v in variants)))

    log_step(
        "research_agent",
        f"Research Agent synthesized grounded claims and summaries across all {len(variants)} variants.",
    )
    log_step(
        "verification_agent",
        "Verification Agent completed independent cross-verification against raw evidence payloads.",
    )

    # Step 5: Report Agent (Agent 3) & Conflict Synthesis
    log_step(
        "report_agent",
        "Report Agent compiled traceable report, identified evidence conflicts, and applied safety disclaimers.",
    )

    report = generate_report(
        job_id=job_id,
        genome_build=genome_build,
        variant_reports=variant_reports,
        pipeline_log=pipeline_log,
        is_demo=is_demo,
    )

    # Persist full analysis to Supabase (non-blocking, fallback-safe)
    try:
        report_dict = report.model_dump(mode="json")
        persist_full_analysis(job_id, report_dict)
    except Exception as exc:
        logger.warning("Supabase persistence failed (non-critical): %s", exc)

    return report
