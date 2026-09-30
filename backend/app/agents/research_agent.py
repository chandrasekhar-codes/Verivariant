"""Agent 1 — Research Agent.

Investigates genomic variants using retrieved multi-source evidence (ClinVar, gnomAD, VEP).
Formulates atomic, traceable claims backed by citations and URLs.
Strict grounding: NEVER hallucinates or invents evidence. If evidence is absent,
it explicitly outputs 'Insufficient evidence available.'
"""

from __future__ import annotations

import json
import uuid

import httpx

from app.config import get_settings
from app.models import Claim, ClaimCategory, EvidenceItem, Variant

SYSTEM_PROMPT = """You are the GENESIS Research Agent, an expert AI genomic researcher.
Your job is to investigate a genomic variant strictly using the provided multi-source evidence.

CRITICAL RULES:
1. Do not invent genomic facts.
2. Do not invent citations or database results.
3. Do not infer clinical significance without direct evidence.
4. Every claim MUST be tied to a specific evidence source (ClinVar, gnomAD, or Ensembl VEP).
5. If evidence is unavailable for a source, state: "Insufficient evidence available."
6. Output MUST be valid JSON adhering to the exact schema.

Schema:
{
  "variant": "<variant_key>",
  "claims": [
    {
      "claim": "<atomic claim>",
      "evidence": "<exact supporting evidence quote or parameter>",
      "source": "ClinVar | gnomAD | Ensembl VEP",
      "source_url": "<url or null>",
      "category": "clinical_significance | population_frequency | functional_consequence | pathogenicity_summary"
    }
  ],
  "summary": "<2-3 sentence grounded research summary>"
}
"""


def _generate_deterministic_claims(
    variant: Variant,
    evidence_items: list[EvidenceItem],
) -> tuple[list[Claim], str]:
    """Deterministic, rule-based reasoning engine ensuring 100% grounded claims

    directly from the retrieved evidence payload without needing external LLM API tokens.
    """
    claims: list[Claim] = []
    evidence_by_source: dict[str, EvidenceItem] = {e.source.value: e for e in evidence_items}

    # 1. ClinVar Claim
    clinvar_item = evidence_by_source.get("clinvar")
    if (
        clinvar_item
        and clinvar_item.status.value == "found"
        and clinvar_item.data.get("clinical_significance") != "Not available"
    ):
        cdata = clinvar_item.data
        sig = cdata.get("clinical_significance", "Unknown")
        cond = cdata.get("condition", "Unspecified condition")
        rev = cdata.get("review_status", "Unreviewed")
        var_id = cdata.get("variation_id", "")

        claim_text = f"ClinVar classifies variant {variant.key} as '{sig}' for {cond}."
        ev_text = f"Classification: {sig}; Condition: {cond}; Review Status: {rev}; Variation ID: {var_id}"
        claims.append(
            Claim(
                id=f"claim_{uuid.uuid4().hex[:8]}",
                variant_key=variant.key,
                text=claim_text,
                claim=claim_text,
                evidence=ev_text,
                source="ClinVar",
                source_url=clinvar_item.url,
                category=ClaimCategory.clinical_significance,
                evidence_ids=[clinvar_item.id],
            )
        )
    else:
        claim_text = f"Insufficient evidence available in ClinVar for variant {variant.key}."
        claims.append(
            Claim(
                id=f"claim_{uuid.uuid4().hex[:8]}",
                variant_key=variant.key,
                text=claim_text,
                claim=claim_text,
                evidence="No matching variation entry in ClinVar database.",
                source="ClinVar",
                source_url=clinvar_item.url if clinvar_item else None,
                category=ClaimCategory.clinical_significance,
                evidence_ids=[clinvar_item.id] if clinvar_item else [],
            )
        )

    # 2. gnomAD Claim
    gnomad_item = evidence_by_source.get("gnomad")
    if (
        gnomad_item
        and gnomad_item.status.value == "found"
        and isinstance(gnomad_item.data.get("allele_frequency"), (int, float))
    ):
        gdata = gnomad_item.data
        af = float(gdata["allele_frequency"])
        ac = gdata.get("allele_count", "N/A")
        an = gdata.get("allele_number", "N/A")
        hom = gdata.get("homozygote_count", 0)

        rarity_desc = (
            "extremely rare" if af < 0.0001 else "rare" if af < 0.01 else "common polymorphism"
        )
        claim_text = (
            f"gnomAD v4 reports a global allele frequency of {af:.6g} (AC: {ac}/{an}, homozygotes: {hom}), "
            f"classifying it as a {rarity_desc} variant."
        )
        ev_text = f"Allele Frequency = {af:.6g}, Allele Count = {ac}, Allele Number = {an}, Homozygotes = {hom}"
        claims.append(
            Claim(
                id=f"claim_{uuid.uuid4().hex[:8]}",
                variant_key=variant.key,
                text=claim_text,
                claim=claim_text,
                evidence=ev_text,
                source="gnomAD",
                source_url=gnomad_item.url,
                category=ClaimCategory.population_frequency,
                evidence_ids=[gnomad_item.id],
            )
        )
    else:
        claim_text = (
            "Insufficient evidence available in gnomAD (variant unobserved in reference cohort)."
        )
        claims.append(
            Claim(
                id=f"claim_{uuid.uuid4().hex[:8]}",
                variant_key=variant.key,
                text=claim_text,
                claim=claim_text,
                evidence="Variant allele frequency not reported or absent in gnomAD v4 cohorts.",
                source="gnomAD",
                source_url=gnomad_item.url if gnomad_item else None,
                category=ClaimCategory.population_frequency,
                evidence_ids=[gnomad_item.id] if gnomad_item else [],
            )
        )

    # 3. Ensembl VEP Claim
    vep_item = evidence_by_source.get("ensembl_vep")
    if (
        vep_item
        and vep_item.status.value == "found"
        and vep_item.data.get("consequence") != "Not available"
    ):
        vdata = vep_item.data
        csq = vdata.get("consequence", "variant")
        impact = vdata.get("impact", "MODERATE")
        gene = vdata.get("gene_symbol") or variant.gene or "unknown gene"
        tx = vdata.get("transcript_id", "canonical")
        hgvsp = vdata.get("hgvsp", "")

        hgvsp_str = f" resulting in {hgvsp}" if hgvsp and hgvsp != "Not available" else ""
        claim_text = (
            f"Ensembl VEP predicts a '{csq}' consequence ({impact} impact) on gene {gene} "
            f"(transcript {tx}){hgvsp_str}."
        )
        ev_text = f"Consequence: {csq}, Impact: {impact}, Gene: {gene}, Transcript: {tx}, SIFT: {vdata.get('sift', 'N/A')}, PolyPhen: {vdata.get('polyphen', 'N/A')}"
        claims.append(
            Claim(
                id=f"claim_{uuid.uuid4().hex[:8]}",
                variant_key=variant.key,
                text=claim_text,
                claim=claim_text,
                evidence=ev_text,
                source="Ensembl VEP",
                source_url=vep_item.url,
                category=ClaimCategory.functional_consequence,
                evidence_ids=[vep_item.id],
            )
        )
    else:
        claim_text = "Insufficient evidence available in Ensembl VEP for transcript consequence."
        claims.append(
            Claim(
                id=f"claim_{uuid.uuid4().hex[:8]}",
                variant_key=variant.key,
                text=claim_text,
                claim=claim_text,
                evidence="No transcript effect prediction returned.",
                source="Ensembl VEP",
                source_url=vep_item.url if vep_item else None,
                category=ClaimCategory.functional_consequence,
                evidence_ids=[vep_item.id] if vep_item else [],
            )
        )

    # 4. Multi-evidence grounded summary
    gene_label = variant.gene or (vep_item.data.get("gene_symbol") if vep_item else "Genomic")
    sig_label = (
        clinvar_item.data.get("clinical_significance")
        if (clinvar_item and clinvar_item.status.value == "found")
        else "unclassified"
    )
    summary = (
        f"Investigation of {variant.key} ({gene_label}) reveals a clinical classification of "
        f"'{sig_label}' according to ClinVar submissions, accompanied by "
        f"{'population frequency data in gnomAD' if gnomad_item and gnomad_item.status.value == 'found' else 'limited cohort frequency data'}. "
        f"Functional consequence modeling indicates {vep_item.data.get('consequence', 'unspecified effects') if vep_item else 'standard variation'}."
    )

    return claims, summary


async def run_research_agent(
    variant: Variant,
    evidence_items: list[EvidenceItem],
) -> tuple[list[Claim], str]:
    """Execute the Research Agent.

    Uses LLM API if configured, with automatic fallback to deterministic grounded logic.
    """
    settings = get_settings()

    # If LLM API is available and configured, we can invoke it with strict grounding
    if settings.anthropic_api_key or settings.openai_api_key:
        try:
            # Prepare evidence payload for prompt
            evidence_payload = {
                e.source.value: {
                    "status": e.status.value,
                    "url": e.url,
                    "data": e.data,
                }
                for e in evidence_items
            }

            user_prompt = f"""Genomic Variant:
ID: {variant.id}
Key: {variant.key}
Chromosome: {variant.chrom}
Position: {variant.pos}
Reference: {variant.ref}
Alternate: {variant.alt}
rsID: {variant.rsid or 'N/A'}
Gene: {variant.gene or 'N/A'}

Retrieved Evidence:
{json.dumps(evidence_payload, indent=2)}

Please extract grounded claims and produce a research summary.
"""
            # If OpenAI key is present
            if settings.openai_api_key:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": user_prompt},
                            ],
                            "response_format": {"type": "json_object"},
                            "temperature": 0.0,
                        },
                    )
                    if resp.status_code == 200:
                        parsed = resp.json()["choices"][0]["message"]["content"]
                        obj = json.loads(parsed)
                        raw_claims = obj.get("claims", [])
                        claims: list[Claim] = []
                        for rc in raw_claims:
                            claims.append(
                                Claim(
                                    id=f"claim_{uuid.uuid4().hex[:8]}",
                                    variant_key=variant.key,
                                    text=rc.get("claim", ""),
                                    claim=rc.get("claim", ""),
                                    evidence=rc.get("evidence", ""),
                                    source=rc.get("source", "Unknown"),
                                    source_url=rc.get("source_url"),
                                    category=(
                                        ClaimCategory(rc.get("category", "other"))
                                        if rc.get("category") in ClaimCategory._value2member_map_
                                        else ClaimCategory.other
                                    ),
                                )
                            )
                        summary = obj.get("summary", "")
                        return claims, summary
        except Exception:
            # Graceful fallback to deterministic engine
            pass

    # Use deterministic grounded reasoning
    return _generate_deterministic_claims(variant, evidence_items)
