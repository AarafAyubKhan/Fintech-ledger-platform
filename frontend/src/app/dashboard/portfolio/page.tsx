"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Star,
  Search,
  Building2,
  BarChart3,
  Shield,
  TrendingUp,
  ArrowRight,
  Loader2,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Download,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { researchApi, type ResearchResponse, type AgentStep } from "@/lib/api";
import ReactMarkdown from "react-markdown";

const sampleCompanies = [
  "HDFC Bank",
  "ICICI Bank",
  "State Bank of India",
  "Infosys",
  "Reliance Industries",
  "TCS",
  "Axis Bank",
  "Kotak Mahindra Bank",
];

export default function PortfolioPage() {
  const token = useAuthStore((s) => s.token);
  const [companyName, setCompanyName] = useState("");
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [activeStep, setActiveStep] = useState<number>(-1);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!companyName.trim() || !token) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await researchApi.portfolioReport(
        {
          company_name: companyName,
          ticker: ticker || undefined,
          include_charts: true,
          include_risk_analysis: true,
          include_regulatory_impact: true,
        },
        token
      );
      setResult(response);
    } catch (err: any) {
      setError(err.message || "Failed to generate report");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-gradient-to-br from-accent-amber to-accent-rose">
          <Star className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Portfolio Mode</h1>
          <p className="text-surface-400">
            Generate complete equity research reports with AI-powered analysis
          </p>
        </div>
      </div>

      {/* Input Section */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold mb-4">Select a Company</h2>

        <div className="flex gap-4 mb-4">
          <div className="flex-1 relative">
            <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-500" />
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Enter company name (e.g., HDFC Bank)"
              className="w-full pl-11 pr-4 py-3 rounded-lg bg-surface-800 border border-surface-700 text-surface-100 placeholder-surface-500 focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 transition-colors text-lg"
            />
          </div>
          <div className="w-40">
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="Ticker (opt)"
              className="w-full px-4 py-3 rounded-lg bg-surface-800 border border-surface-700 text-surface-100 placeholder-surface-500 focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 transition-colors text-lg"
            />
          </div>
          <button
            onClick={handleGenerate}
            disabled={loading || !companyName.trim()}
            className="px-6 py-3 rounded-lg bg-gradient-to-r from-accent-amber to-accent-rose hover:from-accent-amber/90 hover:to-accent-rose/90 text-white font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                Generate Report
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>

        {/* Quick select */}
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-surface-500 py-1">Quick select:</span>
          {sampleCompanies.map((company) => (
            <button
              key={company}
              onClick={() => setCompanyName(company)}
              className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                companyName === company
                  ? "bg-brand-500/10 border-brand-500/30 text-brand-400"
                  : "border-surface-700 text-surface-400 hover:border-surface-500 hover:text-surface-200"
              }`}
            >
              {company}
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-lg bg-accent-rose/10 border border-accent-rose/20 text-accent-rose flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Agent Execution Progress */}
      {loading && (
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-surface-300 mb-4">Agent Pipeline</h3>
          <div className="space-y-3">
            {["Planner", "Financial Research", "Regulatory", "Market Intel", "Analysis", "Verification", "Report Generation"].map(
              (agent, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    i <= 3 ? "bg-accent-emerald animate-pulse" : "bg-surface-600"
                  }`} />
                  <span className={`text-sm ${
                    i <= 3 ? "text-surface-200" : "text-surface-500"
                  }`}>
                    {agent}
                  </span>
                  {i <= 3 && i < 3 && (
                    <CheckCircle2 className="w-4 h-4 text-accent-emerald ml-auto" />
                  )}
                  {i === 3 && (
                    <Loader2 className="w-4 h-4 text-accent-amber animate-spin ml-auto" />
                  )}
                </div>
              )
            )}
          </div>
        </div>
      )}

      {/* Report Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Report Header */}
          <div className="glass-card p-6">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-bold gradient-text">
                  Equity Research Report: {companyName}
                </h2>
                <p className="text-surface-400 mt-1">
                  Generated in {(result.latency_ms / 1000).toFixed(1)}s •{" "}
                  {result.citations.length} sources cited •{" "}
                  {result.agent_steps.length} agents used
                </p>
              </div>
              <div className="flex gap-2">
                <button className="px-4 py-2 rounded-lg border border-surface-700 hover:border-surface-500 text-surface-300 text-sm flex items-center gap-2 transition-colors">
                  <Download className="w-4 h-4" />
                  PDF
                </button>
                <button className="px-4 py-2 rounded-lg border border-surface-700 hover:border-surface-500 text-surface-300 text-sm flex items-center gap-2 transition-colors">
                  <Download className="w-4 h-4" />
                  DOCX
                </button>
              </div>
            </div>
          </div>

          {/* Agent Steps */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-semibold text-surface-300 mb-3">Execution Trace</h3>
            <div className="flex items-center gap-2 overflow-x-auto pb-2 custom-scrollbar">
              {result.agent_steps.map((step, i) => (
                <button
                  key={i}
                  onClick={() => setActiveStep(activeStep === i ? -1 : i)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap border transition-colors ${
                    step.status === "completed"
                      ? "border-accent-emerald/30 bg-accent-emerald/5 text-accent-emerald"
                      : step.status === "error"
                      ? "border-accent-rose/30 bg-accent-rose/5 text-accent-rose"
                      : "border-surface-700 text-surface-400"
                  } ${activeStep === i ? "ring-1 ring-brand-500" : ""}`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    step.status === "completed" ? "bg-accent-emerald" : "bg-accent-rose"
                  }`} />
                  {step.agent_name.replace("_", " ")}
                  {i < result.agent_steps.length - 1 && (
                    <ArrowRight className="w-3 h-3 text-surface-600" />
                  )}
                </button>
              ))}
            </div>
            <AnimatePresence>
              {activeStep >= 0 && result.agent_steps[activeStep] && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-3 p-3 rounded-lg bg-surface-800/50 text-sm text-surface-300"
                >
                  {result.agent_steps[activeStep].message}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Report Content */}
          <div className="glass-card p-8">
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{result.answer}</ReactMarkdown>
            </div>
          </div>

          {/* Citations */}
          {result.citations.length > 0 && (
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-brand-400" />
                Sources & Citations ({result.citations.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.citations.map((citation, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-lg bg-surface-800/50 border border-surface-700/50 hover:border-brand-500/20 transition-colors"
                  >
                    <p className="text-sm font-medium text-brand-400">
                      [{i + 1}] {citation.source}
                    </p>
                    {citation.page && (
                      <p className="text-xs text-surface-500 mt-0.5">Page {citation.page}</p>
                    )}
                    {citation.content_preview && (
                      <p className="text-xs text-surface-400 mt-1 line-clamp-2">
                        {citation.content_preview}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
