import { useCallback, useState } from "react";
import { Header } from "./components/Header";
import { Hero } from "./components/Hero";
import { UploadSection } from "./components/UploadSection";
import { WorkflowProgress, PipelineStep } from "./components/WorkflowProgress";
import { VariantTable } from "./components/VariantTable";
import { VariantDetailModal } from "./components/VariantDetailModal";
import { ReportView } from "./components/ReportView";
import { AboutPage } from "./components/AboutPage";
import { analyzeVcf, runDemoAnalysis } from "./services/api";
import { GenomeBuild, Report, VariantReport } from "./types/genomics";

type AppTab = "dashboard" | "analysis" | "reports" | "about";

export default function App() {
  const [activeTab, setActiveTab] = useState<AppTab>("dashboard");
  const [report, setReport] = useState<Report | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pipelineStep, setPipelineStep] = useState<PipelineStep>("vcf_parsing");
  const [selectedVariant, setSelectedVariant] = useState<VariantReport | null>(null);

  // Simulate pipeline step progression during analysis
  const simulatePipeline = useCallback(() => {
    const steps: PipelineStep[] = [
      "vcf_parsing",
      "variant_identification",
      "research_agent",
      "verification_agent",
      "report_agent",
      "complete",
    ];
    let idx = 0;
    const interval = setInterval(() => {
      idx += 1;
      if (idx < steps.length) {
        setPipelineStep(steps[idx]);
      } else {
        clearInterval(interval);
      }
    }, 800);
    return () => clearInterval(interval);
  }, []);

  const handleAnalyze = async (
    file: File | null,
    isDemo: boolean,
    build: GenomeBuild
  ) => {
    setIsLoading(true);
    setError(null);
    setReport(null);
    setPipelineStep("vcf_parsing");
    setActiveTab("analysis");

    const clearSim = simulatePipeline();

    try {
      let result: Report;
      if (isDemo) {
        result = await runDemoAnalysis();
      } else {
        result = await analyzeVcf(file, false, build);
      }
      setPipelineStep("complete");
      setReport(result);
      // Brief delay so the user sees "complete" state before switching
      setTimeout(() => {
        setActiveTab("reports");
      }, 600);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis pipeline encountered an unexpected failure.");
      setPipelineStep("vcf_parsing");
    } finally {
      setIsLoading(false);
      clearSim();
    }
  };

  const handleDemoFromHero = () => {
    handleAnalyze(null, true, "GRCh38");
  };

  const handleTabChange = (tab: AppTab) => {
    setActiveTab(tab);
    if (tab !== "reports") {
      setSelectedVariant(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 bg-grid-pattern flex flex-col">
      <Header
        activeTab={activeTab}
        onTabChange={handleTabChange}
        hasReport={report !== null}
      />

      <main className="flex-1">
        {/* ---- DASHBOARD TAB ---- */}
        {activeTab === "dashboard" && (
          <>
            <Hero
              onAnalyzeClick={() => setActiveTab("analysis")}
              onDemoClick={handleDemoFromHero}
              isLoading={isLoading}
            />
          </>
        )}

        {/* ---- ANALYSIS TAB ---- */}
        {activeTab === "analysis" && (
          <div className="py-8">
            {!isLoading && !report && (
              <UploadSection onAnalyze={handleAnalyze} isLoading={isLoading} />
            )}
            {isLoading && (
              <WorkflowProgress currentStep={pipelineStep} error={error} />
            )}
            {error && !isLoading && (
              <div className="max-w-3xl mx-auto px-4 sm:px-6 mt-6">
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
                  <strong>Error:</strong> {error}
                  <button
                    onClick={() => {
                      setError(null);
                      setReport(null);
                    }}
                    className="ml-3 underline text-xs cursor-pointer"
                  >
                    Try Again
                  </button>
                </div>
              </div>
            )}
            {report && !isLoading && (
              <div className="max-w-6xl mx-auto px-4 sm:px-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-white">
                      Variant Results Dashboard
                    </h2>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {report.total_variants} variants parsed ·{" "}
                      {report.total_claims} claims generated ·{" "}
                      {report.supported_claims} verified
                    </p>
                  </div>
                  <button
                    onClick={() => setActiveTab("reports")}
                    className="px-4 py-2 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/30 text-xs font-semibold transition-all cursor-pointer"
                  >
                    View Full Report →
                  </button>
                </div>
                <VariantTable
                  variants={report.variants}
                  onSelectVariant={setSelectedVariant}
                  isDemo={report.is_demo}
                />
              </div>
            )}
          </div>
        )}

        {/* ---- REPORTS TAB ---- */}
        {activeTab === "reports" && (
          <>
            {report ? (
              <ReportView
                report={report}
                onInspectVariant={setSelectedVariant}
              />
            ) : (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-4">
                  <span className="text-3xl">📋</span>
                </div>
                <h3 className="text-lg font-bold text-white mb-2">
                  No Report Generated Yet
                </h3>
                <p className="text-sm text-slate-400 mb-6 max-w-sm">
                  Upload a VCF file or run the demo to generate a multi-agent
                  genomic analysis report.
                </p>
                <button
                  onClick={handleDemoFromHero}
                  disabled={isLoading}
                  className="px-5 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm shadow-md cursor-pointer disabled:opacity-50"
                >
                  {isLoading ? "Running..." : "Run Demo Analysis"}
                </button>
              </div>
            )}
          </>
        )}

        {/* ---- ABOUT TAB ---- */}
        {activeTab === "about" && <AboutPage />}
      </main>

      {/* Variant Detail Modal */}
      <VariantDetailModal
        variantReport={selectedVariant}
        onClose={() => setSelectedVariant(null)}
        isDemo={report?.is_demo}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950/80 py-4 px-4 text-center text-[11px] text-slate-500 no-print">
        <span className="font-semibold text-slate-400">GENESIS</span> · Team 63
        · TECHNORAZZ 2026 · Multi-Agent Genomic Intelligence ·{" "}
        <span className="text-amber-400/70">
          Research/demo prototype only — not for clinical diagnosis or treatment.
        </span>
      </footer>
    </div>
  );
}
