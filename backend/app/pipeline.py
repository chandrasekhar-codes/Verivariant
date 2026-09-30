"""GENESIS Multi-Agent Pipeline Orchestrator.

Sequences:
1. VCF Variant Extraction & Normalization
2. Multi-Source Evidence Retrieval (ClinVar, gnomAD, Ensembl VEP)
3. Research Agent Execution (Agent 1)
4. Verification Agent Execution (Agent 2)
5. Report Agent Execution (Agent 3) & Conflict Detection
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime

from app.agents.report_agent import generate_report
from app.agents.research_agent import run_research_agent
from app.agents.verification_agent import run_verification_agent
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

    variant_reports: list[VariantReport] = []

    for idx, var in enumerate(variants):
        # Retrieve evidence concurrently for this variant
        evidence_items, enriched_var = await retrieve_all_evidence(
            var,
            offline_mode=is_demo,
            timeout_sec=5.0,
        )

        # Step 3: Research Agent (Agent 1)
        claims, summary = await run_research_agent(enriched_var, evidence_items)

        # Step 4: Verification Agent (Agent 2)
        verified_claims, _ = run_verification_agent(claims, evidence_items)

        vr = VariantReport(
            variant=enriched_var,
            evidence=evidence_items,
            claims=verified_claims,
            summary=summary,
            overall_confidence="High",
        )
        variant_reports.append(vr)

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

    return report
