import React from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Database,
  ExternalLink,
  FileText,
  Printer,
  ShieldAlert,
} from "lucide-react";
import { Report, VariantReport } from "../types/genomics";
import { ConflictBanner } from "./ConflictBanner";

interface ReportViewProps {
  report: Report;
  onInspectVariant: (vr: VariantReport) => void;
}

export const ReportView: React.FC<ReportViewProps> = ({
  report,
  onInspectVariant,
}) => {
  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Report Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-48 h-48 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-5 border-b border-slate-800">
          <div>
            <span className="text-[11px] font-mono uppercase tracking-widest text-cyan-400 font-semibold">
              GENESIS Multi-Agent Report
            </span>
            <h1 className="text-2xl font-bold text-white mt-1 flex items-center gap-3">
              <FileText className="w-6 h-6 text-cyan-400" />
              Genomic Variant Analysis Report
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Job ID: {report.job_id.substring(0, 12)}... · Generated:{" "}
              {new Date(report.created_at).toLocaleString()} · Build:{" "}
              {report.genome_build}
            </p>
          </div>

          <div className="flex items-center gap-2 no-print">
            {report.is_demo && (
              <span className="px-3 py-1.5 rounded-lg bg-cyan-950/80 border border-cyan-500/40 text-[11px] font-mono text-cyan-300 font-semibold">
                DEMO DATA
              </span>
            )}
            <button
              onClick={handlePrint}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Export Report</span>
            </button>
          </div>
        </div>

        {/* Executive Summary */}
        <div className="mt-5">
          <h3 className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold mb-2">
            Executive Summary
          </h3>
          <p className="text-sm text-slate-300 leading-relaxed">
            {report.summary}
          </p>
        </div>
      </div>

      {/* Metrics Dashboard */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="glass-panel p-4 rounded-xl border border-slate-800 text-center">
          <div className="text-3xl font-bold text-white font-mono">
            {report.total_variants}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-medium">
            Variants Analyzed
          </div>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-800 text-center">
          <div className="text-3xl font-bold text-cyan-400 font-mono">
            {report.total_claims}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-medium">
            Total Claims
          </div>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-800 text-center">
          <div className="text-3xl font-bold text-emerald-400 font-mono">
            {report.supported_claims}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-medium">
            Supported
          </div>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-800 text-center">
          <div className="text-3xl font-bold text-rose-400 font-mono">
            {report.unsupported_claims}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-medium">
            Unsupported
          </div>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-slate-800 text-center">
          <div className="text-3xl font-bold text-amber-400 font-mono">
            {report.conflicts.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-medium">
            Evidence Conflicts
          </div>
        </div>
      </div>

      {/* Conflict Detection */}
      {report.conflicts.length > 0 && (
        <div>
          <h3 className="text-xs font-mono uppercase tracking-wider text-amber-400 font-bold mb-3 flex items-center gap-2">
            <AlertTriangle className="w-3.5 h-3.5" />
            Conflicting Evidence Detected
          </h3>
          <ConflictBanner
            conflicts={report.conflicts}
            onInspectVariant={(key) => {
              const vr = report.variants.find(
                (v) => v.variant.key === key
              );
              if (vr) onInspectVariant(vr);
            }}
          />
        </div>
      )}

      {/* Variant-Level Summaries */}
      <div>
        <h3 className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold mb-4 flex items-center gap-2">
          <Database className="w-3.5 h-3.5" />
          Variant Evidence & Research Findings
        </h3>
        <div className="space-y-4">
          {report.variants.map((vr) => {
            const v = vr.variant;
            const supportedCount = vr.claims.filter(
              (c) =>
                c.verification?.verdict === "supported" ||
                c.verification?.verdict === "partially_supported"
            ).length;
            const hasConflict = vr.conflicts && vr.conflicts.length > 0;

            return (
              <div
                key={v.key}
                onClick={() => onInspectVariant(vr)}
                className="glass-panel p-5 rounded-xl border border-slate-800 hover:border-cyan-500/30 cursor-pointer transition-all group"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-white font-mono group-hover:text-cyan-300 transition-colors">
                      {v.key}
                    </span>
                    {v.gene && (
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700 text-xs font-bold font-mono">
                        {v.gene}
                      </span>
                    )}
                    {v.rsid && (
                      <span className="text-xs font-mono text-slate-400">
                        {v.rsid}
                      </span>
                    )}
                    {hasConflict && (
                      <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] font-mono font-semibold">
                        ⚠ CONFLICT
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-xs">
                    <span className="flex items-center gap-1 text-emerald-400 font-mono font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      {supportedCount}/{vr.claims.length} verified
                    </span>
                    <span className="text-slate-400">→ Click to inspect</span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 mt-3 leading-relaxed">
                  {vr.summary}
                </p>

                <div className="grid grid-cols-3 gap-3 mt-3 text-xs">
                  <div className="bg-slate-900/90 p-2 rounded-lg border border-slate-800">
                    <span className="text-[10px] font-mono text-cyan-400 uppercase block mb-0.5">
                      ClinVar
                    </span>
                    <span className="font-semibold text-slate-200">
                      {v.clinvar_sig || "N/A"}
                    </span>
                  </div>
                  <div className="bg-slate-900/90 p-2 rounded-lg border border-slate-800">
                    <span className="text-[10px] font-mono text-indigo-400 uppercase block mb-0.5">
                      gnomAD AF
                    </span>
                    <span className="font-mono text-slate-200">
                      {v.gnomad_af !== undefined && v.gnomad_af !== null
                        ? Number(v.gnomad_af).toExponential(2)
                        : "N/A"}
                    </span>
                  </div>
                  <div className="bg-slate-900/90 p-2 rounded-lg border border-slate-800">
                    <span className="text-[10px] font-mono text-teal-400 uppercase block mb-0.5">
                      Consequence
                    </span>
                    <span className="font-mono text-slate-200">
                      {v.consequence || "N/A"}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Sources Used */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800">
        <h3 className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold mb-3 flex items-center gap-2">
          <ExternalLink className="w-3.5 h-3.5" />
          Primary Genomic Sources
        </h3>
        <ul className="space-y-2 text-xs text-slate-300">
          {report.sources_used.map((s, i) => (
            <li key={i} className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              {s}
            </li>
          ))}
        </ul>
      </div>

      {/* Limitations */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800">
        <h3 className="text-xs font-mono uppercase tracking-wider text-amber-400 font-bold mb-3 flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5" />
          Limitations & Known Caveats
        </h3>
        <ul className="space-y-2 text-xs text-slate-400">
          {report.limitations.map((l, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
              <span>{l}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Safety Disclaimer */}
      <div className="p-5 rounded-xl bg-rose-950/20 border border-rose-500/30 flex items-start gap-3 text-xs">
        <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-bold text-rose-300 mb-1">
            Medical Safety Disclaimer
          </h4>
          <p className="text-rose-200/80 leading-relaxed">
            {report.disclaimer}
          </p>
        </div>
      </div>
    </div>
  );
};
