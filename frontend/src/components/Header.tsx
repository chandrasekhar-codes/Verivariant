import React, { useEffect, useState } from "react";
import {
  Activity,
  Dna,
  ShieldAlert,
  Info,
  Layers,
  FileText,
} from "lucide-react";
import { getSourcesStatus } from "../services/api";

interface HeaderProps {
  activeTab: "dashboard" | "analysis" | "reports" | "about";
  onTabChange: (tab: "dashboard" | "analysis" | "reports" | "about") => void;
  hasReport: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  hasReport,
}) => {
  const [isLive, setIsLive] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;
    getSourcesStatus()
      .then(() => {
        if (mounted) {
          setIsLive(true);
        }
      })
      .catch(() => {
        if (mounted) setIsLive(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      {/* Top Medical Safety Disclaimer Banner */}
      <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-1.5 text-xs text-amber-300 flex items-center justify-between">
        <div className="flex items-center gap-2 max-w-5xl mx-auto w-full">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span className="truncate">
            <strong className="font-semibold">Research Prototype:</strong> GENESIS does not provide medical diagnosis or treatment recommendations. All findings require review by qualified geneticists.
          </span>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div
          onClick={() => onTabChange("dashboard")}
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 group-hover:shadow-cyan-500/40 transition-all">
            <Dna className="w-5 h-5 text-white animate-pulse-slow" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-wider text-white">
                GENESIS
              </span>
              <span className="px-1.5 py-0.5 text-[10px] uppercase font-mono tracking-wider font-semibold rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                v1.0 MVP
              </span>
            </div>
            <p className="text-[11px] text-slate-400 -mt-0.5 hidden sm:block">
              Multi-Agent Genomic Intelligence
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 sm:gap-2">
          <button
            onClick={() => onTabChange("dashboard")}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
              activeTab === "dashboard"
                ? "bg-slate-800 text-cyan-400 border border-slate-700 shadow-sm"
                : "text-slate-300 hover:text-white hover:bg-slate-900"
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Dashboard</span>
          </button>

          <button
            onClick={() => onTabChange("analysis")}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
              activeTab === "analysis"
                ? "bg-slate-800 text-cyan-400 border border-slate-700 shadow-sm"
                : "text-slate-300 hover:text-white hover:bg-slate-900"
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Analysis</span>
          </button>

          <button
            onClick={() => onTabChange("reports")}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
              activeTab === "reports"
                ? "bg-slate-800 text-cyan-400 border border-slate-700 shadow-sm"
                : "text-slate-300 hover:text-white hover:bg-slate-900"
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Reports</span>
            {hasReport && (
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            )}
          </button>

          <button
            onClick={() => onTabChange("about")}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
              activeTab === "about"
                ? "bg-slate-800 text-cyan-400 border border-slate-700 shadow-sm"
                : "text-slate-300 hover:text-white hover:bg-slate-900"
            }`}
          >
            <Info className="w-4 h-4" />
            <span className="hidden sm:inline">Problem 4.4</span>
            <span className="sm:hidden">About</span>
          </button>
        </nav>

        {/* Live Multi-Source Status Pill */}
        <div className="hidden lg:flex items-center gap-2 pl-4 border-l border-slate-800 text-xs">
          <div className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 px-2.5 py-1 rounded-full">
            <span
              className={`w-2 h-2 rounded-full ${
                isLive ? "bg-emerald-400" : "bg-amber-400"
              }`}
            />
            <span className="text-slate-300 font-mono text-[11px]">
              {isLive ? "API Engine Active" : "Curated Fallback"}
            </span>
          </div>

          <div className="flex items-center gap-1 text-[11px] font-mono text-slate-400">
            <span
              className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-300"
              title="ClinVar NCBI E-Utilities"
            >
              ClinVar
            </span>
            <span
              className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-indigo-300"
              title="Broad Institute gnomAD v4"
            >
              gnomAD
            </span>
            <span
              className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-teal-300"
              title="Ensembl Variant Effect Predictor"
            >
              VEP
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
