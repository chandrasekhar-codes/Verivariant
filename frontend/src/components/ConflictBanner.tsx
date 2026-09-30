import React from "react";
import { AlertTriangle, ShieldAlert } from "lucide-react";
import { ConflictItem } from "../types/genomics";

interface ConflictBannerProps {
  conflicts: ConflictItem[];
  onInspectVariant?: (variantKey: string) => void;
}

export const ConflictBanner: React.FC<ConflictBannerProps> = ({
  conflicts,
  onInspectVariant,
}) => {
  if (!conflicts || conflicts.length === 0) return null;

  return (
    <div className="my-6 space-y-4">
      {conflicts.map((c, i) => (
        <div
          key={i}
          className="rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-950/40 via-slate-900/80 to-slate-900/60 p-5 shadow-lg relative overflow-hidden backdrop-blur-md"
        >
          {/* Subtle amber accent bar */}
          <div className="absolute top-0 left-0 bottom-0 w-1.5 bg-amber-400" />

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-amber-500/20 mb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div>
                <span className="text-[11px] font-mono uppercase tracking-wider text-amber-400 font-semibold">
                  Scientific Discordance Warning
                </span>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>Conflicting Evidence Detected:</span>
                  <span className="text-cyan-400 font-mono text-sm">
                    {c.gene} ({c.variant_key})
                  </span>
                </h3>
              </div>
            </div>

            {onInspectVariant && (
              <button
                onClick={() => onInspectVariant(c.variant_key)}
                className="self-start md:self-auto px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/30 text-xs font-semibold transition-all cursor-pointer"
              >
                Inspect Evidence Matrix
              </button>
            )}
          </div>

          <p className="text-xs text-slate-300 mb-4 leading-relaxed">
            {c.description}
          </p>

          {/* Side-by-side Evidence Breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3 text-xs">
            <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800">
              <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider mb-1 font-semibold">
                NCBI ClinVar
              </div>
              <div className="font-semibold text-slate-200">
                {c.clinvar_assertion || "Not available"}
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800">
              <div className="text-[10px] font-mono text-indigo-400 uppercase tracking-wider mb-1 font-semibold">
                Broad gnomAD v4
              </div>
              <div className="font-semibold text-slate-200">
                AF = {c.gnomad_frequency || "Not available"}
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800">
              <div className="text-[10px] font-mono text-teal-400 uppercase tracking-wider mb-1 font-semibold">
                Ensembl VEP
              </div>
              <div className="font-semibold text-slate-200">
                {c.vep_consequence || "Not available"}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-amber-300/90 bg-amber-500/10 px-3 py-2 rounded-lg border border-amber-500/20">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span>
              <strong>Recommendation:</strong> {c.recommendation}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};
