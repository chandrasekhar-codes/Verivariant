"""Unified Evidence Retrieval Service.

Coordinates concurrent retrieval across ClinVar, gnomAD, and Ensembl VEP
with error isolation, variant enrichment, and caching.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

from app.evidence.clinvar import fetch_clinvar_evidence
from app.evidence.ensembl_vep import fetch_ensembl_vep_evidence
from app.evidence.gnomad import fetch_gnomad_evidence
from app.models import EvidenceItem, EvidenceSource, EvidenceStatus, Variant


async def retrieve_all_evidence(
    variant: Variant,
    offline_mode: bool = False,
    timeout_sec: float = 6.0,
) -> tuple[list[EvidenceItem], Variant]:
    """Retrieve evidence from ClinVar, gnomAD, and Ensembl VEP concurrently.

    Also enriches the variant object with gene symbol, consequence, ClinVar significance,
    and gnomAD allele frequency.
    """
    now = datetime.now(UTC)

    # Launch all 3 evidence retrievers in parallel
    results = await asyncio.gather(
        fetch_clinvar_evidence(variant, offline_mode=offline_mode, timeout_sec=timeout_sec),
        fetch_gnomad_evidence(variant, offline_mode=offline_mode, timeout_sec=timeout_sec),
        fetch_ensembl_vep_evidence(variant, offline_mode=offline_mode, timeout_sec=timeout_sec),
        return_exceptions=True,
    )

    evidence_items: list[EvidenceItem] = []

    # 1. ClinVar item
    if isinstance(results[0], EvidenceItem):
        clinvar_item = results[0]
    else:
        clinvar_item = EvidenceItem(
            id=f"clinvar_{uuid.uuid4().hex[:8]}",
            variant_key=variant.key,
            source=EvidenceSource.clinvar,
            status=EvidenceStatus.error,
            url="https://www.ncbi.nlm.nih.gov/clinvar/",
            retrieved_at=now,
            data={"evidence_summary": f"ClinVar request failed: {results[0]!s}"},
            error_message=str(results[0]),
        )
    evidence_items.append(clinvar_item)

    # 2. gnomAD item
    if isinstance(results[1], EvidenceItem):
        gnomad_item = results[1]
    else:
        gnomad_item = EvidenceItem(
            id=f"gnomad_{uuid.uuid4().hex[:8]}",
            variant_key=variant.key,
            source=EvidenceSource.gnomad,
            status=EvidenceStatus.error,
            url=f"https://gnomad.broadinstitute.org/variant/{variant.key}?dataset=gnomad_r4",
            retrieved_at=now,
            data={"evidence_summary": f"gnomAD request failed: {results[1]!s}"},
            error_message=str(results[1]),
        )
    evidence_items.append(gnomad_item)

    # 3. Ensembl VEP item
    if isinstance(results[2], EvidenceItem):
        vep_item = results[2]
    else:
        vep_item = EvidenceItem(
            id=f"vep_{uuid.uuid4().hex[:8]}",
            variant_key=variant.key,
            source=EvidenceSource.ensembl_vep,
            status=EvidenceStatus.error,
            url="https://www.ensembl.org/Homo_sapiens/Variation/Explore",
            retrieved_at=now,
            data={"evidence_summary": f"Ensembl VEP request failed: {results[2]!s}"},
            error_message=str(results[2]),
        )
    evidence_items.append(vep_item)

    # Enrich variant fields from retrieved evidence if not already set from INFO
    enriched_variant = variant.model_copy()

    # Gene symbol
    if not enriched_variant.gene or enriched_variant.gene == ".":
        gene = vep_item.data.get("gene_symbol")
        if gene and gene != "Not available":
            enriched_variant.gene = gene
        elif "GENE" in variant.info:
            enriched_variant.gene = str(variant.info["GENE"])

    # Consequence
    if not enriched_variant.consequence or enriched_variant.consequence == ".":
        consequence = vep_item.data.get("consequence")
        if consequence and consequence != "Not available":
            enriched_variant.consequence = consequence
        elif "CONSEQUENCE" in variant.info:
            enriched_variant.consequence = str(variant.info["CONSEQUENCE"])

    # ClinVar significance
    if not enriched_variant.clinvar_sig:
        clnsig = clinvar_item.data.get("clinical_significance")
        if clnsig and clnsig != "Not available":
            enriched_variant.clinvar_sig = clnsig
        elif "CLNSIG" in variant.info:
            enriched_variant.clinvar_sig = str(variant.info["CLNSIG"])

    # gnomAD allele frequency
    if enriched_variant.gnomad_af is None:
        af = gnomad_item.data.get("allele_frequency")
        if isinstance(af, (int, float)):
            enriched_variant.gnomad_af = float(af)
        elif "AF" in variant.info:
            try:
                enriched_variant.gnomad_af = float(variant.info["AF"])
            except (ValueError, TypeError):
                pass

    # HGVS
    if not enriched_variant.hgvsc:
        hgvsc = vep_item.data.get("hgvsc")
        if hgvsc and hgvsc != "Not available":
            enriched_variant.hgvsc = hgvsc
        elif "HGVSC" in variant.info:
            enriched_variant.hgvsc = str(variant.info["HGVSC"])

    if not enriched_variant.hgvsp:
        hgvsp = vep_item.data.get("hgvsp")
        if hgvsp and hgvsp != "Not available":
            enriched_variant.hgvsp = hgvsp
        elif "HGVSP" in variant.info:
            enriched_variant.hgvsp = str(variant.info["HGVSP"])

    return evidence_items, enriched_variant
