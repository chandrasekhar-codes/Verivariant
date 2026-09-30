export type GenomeBuild = "GRCh37" | "GRCh38";

export type EvidenceSource = "clinvar" | "gnomad" | "ensembl_vep";

export type EvidenceStatus = "found" | "not_found" | "cached" | "error";

export type VerificationStatus =
  | "supported"
  | "partially_supported"
  | "unsupported"
  | "unclear";

export type ClaimCategory =
  | "clinical_significance"
  | "population_frequency"
  | "functional_consequence"
  | "pathogenicity_summary"
  | "other";

export interface Variant {
  id: string;
  chrom: string;
  pos: number;
  ref: string;
  alt: string;
  rsid: string | null;
  qual: number | null;
  filter: string | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  info: Record<string, any>;
  genome_build: GenomeBuild;
  key: string;
  gene?: string | null;
  consequence?: string | null;
  hgvsc?: string | null;
  hgvsp?: string | null;
  clinvar_sig?: string | null;
  gnomad_af?: number | null;
}

export interface EvidenceItem {
  id: string;
  variant_key: string;
  source: EvidenceSource;
  status: EvidenceStatus;
  url: string | null;
  retrieved_at: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: Record<string, any>;
  is_demo_data?: boolean;
  error_message?: string | null;
}

export interface ClaimVerification {
  status: VerificationStatus;
  verdict: VerificationStatus;
  reason: string;
  confidence: number;
  checked_by: "verification_agent" | "citation_checker";
}

export interface Claim {
  id: string;
  variant_key: string;
  text: string;
  claim?: string | null;
  evidence: string;
  source: string;
  source_url: string | null;
  category: ClaimCategory;
  evidence_ids: string[];
  verification?: ClaimVerification | null;
}

export interface ConflictItem {
  variant_key: string;
  gene: string;
  conflict_type: string;
  description: string;
  clinvar_assertion?: string | null;
  gnomad_frequency?: string | null;
  vep_consequence?: string | null;
  recommendation: string;
}

export interface VariantReport {
  variant: Variant;
  evidence: EvidenceItem[];
  claims: Claim[];
  summary: string;
  overall_confidence: string;
  conflicts: ConflictItem[];
  notes?: string | null;
}

export interface PipelineLogEntry {
  stage: string;
  message: string;
  at: string;
  status: "running" | "complete" | "warning" | "error";
}

export interface Report {
  job_id: string;
  created_at: string;
  genome_build: GenomeBuild;
  variants: VariantReport[];
  rejected_claims: Claim[];
  conflicts: ConflictItem[];
  sources_used: string[];
  total_variants: number;
  total_claims: number;
  supported_claims: number;
  unsupported_claims: number;
  unclear_claims: number;
  summary: string;
  limitations: string[];
  disclaimer: string;
  is_demo: boolean;
  pipeline_log: PipelineLogEntry[];
}

export interface SourcesStatus {
  disclaimer: string;
  sources: {
    clinvar?: { name: string; ok: boolean; status_code?: number };
    gnomad?: { name: string; ok: boolean; status_code?: number };
    ensembl_vep?: { name: string; ok: boolean; status_code?: number };
  };
}
