import React from "react";
import {
  CheckCircle2,
  CircleDashed,
  Dna,
  FileText,
  Loader2,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

export type PipelineStep =
  | "vcf_parsing"
  | "variant_identification"
  | "research_agent"
  | "verification_agent"
  | "report_agent"
  | "complete";

interface WorkflowProgressProps {
  currentStep: PipelineStep;
  error?: string | null;
}

export const WorkflowProgress: React.FC<WorkflowProgressProps> = ({
  currentStep,
  error,
}) => {
  const steps: {
    id: PipelineStep;
    title: string;
    description: string;
    icon: React.ReactNode;
  }[] = [
    {
      id: "vcf_parsing",
      title: "Step 1: VCF Parsing",
      description: "Decompressing and validating genomic VCF syntax & INFO tags.",
      icon: <Dna className="w-5 h-5" />,
    },
    {
      id: "variant_identification",
      title: "Step 2: Variant Identification",
      description: "Extracting normalized chromosome coordinates, alleles, and identifiers.",
      icon: <Sparkles className="w-5 h-5" />,
    },
    {
      id: "research_agent",
      title: "Step 3: Research Agent",
      description: "Retrieving genomic evidence from ClinVar, gnomAD, and Ensembl VEP...",
      icon: <CircleDashed className="w-5 h-5" />,
    },
    {
      id: "verification_agent",
      title: "Step 4: Verification Agent",
      description: "Checking evidence against claims and performing hallucination audit...",
      icon: <ShieldCheck className="w-5 h-5" />,
    },
    {
      id: "report_agent",
      title: "Step 5: Report Agent",
      description: "Detecting scientific conflicts and compiling traceable report...",
      icon: <FileText className="w-5 h-5" />,
    },
  ];

  const getStepIndex = (step: PipelineStep): number => {
    switch (step) {
      case "vcf_parsing":
        return 0;
      case "variant_identification":
        return 1;
      case "research_agent":
        return 2;
      case "verification_agent":
        return 3;
      case "report_agent":
        return 4;
      case "complete":
        return 5;
      default:
        return 0;
    }
  };

  const currentIndex = getStepIndex(currentStep);

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 my-8">
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-cyan-500/30 shadow-2xl relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-800">
          <div>
            <span className="text-[11px] font-mono tracking-widest uppercase font-semibold text-cyan-400">
              Autonomous Pipeline
            </span>
            <h2 className="text-xl font-bold text-white flex items-center gap-2 mt-0.5">
              <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
              <span>ANALYSIS IN PROGRESS</span>
            </h2>
          </div>
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-cyan-300">
            Multi-Agent State
          </span>
        </div>

        {error ? (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
            <strong>Pipeline Error:</strong> {error}
          </div>
        ) : (
          <div className="space-y-4">
            {steps.map((s, idx) => {
              const isPast = idx < currentIndex;
              const isCurrent = idx === currentIndex;

              return (
                <div
                  key={s.id}
                  className={`flex items-start gap-4 p-3.5 rounded-xl border transition-all ${
                    isCurrent
                      ? "bg-cyan-950/30 border-cyan-500/40 shadow-md shadow-cyan-500/5"
                      : isPast
                      ? "bg-slate-900/40 border-slate-800 text-slate-300"
                      : "bg-slate-900/20 border-slate-800/40 opacity-50"
                  }`}
                >
                  <div className="pt-0.5">
                    {isPast ? (
                      <div className="w-7 h-7 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                        <CheckCircle2 className="w-4 h-4" />
                      </div>
                    ) : isCurrent ? (
                      <div className="w-7 h-7 rounded-full bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
                        <Loader2 className="w-4 h-4 animate-spin" />
                      </div>
                    ) : (
                      <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-500">
                        <span className="text-xs font-mono">{idx + 1}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h4
                        className={`text-sm font-semibold ${
                          isCurrent
                            ? "text-cyan-300"
                            : isPast
                            ? "text-white"
                            : "text-slate-400"
                        }`}
                      >
                        {s.title}
                      </h4>
                      <span className="text-[11px] font-mono">
                        {isPast ? (
                          <span className="text-emerald-400 font-medium">✓ Done</span>
                        ) : isCurrent ? (
                          <span className="text-cyan-400 font-medium animate-pulse">Running</span>
                        ) : (
                          <span className="text-slate-500">Queued</span>
                        )}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">{s.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
