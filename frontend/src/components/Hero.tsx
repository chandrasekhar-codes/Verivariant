import React from "react";
import {
  ArrowRight,
  Bot,
  Database,
  Dna,
  FileCheck2,
  Play,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

interface HeroProps {
  onAnalyzeClick: () => void;
  onDemoClick: () => void;
  isLoading: boolean;
}

export const Hero: React.FC<HeroProps> = ({
  onAnalyzeClick,
  onDemoClick,
  isLoading,
}) => {
  return (
    <div className="relative overflow-hidden pt-8 pb-16 lg:pt-14 lg:pb-20">
      {/* Ambient background glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-cyan-600/20 via-indigo-600/15 to-teal-500/10 rounded-full blur-[100px] pointer-events-none -z-10" />

      <div className="max-w-5xl mx-auto text-center px-4 sm:px-6">
        {/* Hackathon Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/90 border border-slate-700/60 text-xs font-mono text-cyan-300 mb-6 shadow-inner backdrop-blur-md">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-spin-slow" />
          <span>TECHNORAZZ &apos;26 MedTech & HealthTech · Problem 4.4</span>
        </div>

        {/* Brand & Main Headline */}
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white mb-4">
          <span className="bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
            GENESIS
          </span>
          <span className="block text-2xl sm:text-3xl font-semibold bg-gradient-to-r from-cyan-400 via-teal-300 to-indigo-400 bg-clip-text text-transparent mt-2">
            Multi-Agent Genomic Intelligence
          </span>
        </h1>

        {/* Tagline & Subtitle */}
        <p className="text-lg sm:text-xl text-cyan-200/90 font-medium mb-3">
          &ldquo;From genomic variants to evidence-backed insights.&rdquo;
        </p>
        <p className="max-w-2xl mx-auto text-sm sm:text-base text-slate-400 mb-8 leading-relaxed">
          Analyze genomic variants with automated evidence retrieval from trusted databases, multi-agent AI reasoning, and strict claim-level verification without hallucination.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-14">
          <button
            onClick={onAnalyzeClick}
            className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-600 hover:from-cyan-400 hover:to-teal-500 text-slate-950 font-semibold text-sm shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30 transition-all flex items-center justify-center gap-2 group cursor-pointer"
          >
            <Dna className="w-4 h-4 text-slate-950 group-hover:rotate-45 transition-transform" />
            <span>Analyze VCF File</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </button>

          <button
            onClick={onDemoClick}
            disabled={isLoading}
            className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-cyan-300 border border-cyan-500/30 hover:border-cyan-400/60 font-medium text-sm shadow-md transition-all flex items-center justify-center gap-2.5 cursor-pointer disabled:opacity-50"
          >
            <Play className="w-4 h-4 text-cyan-400 fill-cyan-400" />
            <span>
              {isLoading ? "Running Demo Pipeline..." : "Try Live Demo (Judge Mode)"}
            </span>
          </button>
        </div>

        {/* Core Pillars / Architecture Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-left">
          <div className="glass-panel p-4 rounded-xl glass-panel-hover">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-3">
              <Database className="w-4 h-4 text-cyan-400" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">
              Multi-Source Evidence
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Concurrent retrieval across ClinVar, gnomAD v4, and Ensembl VEP with resilient offline caches.
            </p>
          </div>

          <div className="glass-panel p-4 rounded-xl glass-panel-hover">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-3">
              <Bot className="w-4 h-4 text-indigo-400" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">
              Research Agent
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Investigates molecular impacts, clinical classifications, and frequency context with zero hallucination.
            </p>
          </div>

          <div className="glass-panel p-4 rounded-xl glass-panel-hover">
            <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center mb-3">
              <ShieldCheck className="w-4 h-4 text-teal-400" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">
              Verification Agent
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Audits every generated claim against raw evidence payloads, assigning supported/unsupported verdicts.
            </p>
          </div>

          <div className="glass-panel p-4 rounded-xl glass-panel-hover">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mb-3">
              <FileCheck2 className="w-4 h-4 text-amber-400" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-1">
              Traceable Report
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Flags scientific evidence conflicts and provides clickable primary citations for clinical review.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
