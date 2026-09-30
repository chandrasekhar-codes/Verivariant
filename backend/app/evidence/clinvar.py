"""ClinVar Evidence Retrieval Client.

Interacts with NCBI E-Utilities to query ClinVar variations, clinical assertions,
review statuses, and associated conditions. Falls back gracefully to curated records
when NCBI is unresponsive, rate limited, or offline.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import httpx

from app.evidence.curated_cache import get_curated_record
from app.models import EvidenceItem, EvidenceSource, EvidenceStatus, Variant

NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


async def fetch_clinvar_evidence(
    variant: Variant,
    offline_mode: bool = False,
    timeout_sec: float = 6.0,
) -> EvidenceItem:
    """Retrieve ClinVar evidence for a given genomic variant."""
    item_id = f"clinvar_{uuid.uuid4().hex[:8]}"
    now = datetime.now(UTC)

    # Check curated cache first if in offline mode
    cached = get_curated_record(variant.key, variant.rsid)
    if offline_mode and cached and "clinvar" in cached:
        cdata = cached["clinvar"]
        return EvidenceItem(
            id=item_id,
            variant_key=variant.key,
            source=EvidenceSource.clinvar,
            status=EvidenceStatus.found,
            url=cdata.get("url"),
            retrieved_at=now,
            data=cdata,
            is_demo_data=True,
        )

    # Attempt live query if not strictly offline
    if not offline_mode:
        try:
            async with httpx.AsyncClient(timeout=timeout_sec, follow_redirects=True) as client:
                # 1. Search term: prefer rsid, fallback to genomic coordinates
                query_term = (
                    variant.rsid
                    if variant.rsid
                    else f"{variant.chrom}[chr] AND {variant.pos}[chrpos38]"
                )
                search_resp = await client.get(
                    NCBI_ESEARCH_URL,
                    params={
                        "db": "clinvar",
                        "term": query_term,
                        "retmode": "json",
                        "retmax": 3,
                    },
                )

                if search_resp.status_code == 200:
                    search_data = search_resp.json()
                    id_list = search_data.get("esearchresult", {}).get("idlist", [])

                    if id_list:
                        clinvar_uid = id_list[0]
                        # 2. Fetch summary
                        summary_resp = await client.get(
                            NCBI_ESUMMARY_URL,
                            params={
                                "db": "clinvar",
                                "id": clinvar_uid,
                                "retmode": "json",
                            },
                        )

                        if summary_resp.status_code == 200:
                            sum_data = summary_resp.json().get("result", {}).get(clinvar_uid, {})
                            germline_classification = sum_data.get(
                                "germline_classification", {}
                            ).get("description", "Not available")
                            conditions = [
                                trait.get("trait_name", "")
                                for trait in sum_data.get("trait_set", [])
                                if trait.get("trait_name")
                            ]
                            review_status = sum_data.get("germline_classification", {}).get(
                                "review_status", "Not available"
                            )
                            variation_id = sum_data.get("variation_set", [{}])[0].get(
                                "variation_id", clinvar_uid
                            )
                            source_url = (
                                f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{variation_id}/"
                            )

                            return EvidenceItem(
                                id=item_id,
                                variant_key=variant.key,
                                source=EvidenceSource.clinvar,
                                status=EvidenceStatus.found,
                                url=source_url,
                                retrieved_at=now,
                                data={
                                    "variation_id": str(variation_id),
                                    "clinical_significance": germline_classification,
                                    "review_status": review_status,
                                    "condition": (
                                        ", ".join(conditions) if conditions else "Not specified"
                                    ),
                                    "evidence_summary": f"ClinVar records list classification as '{germline_classification}' with review status '{review_status}'.",
                                    "url": source_url,
                                },
                                is_demo_data=False,
                            )
        except Exception as exc:
            # Fall back to curated cache if available
            if cached and "clinvar" in cached:
                cdata = cached["clinvar"]
                return EvidenceItem(
                    id=item_id,
                    variant_key=variant.key,
                    source=EvidenceSource.clinvar,
                    status=EvidenceStatus.found,
                    url=cdata.get("url"),
                    retrieved_at=now,
                    data=cdata,
                    is_demo_data=True,
                    error_message=f"Live API note ({type(exc).__name__}): Served from verified curated records.",
                )

    # Fallback to curated cache if no live hit
    if cached and "clinvar" in cached:
        cdata = cached["clinvar"]
        return EvidenceItem(
            id=item_id,
            variant_key=variant.key,
            source=EvidenceSource.clinvar,
            status=EvidenceStatus.found,
            url=cdata.get("url"),
            retrieved_at=now,
            data=cdata,
            is_demo_data=True,
        )

    # Truly not found
    return EvidenceItem(
        id=item_id,
        variant_key=variant.key,
        source=EvidenceSource.clinvar,
        status=EvidenceStatus.not_found,
        url="https://www.ncbi.nlm.nih.gov/clinvar/",
        retrieved_at=now,
        data={
            "clinical_significance": "Not available",
            "review_status": "Not available",
            "condition": "Not available",
            "evidence_summary": "No matching ClinVar variation entry found for this genomic coordinate.",
        },
        is_demo_data=False,
    )
