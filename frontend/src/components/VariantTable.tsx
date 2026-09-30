import React, { useState } from "react";
import {
  ChevronRight,
  Search,
  ShieldCheck,
  SlidersHorizontal,
} from "lucide-react";
import { VariantReport } from "../types/genomics";

interface VariantTableProps {
  variants: VariantReport[];
  onSelectVariant: (vr: VariantReport) => void;
  isDemo?: boolean;
}

export const VariantTable: React.FC<VariantTableProps> = ({
  variants,
  onSelectVariant,
  isDemo,
}) => {
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [sigFilter, setSigFilter] = useState<string>("all");

  const filteredVariants = variants.filter((vr) => {
    const v = vr.variant;
    const term = searchTerm.toLowerCase();
    const matchesSearch =
      v.key.toLowerCase().includes(term) ||
      (v.gene && v.gene.toLowerCase().includes(term)) ||
      (v.rsid && v.rsid.toLowerCase().includes(term)) ||
      (v.consequence && v.consequence.toLowerCase().includes(term));

    if (!matchesSearch) return false;

    if (sigFilter === "all") return true;
    if (sigFilter === "pathogenic") {
      return v.clinvar_sig && v.clinvar_sig.toLowerCase().includes("pathogenic");
    }
    if (sigFilter === "conflict") {
      return (
        v.clinvar_sig && v.clinvar_sig.toLowerCase().includes("conflicting")
      );
    }
    if (sigFilter === "risk") {
      return v.clinvar_sig && v.clinvar_sig.toLowerCase().includes("risk");
    }
    return true;
  });

  const getSigBadge = (sig?: string | null) => {
    if (!sig || sig === "Not available") {
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-400 border border-slate-700">
          Not available
        </span>
      );
    }
    const lower = sig.toLowerCase();
    if (lower.includes("pathogenic") && !lower.includes("conflict")) {
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-rose-500/20 text-rose-300 border border-rose-500/30">
          {sig}
        </span>
      );
    }
    if (lower.includes("benign")) {
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
          {sig}
        </span>
      );
    }
    if (lower.includes("conflict")) {
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30">
          Conflicting
        </span>
      );
    }
    if (lower.includes("risk")) {
      return (
        <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
          Risk factor
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
        {sig}
      </span>
    );
  };

  const getAfBadge = (af?: number | null) => {
    if (af === undefined || af === null) {
      return (
        <span className="text-slate-500 font-mono text-xs">Unobserved</span>
      );
    }
    return (
      <span className="font-mono text-xs text-indigo-300">
        {af < 0.0001 ? af.toExponential(2) : (af * 100).toFixed(2) + "%"}
      </span>
    );
  };

  const getVerificationStatus = (vr: VariantReport) => {
    const claims = vr.claims;
    if (claims.length === 0) return "Pending";
    const supported = claims.filter(
      (c) =>
        c.verification?.verdict === "supported" ||
        c.verification?.verdict === "partially_supported"
    ).length;
    return `${supported}/${claims.length} Verified`;
  };

  return (
    <div className="space-y-4">
      {/* Controls & Search */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Filter by gene, rsID, or variant key..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
          />
        </div>

        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-400">Filter:</span>
          <select
            value={sigFilter}
            onChange={(e) => setSigFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-cyan-500/50"
          >
            <option value="all">All Classifications</option>
            <option value="pathogenic">Pathogenic Only</option>
            <option value="conflict">Conflicting Only</option>
            <option value="risk">Risk Factors</option>
          </select>

          {isDemo && (
            <span className="px-2.5 py-1 rounded-md bg-cyan-950/80 border border-cyan-500/40 text-[11px] font-mono text-cyan-300 font-semibold ml-auto">
              DEMO DATA
            </span>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800 glass-panel">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-slate-900/90 text-slate-400 font-mono text-[11px] uppercase tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Variant & rsID</th>
              <th className="py-3 px-4">Gene</th>
              <th className="py-3 px-4">Locus</th>
              <th className="py-3 px-4">Consequence</th>
              <th className="py-3 px-4">ClinVar</th>
              <th className="py-3 px-4">gnomAD AF</th>
              <th className="py-3 px-4">VEP Impact</th>
              <th className="py-3 px-4">Verification</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredVariants.map((vr) => {
              const v = vr.variant;
              const hasConflict = vr.conflicts && vr.conflicts.length > 0;

              return (
                <tr
                  key={v.key}
                  onClick={() => onSelectVariant(vr)}
                  className="hover:bg-slate-850/60 cursor-pointer transition-colors group"
                >
                  <td className="py-3.5 px-4">
                    <div className="font-mono font-medium text-slate-200 group-hover:text-cyan-300 transition-colors">
                      {v.key}
                    </div>
                    {v.rsid && (
                      <div className="text-[11px] font-mono text-slate-400">
                        {v.rsid}
                      </div>
                    )}
                  </td>

                  <td className="py-3.5 px-4">
                    <span className="font-bold text-white text-xs px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700/80">
                      {v.gene || "N/A"}
                    </span>
                  </td>

                  <td className="py-3.5 px-4 font-mono text-slate-400 text-[11px]">
                    chr{v.chrom}:{v.pos}
                  </td>

                  <td className="py-3.5 px-4 font-mono text-slate-300">
                    {v.consequence || "Not available"}
                  </td>

                  <td className="py-3.5 px-4">
                    {getSigBadge(v.clinvar_sig)}
                  </td>

                  <td className="py-3.5 px-4">
                    {getAfBadge(v.gnomad_af)}
                  </td>

                  <td className="py-3.5 px-4">
                    <span className="font-mono text-slate-300">
                      {vr.evidence.find((e) => e.source === "ensembl_vep")?.data?.impact || "MODERATE"}
                    </span>
                  </td>

                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
                      <span className="font-mono text-xs text-cyan-300 font-medium">
                        {getVerificationStatus(vr)}
                      </span>
                    </div>
                    {hasConflict && (
                      <span className="text-[10px] text-amber-400 font-medium block">
                        ⚠ Conflict
                      </span>
                    )}
                  </td>

                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectVariant(vr);
                      }}
                      className="px-2.5 py-1 rounded bg-slate-800 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 border border-slate-700 hover:border-cyan-500/30 text-xs font-semibold transition-all inline-flex items-center gap-1 cursor-pointer"
                    >
                      <span>Inspect</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filteredVariants.length === 0 && (
          <div className="p-8 text-center text-slate-400 text-xs">
            No variants match the current search or filter query.
          </div>
        )}
      </div>
    </div>
  );
};
