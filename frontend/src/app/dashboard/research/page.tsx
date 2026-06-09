"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Search, Send, Loader2, FileText, ArrowRight, Sparkles } from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { researchApi, type ResearchResponse } from "@/lib/api";
import ReactMarkdown from "react-markdown";

export default function ResearchPage() {
  const token = useAuthStore((s) => s.token);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !token) return;
    setLoading(true);
    setError("");

    try {
      const response = await researchApi.analyze(
        { query, include_regulations: true, include_market_data: true },
        token
      );
      setResult(response);
    } catch (err: any) {
      setError(err.message || "Research query failed");
    } finally {
      setLoading(false);
    }
  };

  const sampleQueries = [
    "Analyze HDFC Bank's financial health considering recent RBI regulations",
    "Compare HDFC Bank and ICICI Bank on key financial metrics",
    "What is the impact of digital lending regulations on private banks?",
    "Summarize key findings from SBI's latest quarterly earnings",
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Research Workspace</h1>
        <p className="text-surface-400 mt-1">
          Ask complex financial questions and get citation-backed answers
        </p>
      </div>

      {/* Search Input */}
      <form onSubmit={handleSubmit} className="glass-card p-6">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a financial research question..."
            className="w-full pl-12 pr-24 py-4 rounded-xl bg-surface-800 border border-surface-700 text-surface-100 placeholder-surface-500 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition-all text-lg"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-5 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            <span className="hidden sm:inline">Analyze</span>
          </button>
        </div>

        {/* Sample queries */}
        {!result && (
          <div className="mt-4 space-y-2">
            <p className="text-xs text-surface-500">Try these queries:</p>
            <div className="flex flex-wrap gap-2">
              {sampleQueries.map((sq, i) => (
                <button
                  key={i}
                  onClick={() => setQuery(sq)}
                  className="px-3 py-1.5 text-xs rounded-full border border-surface-700 text-surface-400 hover:border-brand-500/30 hover:text-brand-400 hover:bg-brand-500/5 transition-all"
                >
                  {sq}
                </button>
              ))}
            </div>
          </div>
        )}
      </form>

      {/* Loading state */}
      {loading && (
        <div className="glass-card p-8 text-center">
          <Loader2 className="w-8 h-8 text-brand-400 animate-spin mx-auto mb-4" />
          <p className="text-surface-300 font-medium">Running multi-agent analysis...</p>
          <p className="text-surface-500 text-sm mt-1">
            Planner → Research → Regulatory → Market Intel → Analysis → Verification → Report
          </p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 rounded-lg bg-accent-rose/10 border border-accent-rose/20 text-accent-rose text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Execution Summary */}
          <div className="glass-card p-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Sparkles className="w-5 h-5 text-brand-400" />
              <span className="text-sm text-surface-300">
                Completed in {(result.latency_ms / 1000).toFixed(1)}s
              </span>
              <span className="text-surface-600">•</span>
              <span className="text-sm text-surface-300">
                {result.agent_steps.length} agents executed
              </span>
              <span className="text-surface-600">•</span>
              <span className="text-sm text-surface-300">
                {result.citations.length} citations
              </span>
            </div>
          </div>

          {/* Answer */}
          <div className="glass-card p-8">
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{result.answer}</ReactMarkdown>
            </div>
          </div>

          {/* Citations */}
          {result.citations.length > 0 && (
            <div className="glass-card p-6">
              <h3 className="text-sm font-semibold text-surface-300 mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4 text-brand-400" />
                Sources ({result.citations.length})
              </h3>
              <div className="space-y-2">
                {result.citations.map((c, i) => (
                  <div key={i} className="flex items-start gap-3 p-2 rounded-lg hover:bg-surface-800/30 transition-colors">
                    <span className="text-xs text-brand-400 font-mono mt-0.5">[{i + 1}]</span>
                    <div>
                      <p className="text-sm text-surface-200">{c.source}</p>
                      {c.page && <p className="text-xs text-surface-500">Page {c.page}</p>}
                    </div>
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
