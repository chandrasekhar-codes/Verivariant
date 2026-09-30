import React from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Database,
  Dna,
  ExternalLink,
  HelpCircle,
  Layers,
  ShieldCheck,
  X,
  XCircle,
} from "lucide-react";
import {
  VariantReport,
  VerificationStatus,
} from "../types/genomics";

interface VariantDetailModalProps {
  variantReport: VariantReport | null;
  onClose: () => void;
  isDemo?: boolean;
}

export const VariantDetailModal: React.FC<VariantDetailModalProps> = ({
  variantReport,
  onClose,
  isDemo,
}) => {
  if (!variantReport) return null;

  const v = variantReport.variant;
  const clinvar = variantReport.evidence.find((e) => e.source === "clinvar");
  const gnomad = variantReport.evidence.find((e) => e.source === "gnomad");
  const vep = variantReport.evidence.find((e) => e.source === "ensembl_vep");

  const getVerdictBadge = (verdict?: VerificationStatus) => {
    switch (verdict) {
      case "supported":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            SUPPORTED
          </span>
        );
      case "partially_supported":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            PARTIALLY SUPPORTED
          </span>
        );
      case "unsupported":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40">
            <XCircle className="w-3.5 h-3.5 text-rose-400" />
            UNSUPPORTED
          </span>
        );
      case "unclear":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-slate-800 text-slate-300 border border-slate-700">
            <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            UNCLEAR
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-6">
      <div className="glass-panel w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-2xl border border-slate-700 shadow-2xl p-6 sm:p-8 relative text-slate-100">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer border border-slate-800"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-5 border-b border-slate-800 gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Dna className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white font-mono">
                  {v.key}
                </h2>
                {v.gene && (
                  <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 text-xs font-bold font-mono">
                    {v.gene}
                  </span>
                )}
                {isDemo && (
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 text-[10px] font-mono">
                    DEMO DATA
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5 font-mono">
                {v.rsid ? `dbSNP: ${v.rsid}` : "Novel / Unregistered rsID"} · {v.genome_build}
              </p>
            </div>
          </div>
        </div>

        {/* Section 1: Variant Overview */}
        <div className="mt-6 mb-8">
          <h3 className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold mb-3 flex items-center gap-2">
            <Layers className="w-3.5 h-3.5" />
            <span>VARIANT OVERVIEW</span>
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-900/60 p-4 rounded-xl border border-slate-800 text-xs">
            <div>
              <span className="text-slate-400 block text-[11px]">Variant ID</span>
              <span className="font-mono font-medium text-slate-200">{v.id}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Chromosome</span>
              <span className="font-mono font-medium text-slate-200">chr{v.chrom}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Position</span>
              <span className="font-mono font-medium text-slate-200">{v.pos.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Ref / Alt</span>
              <span className="font-mono font-medium text-cyan-300">{v.ref} → {v.alt}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Associated Gene</span>
              <span className="font-semibold text-white">{v.gene || "Not available"}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Consequence</span>
              <span className="font-mono text-slate-200">{v.consequence || "Not available"}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">cDNA Change (HGVSc)</span>
              <span className="font-mono text-slate-200">{v.hgvsc || "Not available"}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Protein Change (HGVSp)</span>
              <span className="font-mono text-slate-200">{v.hgvsp || "Not available"}</span>
            </div>
          </div>
        </div>

        {/* Section 2: Retrieved Evidence (ClinVar, gnomAD, Ensembl VEP) */}
        <div className="mb-8">
          <h3 className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold mb-3 flex items-center gap-2">
            <Database className="w-3.5 h-3.5" />
            <span>GENOMIC EVIDENCE SOURCES</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* ClinVar Evidence Card */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                  <span className="text-xs font-bold text-cyan-300 font-mono">
                    NCBI CLINVAR
                  </span>
                  {clinvar?.url && (
                    <a
                      href={clinvar.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:text-cyan-300 transition-colors"
                      title="Open ClinVar Entry"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Clinical Significance</span>
                    <span className="font-semibold text-white">
                      {clinvar?.data?.clinical_significance || "Not available"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Condition</span>
                    <span className="text-slate-300">
                      {clinvar?.data?.condition || "Not available"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Review Status</span>
                    <span className="text-slate-400 font-mono text-[11px]">
                      {clinvar?.data?.review_status || "Not available"}
                    </span>
                  </div>
                </div>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-800/80 text-[11px] text-slate-500 font-mono">
                Variation ID: {clinvar?.data?.variation_id || "N/A"}
              </div>
            </div>

            {/* gnomAD Evidence Card */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                  <span className="text-xs font-bold text-indigo-300 font-mono">
                    GNOMAD v4 COHORTS
                  </span>
                  {gnomad?.url && (
                    <a
                      href={gnomad.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-400 hover:text-indigo-300 transition-colors"
                      title="Open gnomAD Entry"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Global Allele Frequency</span>
                    <span className="font-mono font-semibold text-indigo-300">
                      {gnomad?.data?.allele_frequency !== undefined &&
                      gnomad?.data?.allele_frequency !== "Not available"
                        ? Number(gnomad.data.allele_frequency).toExponential(3)
                        : "Not available"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Allele Count / Total</span>
                    <span className="font-mono text-slate-300">
                      {gnomad?.data?.allele_count || "N/A"} / {gnomad?.data?.allele_number || "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Homozygotes</span>
                    <span className="font-mono text-slate-300">
                      {gnomad?.data?.homozygote_count !== undefined ? gnomad.data.homozygote_count : "0"}
                    </span>
                  </div>
                </div>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-800/80 text-[11px] text-slate-500 font-mono">
                Populations: European, African, Asian
              </div>
            </div>

            {/* Ensembl VEP Evidence Card */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                  <span className="text-xs font-bold text-teal-300 font-mono">
                    ENSEMBL VEP
                  </span>
                  {vep?.url && (
                    <a
                      href={vep.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-teal-400 hover:text-teal-300 transition-colors"
                      title="Open Ensembl Entry"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Consequence & Impact</span>
                    <span className="font-mono font-semibold text-teal-300">
                      {vep?.data?.consequence || "Not available"} ({vep?.data?.impact || "N/A"})
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Transcript ID</span>
                    <span className="font-mono text-slate-300 text-[11px]">
                      {vep?.data?.transcript_id || "Not available"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">SIFT / PolyPhen</span>
                    <span className="text-slate-400 font-mono text-[11px]">
                      {vep?.data?.sift || "N/A"} / {vep?.data?.polyphen || "N/A"}
                    </span>
                  </div>
                </div>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-800/80 text-[11px] text-slate-500 font-mono">
                Biotype: {vep?.data?.biotype || "protein_coding"}
              </div>
            </div>
          </div>
        </div>

        {/* Section 3: Multi-Agent Grounded Claims & Verification Matrix */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>CLAIM-LEVEL TRACEABILITY & VERIFICATION MATRIX</span>
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">
              Audited by Verification Agent
            </span>
          </div>

          <div className="space-y-3">
            {variantReport.claims.map((claim, idx) => (
              <div
                key={claim.id || idx}
                className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors text-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 mb-2 border-b border-slate-800/70">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      Source: {claim.source}
                    </span>
                    {claim.source_url && (
                      <a
                        href={claim.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-cyan-400 hover:text-cyan-300 inline-flex items-center gap-0.5 text-[11px] font-mono"
                      >
                        <span>Official Record</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                  <div>{getVerdictBadge(claim.verification?.verdict)}</div>
                </div>

                <div className="mb-2">
                  <span className="text-[11px] text-slate-400 font-semibold block uppercase font-mono">
                    Research Agent Claim:
                  </span>
                  <p className="text-slate-100 font-medium leading-relaxed mt-0.5">
                    {claim.text}
                  </p>
                </div>

                {claim.verification && (
                  <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 text-[11px]">
                    <div className="flex items-center justify-between text-slate-400 mb-1">
                      <span className="font-mono">
                        Verification Agent Audit (Checked by: {claim.verification.checked_by})
                      </span>
                      <span className="font-mono text-cyan-300 font-semibold">
                        Confidence: {(claim.verification.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-slate-300 leading-normal">
                      {claim.verification.reason}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
