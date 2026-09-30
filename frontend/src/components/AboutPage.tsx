import React from "react";
import {
  Bot,
  Database,
  FileCheck2,
  Layers,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";

export const AboutPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-10">
      {/* Problem Statement */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800">
        <span className="text-[11px] font-mono uppercase tracking-widest text-cyan-400 font-semibold">
          Technorazz &apos;26 · MedTech & HealthTech
        </span>
        <h1 className="text-2xl sm:text-3xl font-bold text-white mt-2 mb-4">
          Problem 4.4 — Multi-Agent Genomic Variant Analyzer
        </h1>
        <p className="text-sm text-slate-300 leading-relaxed">
          Build an AI-powered system that analyzes genomic variants using
          multi-agent architecture. The system retrieves evidence from trusted
          genomic databases, uses AI agents to research and verify findings, and
          generates traceable reports with claim-level evidence attribution.
        </p>
      </div>

      {/* Architecture */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800">
        <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          System Architecture
        </h2>

        <div className="space-y-4">
          {[
            {
              icon: <Zap className="w-4 h-4 text-cyan-400" />,
              label: "VCF Parser",
              desc: "Parses and normalizes VCF files using cyvcf2, extracting variant coordinates, alleles, rsIDs, and INFO annotations across GRCh37/GRCh38 builds.",
            },
            {
              icon: <Database className="w-4 h-4 text-indigo-400" />,
              label: "Evidence Retrieval Layer",
              desc: "Concurrent retrieval from NCBI ClinVar (E-Utilities API), Broad Institute gnomAD v4 (GraphQL), and Ensembl VEP (REST API) with resilient curated fallback.",
            },
            {
              icon: <Bot className="w-4 h-4 text-teal-400" />,
              label: "Agent 1 — Research Agent",
              desc: "Investigates each variant using retrieved multi-source evidence. Produces atomic, grounded claims with citations and URLs. Never hallucinates or invents evidence.",
            },
            {
              icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
              label: "Agent 2 — Verification Agent",
              desc: "Independently audits every Research Agent claim against raw database payloads. Assigns verdicts: SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, or UNCLEAR.",
            },
            {
              icon: <FileCheck2 className="w-4 h-4 text-amber-400" />,
              label: "Agent 3 — Report Agent",
              desc: "Compiles verified findings into a traceable report. Detects scientific discordance between ClinVar, gnomAD, and VEP. Applies medical safety disclaimers.",
            },
          ].map((step, i) => (
            <div
              key={i}
              className="flex items-start gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800"
            >
              <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                {step.icon}
              </div>
              <div>
                <h4 className="text-sm font-semibold text-white">{step.label}</h4>
                <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tech Stack */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800">
        <h2 className="text-lg font-bold text-white mb-5 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-cyan-400" />
          Technology Stack
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <h4 className="font-semibold text-cyan-300 mb-2">Frontend</h4>
            <ul className="space-y-1.5 text-slate-300">
              <li>• React 19 + TypeScript (strict mode)</li>
              <li>• Vite 6 build system</li>
              <li>• Tailwind CSS 3 (dark glassmorphism)</li>
              <li>• Lucide React icon library</li>
              <li>• Recharts (data visualization)</li>
            </ul>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <h4 className="font-semibold text-indigo-300 mb-2">Backend</h4>
            <ul className="space-y-1.5 text-slate-300">
              <li>• Python 3.11+ with type hints</li>
              <li>• FastAPI + Pydantic v2 validation</li>
              <li>• cyvcf2 VCF parser</li>
              <li>• httpx async HTTP client</li>
              <li>• uvicorn ASGI server</li>
            </ul>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <h4 className="font-semibold text-teal-300 mb-2">
              Genomic Data Sources
            </h4>
            <ul className="space-y-1.5 text-slate-300">
              <li>• NCBI ClinVar (E-Utilities API)</li>
              <li>• Broad Institute gnomAD v4 (GraphQL)</li>
              <li>• Ensembl Variant Effect Predictor (REST)</li>
            </ul>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <h4 className="font-semibold text-amber-300 mb-2">
              AI & Multi-Agent
            </h4>
            <ul className="space-y-1.5 text-slate-300">
              <li>• Deterministic grounded reasoning engine</li>
              <li>• Optional LLM API integration (OpenAI)</li>
              <li>• Research, Verification, and Report Agents</li>
              <li>• Strong anti-hallucination guardrails</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Team */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 text-center">
        <h2 className="text-lg font-bold text-white mb-3">Team 63 — GENESIS</h2>
        <p className="text-sm text-slate-400 mb-4">
          TECHNORAZZ 2026 — &ldquo;Hack the Gap&rdquo;
        </p>
        <p className="text-xs text-slate-500 italic leading-relaxed max-w-xl mx-auto">
          &ldquo;From genomic variants to evidence-backed insights.&rdquo;
        </p>
      </div>
    </div>
  );
};
