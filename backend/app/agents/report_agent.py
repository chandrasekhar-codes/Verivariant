"""Agent 3 — Report Agent.

Compiles verified findings, multi-source evidence, conflict analyses, and limitations
into a traceable, structured genomic variant report with medical safety disclaimers.
Identifies scientific discordance across ClinVar, gnomAD, and VEP.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.models import (
    DISCLAIMER,
    ConflictItem,
    EvidenceSource,
    GenomeBuild,
    PipelineLogEntry,
    Report,
    VariantReport,
    VerificationStatus,
)


def detect_evidence_conflicts(variant_report: VariantReport) -> list[ConflictItem]:
    """Identify scientific discordance or conflicting evidence across ClinVar, gnomAD, and VEP."""
    conflicts: list[ConflictItem] = []
    variant = variant_report.variant
    evidence_by_source = {e.source: e for e in variant_report.evidence}

    clinvar_item = evidence_by_source.get(EvidenceSource.clinvar)
    gnomad_item = evidence_by_source.get(EvidenceSource.gnomad)
    vep_item = evidence_by_source.get(EvidenceSource.ensembl_vep)

    clinvar_sig = clinvar_item.data.get("clinical_significance", "") if clinvar_item else ""
    gnomad_af = gnomad_item.data.get("allele_frequency") if gnomad_item else None
    vep_csq = vep_item.data.get("consequence", "") if vep_item else ""

    # Conflict Pattern 1: ClinVar reports conflicting interpretations
    if "conflicting" in clinvar_sig.lower():
        conflicts.append(
            ConflictItem(
                variant_key=variant.key,
                gene=variant.gene or "Unknown",
                conflict_type="ClinVar Submitter Discordance",
                description=(
                    f"ClinVar records list conflicting classifications ('{clinvar_sig}') "
                    f"among independent clinical laboratories and academic submitters."
                ),
                clinvar_assertion=clinvar_sig,
                gnomad_frequency=(
                    f"{gnomad_af:.4f}" if isinstance(gnomad_af, (int, float)) else "N/A"
                ),
                vep_consequence=vep_csq or "N/A",
                recommendation="Recommend comprehensive clinical review against ACMG/AMP variant interpretation guidelines.",
            )
        )

    # Conflict Pattern 2: High population frequency for a reported Pathogenic variant
    if (
        isinstance(gnomad_af, (int, float))
        and gnomad_af > 0.05
        and "pathogenic" in clinvar_sig.lower()
    ):
        conflicts.append(
            ConflictItem(
                variant_key=variant.key,
                gene=variant.gene or "Unknown",
                conflict_type="Frequency-Pathogenicity Discordance",
                description=(
                    f"Variant carries a 'Pathogenic' label in ClinVar, yet exhibits high common population "
                    f"allele frequency in gnomAD (AF = {gnomad_af:.4f} > 5%), strongly suggesting reduced penetrance "
                    f"or a benign polymorphism under modern ACMG BA1/BS1 criteria."
                ),
                clinvar_assertion=clinvar_sig,
                gnomad_frequency=f"{gnomad_af:.4f}",
                vep_consequence=vep_csq or "N/A",
                recommendation="Caution: High population prevalence frequently invalidates classical monogenic pathogenicity. Review current literature.",
            )
        )

    return conflicts


def generate_report(
    job_id: str,
    genome_build: GenomeBuild,
    variant_reports: list[VariantReport],
    pipeline_log: list[PipelineLogEntry] | None = None,
    is_demo: bool = False,
) -> Report:
    """Execute the Report Agent to generate a fully traceable genomic analysis report."""
    now = datetime.now(UTC)
    all_conflicts: list[ConflictItem] = []
    total_claims = 0
    supported_claims = 0
    unsupported_claims = 0
    unclear_claims = 0
    rejected_claims = []

    # Detect conflicts for each variant and aggregate claim metrics
    for vr in variant_reports:
        vr_conflicts = detect_evidence_conflicts(vr)
        vr.conflicts = vr_conflicts
        all_conflicts.extend(vr_conflicts)

        for c in vr.claims:
            total_claims += 1
            if c.verification:
                v = c.verification.verdict
                if v == VerificationStatus.supported or v == VerificationStatus.partially_supported:
                    supported_claims += 1
                elif v == VerificationStatus.unsupported:
                    unsupported_claims += 1
                    rejected_claims.append(c)
                elif v == VerificationStatus.unclear:
                    unclear_claims += 1

    # Standard limitations
    limitations = [
        "In silico predictions from Ensembl VEP (SIFT, PolyPhen) are computational heuristics and do not replace biological functional assays.",
        "Population allele frequencies in gnomAD v4 reflect specific cohorts and may not capture rare regional or underrepresented ancestral sub-populations.",
        "ClinVar classifications are submitter-provided and undergo varying degrees of curation review status (0 to 4 stars).",
        "Analysis scope is limited to small genomic variants (SNVs, small indels) and does not assess structural variants or copy number alterations (CNVs).",
    ]

    # Executive summary synthesis
    pathogenic_count = sum(
        1
        for vr in variant_reports
        if vr.variant.clinvar_sig and "pathogenic" in vr.variant.clinvar_sig.lower()
    )
    conflict_count = len(all_conflicts)

    summary = (
        f"GENESIS multi-agent analysis completed for {len(variant_reports)} variant(s) across genome build {genome_build.value}. "
        f"Retrieved independent evidence from NCBI ClinVar, Broad Institute gnomAD v4, and Ensembl VEP. "
        f"Identified {pathogenic_count} clinically significant pathogenic/likely pathogenic variant(s) "
        f"and {conflict_count} evidence conflict(s) requiring multidisciplinary attention. "
        f"Across all findings, {supported_claims} of {total_claims} claims were rigorously verified against raw database payloads."
    )

    return Report(
        job_id=job_id,
        created_at=now,
        genome_build=genome_build,
        variants=variant_reports,
        rejected_claims=rejected_claims,
        conflicts=all_conflicts,
        sources_used=[
            "NCBI ClinVar (E-Utilities API)",
            "Broad Institute gnomAD (v4 GraphQL API)",
            "Ensembl Variant Effect Predictor (REST API)",
        ],
        total_variants=len(variant_reports),
        total_claims=total_claims,
        supported_claims=supported_claims,
        unsupported_claims=unsupported_claims,
        unclear_claims=unclear_claims,
        summary=summary,
        limitations=limitations,
        disclaimer=DISCLAIMER,
        is_demo=is_demo,
        pipeline_log=pipeline_log or [],
    )
