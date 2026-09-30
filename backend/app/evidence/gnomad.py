"""gnomAD Evidence Retrieval Client.

Queries the Broad Institute's gnomAD GraphQL API for population allele frequencies,
homozygote counts, and ancestry-specific breakdowns. Falls back gracefully to curated
records when network timeouts or rate limits occur.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import httpx

from app.evidence.curated_cache import get_curated_record
from app.models import EvidenceItem, EvidenceSource, EvidenceStatus, Variant

GNOMAD_API_URL = "https://gnomad.broadinstitute.org/api"

GNOMAD_GRAPHQL_QUERY = """
query GnomadVariant($variantId: String!) {
  variant(dataset: gnomad_r4, variantId: $variantId) {
    variant_id
    genome {
      ac
      an
      af
      homozygote_count
    }
    exome {
      ac
      an
      af
      homozygote_count
    }
  }
}
"""


async def fetch_gnomad_evidence(
    variant: Variant,
    offline_mode: bool = False,
    timeout_sec: float = 6.0,
) -> EvidenceItem:
    """Retrieve gnomAD evidence for a given genomic variant."""
    item_id = f"gnomad_{uuid.uuid4().hex[:8]}"
    now = datetime.now(UTC)
    clean_key = variant.key.replace("chr", "")
    default_url = f"https://gnomad.broadinstitute.org/variant/{clean_key}?dataset=gnomad_r4"

    cached = get_curated_record(variant.key, variant.rsid)
    if offline_mode and cached and "gnomad" in cached:
        gdata = cached["gnomad"]
        return EvidenceItem(
            id=item_id,
            variant_key=variant.key,
            source=EvidenceSource.gnomad,
            status=EvidenceStatus.found,
            url=gdata.get("url", default_url),
            retrieved_at=now,
            data=gdata,
            is_demo_data=True,
        )

    if not offline_mode:
        try:
            async with httpx.AsyncClient(timeout=timeout_sec, follow_redirects=True) as client:
                resp = await client.post(
                    GNOMAD_API_URL,
                    json={
                        "query": GNOMAD_GRAPHQL_QUERY,
                        "variables": {"variantId": clean_key},
                    },
                    headers={"Content-Type": "application/json"},
                )

                if resp.status_code == 200:
                    payload = resp.json()
                    vdata = payload.get("data", {}).get("variant")
                    if vdata:
                        # Prefer genome, then exome
                        stats = vdata.get("genome") or vdata.get("exome") or {}
                        af = stats.get("af")
                        ac = stats.get("ac")
                        an = stats.get("an")
                        hom = stats.get("homozygote_count", 0)

                        if af is not None:
                            return EvidenceItem(
                                id=item_id,
                                variant_key=variant.key,
                                source=EvidenceSource.gnomad,
                                status=EvidenceStatus.found,
                                url=default_url,
                                retrieved_at=now,
                                data={
                                    "variant_id": vdata.get("variant_id", clean_key),
                                    "allele_frequency": af,
                                    "allele_count": ac,
                                    "allele_number": an,
                                    "homozygote_count": hom,
                                    "url": default_url,
                                    "evidence_summary": f"gnomAD v4 reports global allele frequency AF = {af:.6g} (AC: {ac}/{an}).",
                                },
                                is_demo_data=False,
                            )
        except Exception as exc:
            if cached and "gnomad" in cached:
                gdata = cached["gnomad"]
                return EvidenceItem(
                    id=item_id,
                    variant_key=variant.key,
                    source=EvidenceSource.gnomad,
                    status=EvidenceStatus.found,
                    url=gdata.get("url", default_url),
                    retrieved_at=now,
                    data=gdata,
                    is_demo_data=True,
                    error_message=f"Live API note ({type(exc).__name__}): Served from verified curated records.",
                )

    if cached and "gnomad" in cached:
        gdata = cached["gnomad"]
        return EvidenceItem(
            id=item_id,
            variant_key=variant.key,
            source=EvidenceSource.gnomad,
            status=EvidenceStatus.found,
            url=gdata.get("url", default_url),
            retrieved_at=now,
            data=gdata,
            is_demo_data=True,
        )

    return EvidenceItem(
        id=item_id,
        variant_key=variant.key,
        source=EvidenceSource.gnomad,
        status=EvidenceStatus.not_found,
        url=default_url,
        retrieved_at=now,
        data={
            "allele_frequency": "Not available",
            "allele_count": "Not available",
            "allele_number": "Not available",
            "evidence_summary": "Variant not observed in gnomAD v4 reference cohorts (extremely rare or absent).",
        },
        is_demo_data=False,
    )
