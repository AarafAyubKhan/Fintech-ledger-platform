"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import {
  Brain,
  FileSearch,
  Shield,
  BarChart3,
  FileText,
  Zap,
  ArrowRight,
  Sparkles,
  TrendingUp,
  Building2,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Multi-Agent Intelligence",
    description:
      "7 specialized AI agents work together — planner, researcher, regulatory analyst, market intelligence, financial analyst, verifier, and report generator.",
    color: "from-brand-500 to-accent-violet",
  },
  {
    icon: FileSearch,
    title: "Citation-Backed RAG",
    description:
      "Every claim is grounded in source documents with page-level citations. No hallucinations — only verified financial intelligence.",
    color: "from-accent-emerald to-accent-cyan",
  },
  {
    icon: Shield,
    title: "Verification Engine",
    description:
      "Dedicated verification agent cross-checks claims, validates citations, and rejects unsupported statements before any report is generated.",
    color: "from-accent-amber to-accent-rose",
  },
  {
    icon: BarChart3,
    title: "Financial Analytics",
    description:
      "Automated calculation of ROE, ROA, D/E ratio, profit margins, revenue growth, and 10+ financial metrics with trend analysis.",
    color: "from-accent-violet to-brand-500",
  },
  {
    icon: FileText,
    title: "Portfolio Mode",
    description:
      "Generate complete equity research reports with charts, financial ratios, SWOT analysis, and Buy/Hold/Sell recommendations.",
    color: "from-accent-cyan to-accent-emerald",
  },
  {
    icon: Zap,
    title: "Regulatory Intelligence",
    description:
      "Track RBI circulars, SEBI notifications, and banking regulations. Assess regulatory impact on companies and sectors.",
    color: "from-accent-rose to-accent-amber",
  },
];

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 },
};

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-surface-800/50 bg-surface-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-accent-violet flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold">FinSight AI</span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm text-surface-400 hover:text-surface-200 transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 hover:bg-brand-500 text-white transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-brand-500/30 bg-brand-500/10 text-brand-400 text-sm mb-8">
              <Zap className="w-3.5 h-3.5" />
              Powered by Multi-Agent AI Architecture
            </div>

            <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
              <span className="gradient-text">Financial Intelligence</span>
              <br />
              <span className="text-surface-200">Reimagined with AI</span>
            </h1>

            <p className="text-lg md:text-xl text-surface-400 max-w-3xl mx-auto mb-10 leading-relaxed">
              FinSight AI deploys 7 specialized agents to analyze companies, compare financials,
              assess regulatory impact, and generate citation-backed equity research reports —
              all in seconds.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/register"
                className="group px-8 py-3.5 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white font-semibold text-lg transition-all duration-300 flex items-center gap-2 shadow-lg shadow-brand-500/20"
              >
                Start Analyzing
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="/dashboard/portfolio"
                className="px-8 py-3.5 rounded-xl border border-surface-700 hover:border-surface-500 text-surface-300 hover:text-surface-100 font-medium text-lg transition-all duration-300"
              >
                Try Portfolio Mode
              </Link>
            </div>
          </motion.div>

          {/* Hero Visual */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="mt-16 relative"
          >
            <div className="glass-card p-1 max-w-5xl mx-auto">
              <div className="rounded-lg bg-surface-900 p-6">
                {/* Mock Dashboard Preview */}
                <div className="grid grid-cols-4 gap-4 mb-6">
                  {[
                    { label: "Revenue Growth", value: "+18.2%", trend: "up" },
                    { label: "ROE", value: "16.8%", trend: "up" },
                    { label: "D/E Ratio", value: "0.72", trend: "down" },
                    { label: "Net Margin", value: "22.4%", trend: "up" },
                  ].map((metric, i) => (
                    <div key={i} className="glass-card p-4">
                      <p className="text-xs text-surface-400 mb-1">{metric.label}</p>
                      <p className={`text-xl font-mono font-bold ${
                        metric.trend === "up" ? "metric-positive" : "metric-negative"
                      }`}>
                        {metric.value}
                      </p>
                      <div className="flex items-center gap-1 mt-1">
                        <TrendingUp className={`w-3 h-3 ${
                          metric.trend === "up" ? "text-accent-emerald" : "text-accent-rose rotate-180"
                        }`} />
                        <span className="text-[10px] text-surface-500">vs last year</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Agent Pipeline Visualization */}
                <div className="flex items-center justify-between px-4 py-3 rounded-lg bg-surface-800/50 border border-surface-700/50">
                  {["Planner", "Research", "Regulatory", "Analysis", "Verify", "Report"].map(
                    (agent, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className={`agent-dot ${i < 4 ? "agent-dot-active" : i === 4 ? "agent-dot-processing" : "agent-dot-idle"}`} />
                        <span className="text-xs text-surface-400">{agent}</span>
                        {i < 5 && (
                          <ArrowRight className="w-3 h-3 text-surface-600 mx-1" />
                        )}
                      </div>
                    )
                  )}
                </div>
              </div>
            </div>

            {/* Glow effect */}
            <div className="absolute -inset-4 bg-gradient-to-r from-brand-500/5 via-accent-violet/5 to-accent-cyan/5 rounded-2xl blur-3xl -z-10" />
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6" id="features">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Enterprise-Grade Financial Intelligence
            </h2>
            <p className="text-surface-400 max-w-2xl mx-auto">
              Built with production-ready RAG, multi-agent orchestration, and real-time
              verification — not a demo chatbot.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="glass-card-hover p-6 group"
              >
                <div
                  className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} p-2.5 mb-4 group-hover:scale-110 transition-transform duration-300`}
                >
                  <feature.icon className="w-full h-full text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-sm text-surface-400 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="glass-card p-12 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-brand-600/10 via-accent-violet/10 to-accent-cyan/10" />
            <div className="relative">
              <Building2 className="w-12 h-12 text-brand-400 mx-auto mb-6" />
              <h2 className="text-3xl font-bold mb-4">
                Ready to transform your financial research?
              </h2>
              <p className="text-surface-400 mb-8 max-w-xl mx-auto">
                Start generating citation-backed financial intelligence with the power of
                multi-agent AI. No hallucinations — only verified insights.
              </p>
              <Link
                href="/register"
                className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold transition-colors"
              >
                Get Started Free
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-surface-800 py-8 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-sm text-surface-500">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-brand-500" />
            <span>FinSight AI</span>
          </div>
          <p>Built with LangGraph, FastAPI, Next.js, and Qdrant</p>
        </div>
      </footer>
    </div>
  );
}
