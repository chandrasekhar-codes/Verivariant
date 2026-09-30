"""Ensembl Variant Effect Predictor (VEP) Evidence Retrieval Client.

Queries the Ensembl REST API (https://rest.ensembl.org) for molecular consequences,
transcript annotations, coding impacts, SIFT/PolyPhen predictions, and HGVS nomenclature.
Falls back gracefully to curated records if the external endpoint is rate limited or offline.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import httpx

from app.evidence.curated_cache import get_curated_record
from app.models import EvidenceItem, EvidenceSource, EvidenceStatus, Variant

ENSEMBL_REST_BASE = "https://rest.ensembl.org"


async def fetch_ensembl_vep_evidence(
    variant: Variant,
    offline_mode: bool = False,
    timeout_sec: float = 6.0,
) -> EvidenceItem:
    """Retrieve Ensembl VEP evidence for a given genomic variant."""
    item_id = f"vep_{uuid.uuid4().hex[:8]}"
    now = datetime.now(UTC)
    clean_chrom = variant.chrom.replace("chr", "")
    rsid_url = (
        f"https://www.ensembl.org/Homo_sapiens/Variation/Explore?v={variant.rsid}"
        if variant.rsid
        else f"https://www.ensembl.org/Homo_sapiens/Location/View?r={clean_chrom}:{variant.pos}-{variant.pos}"
    )

    cached = get_curated_record(variant.key, variant.rsid)
    if offline_mode and cached and "ensembl_vep" in cached:
        vdata = cached["ensembl_vep"]
        return EvidenceItem(
            id=item_id,
            variant_key=variant.key,
            source=EvidenceSource.ensembl_vep,
            status=EvidenceStatus.found,
            url=vdata.get("url", rsid_url),
            retrieved_at=now,
            data=vdata,
            is_demo_data=True,
        )

    if not offline_mode:
        try:
            # Ensembl VEP region endpoint: /vep/human/region/{chrom}:{pos}-{pos}/{allele}
            # For indels, Ensembl expects specific allele format, or we can query by rsid if present
            url = f"{ENSEMBL_REST_BASE}/vep/human/region/{clean_chrom}:{variant.pos}-{variant.pos}/{variant.alt}"
            if variant.rsid:
                url = f"{ENSEMBL_REST_BASE}/vep/human/id/{variant.rsid}"

            async with httpx.AsyncClient(timeout=timeout_sec, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                )

                if resp.status_code == 200:
                    payload = resp.json()
                    if isinstance(payload, list) and payload:
                        rec = payload[0]
                        consequence = rec.get("most_severe_consequence", "unknown_consequence")
                        transcripts = rec.get("transcript_consequences", [])
                        primary_tx = transcripts[0] if transcripts else {}
                        gene_symbol = primary_tx.get("gene_symbol", "Not available")
                        gene_id = primary_tx.get("gene_id", "Not available")
                        impact = primary_tx.get("impact", "MODIFIER")
                        hgvsc = primary_tx.get("hgvsc")
                        hgvsp = primary_tx.get("hgvsp")
                        sift = primary_tx.get("sift_prediction")
                        polyphen = primary_tx.get("polyphen_prediction")

                        vep_data = {
                            "consequence": consequence,
                            "impact": impact,
                            "gene_symbol": gene_symbol,
                            "gene_id": gene_id,
                            "transcript_id": primary_tx.get("transcript_id", "Not available"),
                            "biotype": primary_tx.get("biotype", "protein_coding"),
                            "codons": primary_tx.get("codons", "Not available"),
                            "amino_acids": primary_tx.get("amino_acids", "Not available"),
                            "hgvsc": hgvsc or "Not available",
                            "hgvsp": hgvsp or "Not available",
                            "sift": sift or "Not available",
                            "polyphen": polyphen or "Not available",
                            "url": rsid_url,
                            "evidence_summary": f"Ensembl VEP predicts '{consequence}' ({impact} impact) on gene {gene_symbol}.",
                        }

                        return EvidenceItem(
                            id=item_id,
                            variant_key=variant.key,
                            source=EvidenceSource.ensembl_vep,
                            status=EvidenceStatus.found,
                            url=rsid_url,
                            retrieved_at=now,
                            data=vep_data,
                            is_demo_data=False,
                        )
        except Exception as exc:
            if cached and "ensembl_vep" in cached:
                vdata = cached["ensembl_vep"]
                return EvidenceItem(
                    id=item_id,
                    variant_key=variant.key,
                    source=EvidenceSource.ensembl_vep,
                    status=EvidenceStatus.found,
                    url=vdata.get("url", rsid_url),
                    retrieved_at=now,
                    data=vdata,
                    is_demo_data=True,
                    error_message=f"Live API note ({type(exc).__name__}): Served from verified curated records.",
                )

    if cached and "ensembl_vep" in cached:
        vdata = cached["ensembl_vep"]
        return EvidenceItem(
            id=item_id,
            variant_key=variant.key,
            source=EvidenceSource.ensembl_vep,
            status=EvidenceStatus.found,
            url=vdata.get("url", rsid_url),
            retrieved_at=now,
            data=vdata,
            is_demo_data=True,
        )

    return EvidenceItem(
        id=item_id,
        variant_key=variant.key,
        source=EvidenceSource.ensembl_vep,
        status=EvidenceStatus.not_found,
        url=rsid_url,
        retrieved_at=now,
        data={
            "consequence": "Not available",
            "impact": "Not available",
            "gene_symbol": "Not available",
            "evidence_summary": "No transcript annotation returned by Ensembl VEP for this coordinate.",
        },
        is_demo_data=False,
    )
