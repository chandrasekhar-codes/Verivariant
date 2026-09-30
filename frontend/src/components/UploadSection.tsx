import React, { useRef, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  FileCode,
  FileUp,
  Sparkles,
  Trash2,
  Upload,
} from "lucide-react";
import { GenomeBuild } from "../types/genomics";

interface UploadSectionProps {
  onAnalyze: (file: File | null, isDemo: boolean, build: GenomeBuild) => void;
  isLoading: boolean;
}

export const UploadSection: React.FC<UploadSectionProps> = ({
  onAnalyze,
  isLoading,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [genomeBuild, setGenomeBuild] = useState<GenomeBuild>("GRCh38");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (file: File) => {
    setErrorMsg(null);
    const lowerName = file.name.toLowerCase();
    const isValidExt =
      lowerName.endsWith(".vcf") ||
      lowerName.endsWith(".vcf.gz") ||
      lowerName.endsWith(".bgz") ||
      (lowerName.endsWith(".gz") && lowerName.includes(".vcf"));
    if (!isValidExt) {
      setErrorMsg("Invalid file format. Please upload a .vcf or .vcf.gz file.");
      return;
    }
    setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setErrorMsg(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMsg("Please select a VCF file or click 'Load Demo Dataset'.");
      return;
    }
    onAnalyze(selectedFile, false, genomeBuild);
  };

  const handleDemoClick = () => {
    removeFile();
    onAnalyze(null, true, genomeBuild);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6">
      <div className="glass-panel p-6 sm:p-8 rounded-2xl shadow-xl relative border border-slate-800">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 mb-6 border-b border-slate-800 gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Upload className="w-5 h-5 text-cyan-400" />
              <span>Upload Genomic Dataset</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Select or drop an annotated human VCF file to launch autonomous multi-agent analysis.
            </p>
          </div>

          {/* Genome Build Picker */}
          <div className="flex items-center gap-2 bg-slate-900/90 p-1 rounded-lg border border-slate-800 text-xs">
            <span className="text-slate-400 px-2 font-mono text-[11px]">Build:</span>
            <button
              type="button"
              onClick={() => setGenomeBuild("GRCh38")}
              className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
                genomeBuild === "GRCh38"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              GRCh38 (hg38)
            </button>
            <button
              type="button"
              onClick={() => setGenomeBuild("GRCh37")}
              className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
                genomeBuild === "GRCh37"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              GRCh37 (hg19)
            </button>
          </div>
        </div>

        {/* Drag & Drop Area */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
            isDragging
              ? "border-cyan-400 bg-cyan-950/20 scale-[0.99]"
              : selectedFile
              ? "border-emerald-500/40 bg-emerald-950/10"
              : "border-slate-700/80 hover:border-cyan-500/50 bg-slate-900/50 hover:bg-slate-900/80"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".vcf,.vcf.gz,.gz,.bgz"
            onChange={handleFileChange}
            className="hidden"
          />

          {selectedFile ? (
            <div className="flex flex-col items-center">
              <div className="w-12 h-12 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center mb-3">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              </div>
              <p className="text-sm font-semibold text-white mb-1">
                {selectedFile.name}
              </p>
              <p className="text-xs text-slate-400 font-mono mb-3">
                {selectedFile.size >= 1024 * 1024
                  ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB`
                  : `${(selectedFile.size / 1024).toFixed(1)} KB`}{" "}
                · Ready to parse
              </p>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile();
                }}
                className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1 px-2.5 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Remove file</span>
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <div className="w-12 h-12 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-3">
                <FileUp className="w-6 h-6 text-cyan-400" />
              </div>
              <p className="text-sm font-semibold text-slate-200 mb-1">
                Drag and drop your VCF file here, or{" "}
                <span className="text-cyan-400 underline underline-offset-2">
                  browse files
                </span>
              </p>
              <p className="text-xs text-slate-400">
                Supported: <span className="font-mono text-slate-300">.vcf, .vcf.gz</span> · No file size limit
              </p>
            </div>
          )}
        </div>

        {/* Error message if any */}
        {errorMsg && (
          <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Action Controls & Demo Dataset Loader */}
        <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <button
            type="button"
            onClick={handleDemoClick}
            disabled={isLoading}
            className="w-full sm:w-auto px-4 py-2.5 rounded-lg bg-indigo-950/60 hover:bg-indigo-900/80 text-indigo-300 border border-indigo-500/30 hover:border-indigo-400/50 text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span>Load Demo Dataset (BRCA1, BRAF, CFTR...)</span>
          </button>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={!selectedFile || isLoading}
            className="w-full sm:w-auto px-6 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-500/20 hover:shadow-cyan-500/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <FileCode className="w-4 h-4 text-slate-950" />
            <span>{isLoading ? "Analyzing Variants..." : "Analyze VCF"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
