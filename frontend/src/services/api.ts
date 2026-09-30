import {
  Claim,
  ClaimVerification,
  EvidenceItem,
  Report,
  SourcesStatus,
  VariantReport,
} from "../types/genomics";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function checkHealth(): Promise<{ status: string; disclaimer: string }> {
  const resp = await fetch(`${API_BASE}/api/health`);
  if (!resp.ok) {
    throw new Error(`Health check failed with status ${resp.status}`);
  }
  return resp.json();
}

export async function getSourcesStatus(): Promise<SourcesStatus> {
  const resp = await fetch(`${API_BASE}/api/sources/status`);
  if (!resp.ok) {
    throw new Error(`Sources status failed with status ${resp.status}`);
  }
  return resp.json();
}

export async function analyzeVcf(
  file: File | null,
  demo: boolean = false,
  genomeBuild: string = "GRCh38"
): Promise<Report> {
  const url = new URL(`${API_BASE}/api/analyze-vcf`);
  if (demo) {
    url.searchParams.set("demo", "true");
  }
  if (genomeBuild) {
    url.searchParams.set("genome_build", genomeBuild);
  }

  const formData = new FormData();
  if (file && !demo) {
    formData.append("file", file);
  }

  const resp = await fetch(url.toString(), {
    method: "POST",
    body: demo ? undefined : formData,
  });

  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Analysis request failed with status ${resp.status}`
    );
  }

  return resp.json();
}

export async function runDemoAnalysis(): Promise<Report> {
  const resp = await fetch(`${API_BASE}/api/demo`, {
    method: "POST",
  });

  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Demo request failed with status ${resp.status}`
    );
  }

  return resp.json();
}

export async function getReport(analysisId: string): Promise<Report> {
  const resp = await fetch(`${API_BASE}/api/report/${analysisId}`);
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Failed to fetch report ${analysisId}`
    );
  }
  return resp.json();
}

export async function getVariantDetails(
  analysisId: string,
  variantId: string
): Promise<VariantReport> {
  const resp = await fetch(
    `${API_BASE}/api/variant/${encodeURIComponent(analysisId)}/${encodeURIComponent(variantId)}`
  );
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Failed to fetch variant details`
    );
  }
  return resp.json();
}

export async function verifyCustomClaim(
  claim: Claim,
  evidenceItems: EvidenceItem[]
): Promise<{ claim_id: string; verification: ClaimVerification }> {
  const resp = await fetch(`${API_BASE}/api/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      claim,
      evidence_items: evidenceItems,
    }),
  });

  if (!resp.ok) {
    throw new Error(`Verification endpoint failed with status ${resp.status}`);
  }
  return resp.json();
}
