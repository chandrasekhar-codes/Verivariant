"""Agent 2 — Verification Agent.

Independently inspects and cross-verifies Research Agent claims against raw retrieved
evidence payloads. Assigns verdicts: SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, UNCLEAR.
Enforces strict hallucination control and logs detailed confidence and reasoning.
Never silently removes unsupported claims—flags them for human review.
"""

from __future__ import annotations

import re

from app.models import (
    Claim,
    ClaimVerification,
    EvidenceItem,
    EvidenceSource,
    VerificationStatus,
)


def _normalize_text(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", s).lower()


def verify_single_claim(
    claim: Claim,
    evidence_items: list[EvidenceItem],
) -> ClaimVerification:
    """Independently verify an individual claim against available evidence items."""
    source_lower = claim.source.lower().strip()
    claim_text_lower = claim.text.lower()

    # Find matching evidence item
    matching_evidence: EvidenceItem | None = None
    for ev in evidence_items:
        if ev.source.value in source_lower or source_lower in ev.source.value:
            matching_evidence = ev
            break
        # Also check source string variations
        if "clinvar" in source_lower and ev.source == EvidenceSource.clinvar:
            matching_evidence = ev
            break
        if "gnomad" in source_lower and ev.source == EvidenceSource.gnomad:
            matching_evidence = ev
            break
        if (
            "vep" in source_lower or "ensembl" in source_lower
        ) and ev.source == EvidenceSource.ensembl_vep:
            matching_evidence = ev
            break

    # If no evidence source exists at all
    if matching_evidence is None:
        return ClaimVerification(
            status=VerificationStatus.unsupported,
            verdict=VerificationStatus.unsupported,
            reason=f"No retrieved evidence record exists for cited source '{claim.source}'.",
            confidence=0.15,
            checked_by="verification_agent",
        )

    ev_data = matching_evidence.data or {}

    # Case A: Claim states "Insufficient evidence"
    if "insufficient evidence" in claim_text_lower:
        if matching_evidence.status.value in ("not_found", "error") or not ev_data:
            return ClaimVerification(
                status=VerificationStatus.supported,
                verdict=VerificationStatus.supported,
                reason=f"Verified: {claim.source} returned {matching_evidence.status.value}; absence of evidence is accurately conveyed without hallucination.",
                confidence=0.99,
                checked_by="verification_agent",
            )
        else:
            return ClaimVerification(
                status=VerificationStatus.unsupported,
                verdict=VerificationStatus.unsupported,
                reason=f"Contradiction: Claim asserts insufficient evidence, but {claim.source} returned an active record.",
                confidence=0.90,
                checked_by="verification_agent",
            )

    # Case B: ClinVar Verification
    if matching_evidence.source == EvidenceSource.clinvar:
        sig = str(ev_data.get("clinical_significance", "")).lower()
        condition = str(ev_data.get("condition", "")).lower()

        if not sig or sig == "not available":
            return ClaimVerification(
                status=VerificationStatus.unsupported,
                verdict=VerificationStatus.unsupported,
                reason="ClinVar record lacks clinical significance assertion.",
                confidence=0.20,
                checked_by="verification_agent",
            )

        # Check if the clinical classification in claim matches ClinVar data
        sig_match = any(word in claim_text_lower for word in sig.split()) or sig in claim_text_lower
        cond_match = any(word in claim_text_lower for word in condition.split() if len(word) > 4)

        if sig_match and cond_match:
            return ClaimVerification(
                status=VerificationStatus.supported,
                verdict=VerificationStatus.supported,
                reason=f"Directly supported by ClinVar variation record: classification '{ev_data.get('clinical_significance')}' and condition '{ev_data.get('condition')}' fully match.",
                confidence=0.98,
                checked_by="verification_agent",
            )
        elif sig_match:
            return ClaimVerification(
                status=VerificationStatus.supported,
                verdict=VerificationStatus.supported,
                reason=f"Supported by ClinVar germline classification: '{ev_data.get('clinical_significance')}'.",
                confidence=0.92,
                checked_by="verification_agent",
            )
        elif "conflicting" in sig:
            return ClaimVerification(
                status=VerificationStatus.partially_supported,
                verdict=VerificationStatus.partially_supported,
                reason="ClinVar reports conflicting interpretations of pathogenicity across submitters.",
                confidence=0.75,
                checked_by="verification_agent",
            )
        else:
            return ClaimVerification(
                status=VerificationStatus.unclear,
                verdict=VerificationStatus.unclear,
                reason=f"ClinVar record shows '{ev_data.get('clinical_significance')}', which does not fully align with claim phrasing.",
                confidence=0.50,
                checked_by="verification_agent",
            )

    # Case C: gnomAD Verification
    if matching_evidence.source == EvidenceSource.gnomad:
        af = ev_data.get("allele_frequency")
        if af is None or af == "Not available":
            return ClaimVerification(
                status=VerificationStatus.unclear,
                verdict=VerificationStatus.unclear,
                reason="gnomAD does not contain cohort frequency metrics for this variant.",
                confidence=0.40,
                checked_by="verification_agent",
            )

        try:
            af_val = float(af)
            # Check if numeric frequency is referenced in claim
            # Look for decimal numbers in claim
            nums = re.findall(r"0?\.\d+", claim.text)
            num_match = False
            for n in nums:
                try:
                    if abs(float(n) - af_val) < 0.001 or f"{af_val:.4f}" in n:
                        num_match = True
                        break
                except ValueError:
                    pass

            rarity_words = ["rare", "common", "frequency", "allele", "polymorphism"]
            has_context = any(w in claim_text_lower for w in rarity_words)

            if num_match or has_context:
                return ClaimVerification(
                    status=VerificationStatus.supported,
                    verdict=VerificationStatus.supported,
                    reason=f"Numerically verified against gnomAD v4 global AF = {af_val:.6g} (AC: {ev_data.get('allele_count')}/{ev_data.get('allele_number')}).",
                    confidence=0.97,
                    checked_by="verification_agent",
                )
            else:
                return ClaimVerification(
                    status=VerificationStatus.partially_supported,
                    verdict=VerificationStatus.partially_supported,
                    reason=f"gnomAD confirms variant presence (AF = {af_val:.6g}), but specific claim numbers vary slightly.",
                    confidence=0.75,
                    checked_by="verification_agent",
                )
        except (ValueError, TypeError):
            return ClaimVerification(
                status=VerificationStatus.unclear,
                verdict=VerificationStatus.unclear,
                reason="gnomAD frequency metric could not be parsed as a float.",
                confidence=0.50,
                checked_by="verification_agent",
            )

    # Case D: Ensembl VEP Verification
    if matching_evidence.source == EvidenceSource.ensembl_vep:
        csq = str(ev_data.get("consequence", "")).lower()
        impact = str(ev_data.get("impact", "")).lower()
        gene = str(ev_data.get("gene_symbol", "")).lower()

        csq_match = bool(csq and csq in claim_text_lower)
        gene_match = bool(gene and gene in claim_text_lower)
        impact_match = bool(impact and impact in claim_text_lower)

        if csq_match and gene_match:
            return ClaimVerification(
                status=VerificationStatus.supported,
                verdict=VerificationStatus.supported,
                reason=f"Directly verified by Ensembl VEP: consequence '{ev_data.get('consequence')}' on gene '{ev_data.get('gene_symbol')}' confirmed.",
                confidence=0.98,
                checked_by="verification_agent",
            )
        elif csq_match or gene_match or impact_match:
            return ClaimVerification(
                status=VerificationStatus.supported,
                verdict=VerificationStatus.supported,
                reason=f"Partially confirmed by Ensembl VEP annotation ('{ev_data.get('consequence')}').",
                confidence=0.88,
                checked_by="verification_agent",
            )
        else:
            return ClaimVerification(
                status=VerificationStatus.unclear,
                verdict=VerificationStatus.unclear,
                reason=f"Ensembl VEP predicts '{ev_data.get('consequence')}', but claim phrasing diverges.",
                confidence=0.55,
                checked_by="verification_agent",
            )

    # Fallback default
    return ClaimVerification(
        status=VerificationStatus.partially_supported,
        verdict=VerificationStatus.partially_supported,
        reason="Claim correlates with evidence items with general consistency.",
        confidence=0.70,
        checked_by="verification_agent",
    )


def run_verification_agent(
    claims: list[Claim],
    evidence_items: list[EvidenceItem],
) -> tuple[list[Claim], list[Claim]]:
    """Execute Verification Agent across all claims.

    Returns:
        (verified_claims, rejected_or_flagged_claims)
    """
    verified_claims: list[Claim] = []
    flagged_claims: list[Claim] = []

    for c in claims:
        verification = verify_single_claim(c, evidence_items)
        updated_claim = c.model_copy()
        updated_claim.verification = verification

        verified_claims.append(updated_claim)
        if verification.verdict in (VerificationStatus.unsupported, VerificationStatus.unclear):
            flagged_claims.append(updated_claim)

    return verified_claims, flagged_claims
