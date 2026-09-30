from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

DISCLAIMER = (
    "GENESIS is a research and report-drafting prototype. It does not provide medical diagnosis "
    "or treatment recommendations. Results require review by qualified professionals."
)

__all__ = [
    "DISCLAIMER",
    "Claim",
    "ClaimCategory",
    "ClaimVerification",
    "ConflictItem",
    "EvidenceItem",
    "EvidenceSource",
    "EvidenceStatus",
    "GenomeBuild",
    "PipelineLogEntry",
    "Report",
    "Variant",
    "VariantReport",
    "VerificationStatus",
]


class GenomeBuild(str, Enum):
    grch37 = "GRCh37"
    grch38 = "GRCh38"


class EvidenceSource(str, Enum):
    clinvar = "clinvar"
    gnomad = "gnomad"
    ensembl_vep = "ensembl_vep"


class EvidenceStatus(str, Enum):
    found = "found"
    not_found = "not_found"
    cached = "cached"
    error = "error"


class ClaimCategory(str, Enum):
    clinical_significance = "clinical_significance"
    population_frequency = "population_frequency"
    functional_consequence = "functional_consequence"
    pathogenicity_summary = "pathogenicity_summary"
    other = "other"


class VerificationStatus(str, Enum):
    supported = "supported"
    partially_supported = "partially_supported"
    unsupported = "unsupported"
    unclear = "unclear"


class Variant(BaseModel):
    id: str
    chrom: str
    pos: int
    ref: str
    alt: str
    rsid: str | None = None
    qual: float | None = None
    filter: str | None = None
    info: dict[str, Any] = Field(default_factory=dict)
    genome_build: GenomeBuild = GenomeBuild.grch38
    key: str
    # Enriched convenience properties
    gene: str | None = None
    consequence: str | None = None
    hgvsc: str | None = None
    hgvsp: str | None = None
    clinvar_sig: str | None = None
    gnomad_af: float | None = None


class EvidenceItem(BaseModel):
    id: str
    variant_key: str
    source: EvidenceSource
    status: EvidenceStatus
    url: str | None = None
    retrieved_at: datetime
    data: dict[str, Any] = Field(default_factory=dict)
    is_demo_data: bool = False
    error_message: str | None = None


class ClaimVerification(BaseModel):
    status: VerificationStatus
    verdict: VerificationStatus = VerificationStatus.supported
    reason: str
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    checked_by: Literal["verification_agent", "citation_checker"] = "verification_agent"


class Claim(BaseModel):
    id: str
    variant_key: str
    text: str
    claim: str | None = None  # alias for text if provided
    evidence: str = ""
    source: str = ""
    source_url: str | None = None
    category: ClaimCategory = ClaimCategory.other
    evidence_ids: list[str] = Field(default_factory=list)
    verification: ClaimVerification | None = None

    def model_post_init(self, context: Any, /) -> None:
        if self.claim is None:
            self.claim = self.text
        elif not self.text:
            self.text = self.claim


class ConflictItem(BaseModel):
    variant_key: str
    gene: str
    conflict_type: str
    description: str
    clinvar_assertion: str | None = None
    gnomad_frequency: str | None = None
    vep_consequence: str | None = None
    recommendation: str = "Recommend multidisciplinary clinical review by a certified geneticist."


class VariantReport(BaseModel):
    variant: Variant
    evidence: list[EvidenceItem] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    summary: str = ""
    overall_confidence: str = "High"
    conflicts: list[ConflictItem] = Field(default_factory=list)
    notes: str | None = None


class PipelineLogEntry(BaseModel):
    stage: str
    message: str
    at: datetime
    status: Literal["running", "complete", "warning", "error"] = "complete"


class Report(BaseModel):
    job_id: str
    created_at: datetime
    genome_build: GenomeBuild
    variants: list[VariantReport]
    rejected_claims: list[Claim] = Field(default_factory=list)
    conflicts: list[ConflictItem] = Field(default_factory=list)
    sources_used: list[str] = Field(default_factory=list)
    total_variants: int = 0
    total_claims: int = 0
    supported_claims: int = 0
    unsupported_claims: int = 0
    unclear_claims: int = 0
    summary: str = ""
    limitations: list[str] = Field(default_factory=list)
    disclaimer: str = DISCLAIMER
    is_demo: bool = False
    pipeline_log: list[PipelineLogEntry] = Field(default_factory=list)
