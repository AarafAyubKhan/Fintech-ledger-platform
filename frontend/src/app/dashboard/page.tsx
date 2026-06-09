"use client";

import { motion } from "framer-motion";
import {
  BarChart3,
  FileText,
  MessageSquare,
  Upload,
  TrendingUp,
  TrendingDown,
  ArrowRight,
  Zap,
  Clock,
  Activity,
  Star,
} from "lucide-react";
import Link from "next/link";

const stats = [
  { label: "Documents Analyzed", value: "24", icon: FileText, change: "+3 this week", trend: "up" },
  { label: "Research Queries", value: "156", icon: MessageSquare, change: "+12 today", trend: "up" },
  { label: "Reports Generated", value: "8", icon: BarChart3, change: "+2 this week", trend: "up" },
  { label: "Avg Response Time", value: "3.2s", icon: Clock, change: "-0.5s improved", trend: "down" },
];

const recentActivities = [
  {
    type: "research",
    title: "Analyzed HDFC Bank Q3 FY2025 earnings",
    time: "2 hours ago",
    status: "completed",
    agents: ["planner", "research", "analysis", "report"],
  },
  {
    type: "document",
    title: "Ingested RBI Circular on Digital Lending",
    time: "4 hours ago",
    status: "completed",
    agents: ["ingestion"],
  },
  {
    type: "report",
    title: "Portfolio Report: ICICI Bank vs Axis Bank",
    time: "1 day ago",
    status: "completed",
    agents: ["planner", "research", "regulatory", "analysis", "verification", "report"],
  },
  {
    type: "research",
    title: "Impact analysis of RBI rate decision on banking sector",
    time: "2 days ago",
    status: "completed",
    agents: ["planner", "regulatory", "market_intel", "analysis"],
  },
];

const quickActions = [
  {
    title: "Portfolio Report",
    description: "Generate a complete equity research report",
    href: "/dashboard/portfolio",
    icon: Star,
    color: "from-accent-amber to-accent-rose",
  },
  {
    title: "New Research",
    description: "Ask a financial research question",
    href: "/dashboard/research",
    icon: Zap,
    color: "from-brand-500 to-accent-violet",
  },
  {
    title: "Upload Document",
    description: "Add annual reports, circulars, or transcripts",
    href: "/dashboard/documents",
    icon: Upload,
    color: "from-accent-emerald to-accent-cyan",
  },
];

export default function DashboardPage() {
  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-surface-400 mt-1">
          Welcome back. Here&apos;s your financial intelligence overview.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass-card p-5 group hover:border-brand-500/20 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-surface-400">{stat.label}</p>
                <p className="text-3xl font-bold font-mono mt-1">{stat.value}</p>
              </div>
              <div className="p-2 rounded-lg bg-surface-800 group-hover:bg-brand-500/10 transition-colors">
                <stat.icon className="w-5 h-5 text-surface-400 group-hover:text-brand-400 transition-colors" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-3">
              {stat.trend === "up" ? (
                <TrendingUp className="w-3.5 h-3.5 text-accent-emerald" />
              ) : (
                <TrendingDown className="w-3.5 h-3.5 text-accent-emerald" />
              )}
              <span className="text-xs text-accent-emerald">{stat.change}</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickActions.map((action, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + index * 0.1 }}
            >
              <Link
                href={action.href}
                className="glass-card-hover p-5 flex items-start gap-4 group block"
              >
                <div
                  className={`p-2.5 rounded-xl bg-gradient-to-br ${action.color} group-hover:scale-110 transition-transform`}
                >
                  <action.icon className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-surface-200 group-hover:text-white transition-colors">
                    {action.title}
                  </h3>
                  <p className="text-sm text-surface-500 mt-0.5">{action.description}</p>
                </div>
                <ArrowRight className="w-4 h-4 text-surface-600 group-hover:text-brand-400 group-hover:translate-x-1 transition-all mt-1" />
              </Link>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recent Activity</h2>
          <Link href="/dashboard/research" className="text-sm text-brand-400 hover:text-brand-300 flex items-center gap-1">
            View all <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="glass-card divide-y divide-surface-800">
          {recentActivities.map((activity, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 + index * 0.1 }}
              className="p-4 flex items-center gap-4 hover:bg-surface-800/30 transition-colors"
            >
              <div
                className={`p-2 rounded-lg ${
                  activity.type === "research"
                    ? "bg-brand-500/10 text-brand-400"
                    : activity.type === "document"
                    ? "bg-accent-emerald/10 text-accent-emerald"
                    : "bg-accent-violet/10 text-accent-violet"
                }`}
              >
                {activity.type === "research" ? (
                  <MessageSquare className="w-4 h-4" />
                ) : activity.type === "document" ? (
                  <Upload className="w-4 h-4" />
                ) : (
                  <FileText className="w-4 h-4" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-surface-200 truncate">
                  {activity.title}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-surface-500">{activity.time}</span>
                  <span className="text-surface-700">•</span>
                  <div className="flex items-center gap-1">
                    {activity.agents.map((agent, i) => (
                      <span
                        key={i}
                        className="w-1.5 h-1.5 rounded-full bg-accent-emerald"
                        title={agent}
                      />
                    ))}
                    <span className="text-xs text-surface-500 ml-1">
                      {activity.agents.length} agents
                    </span>
                  </div>
                </div>
              </div>

              <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-accent-emerald/10 text-accent-emerald">
                {activity.status}
              </span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Agent Pipeline Status */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-brand-400" />
          <h2 className="text-lg font-semibold">Agent Pipeline Status</h2>
        </div>
        <div className="grid grid-cols-7 gap-3">
          {[
            { name: "Planner", status: "ready" },
            { name: "Research", status: "ready" },
            { name: "Regulatory", status: "ready" },
            { name: "Market Intel", status: "ready" },
            { name: "Analysis", status: "ready" },
            { name: "Verification", status: "ready" },
            { name: "Report Gen", status: "ready" },
          ].map((agent, i) => (
            <div
              key={i}
              className="text-center p-3 rounded-lg bg-surface-800/50 border border-surface-700/50"
            >
              <div className="agent-dot-active mx-auto mb-2" />
              <p className="text-xs text-surface-400">{agent.name}</p>
              <p className="text-[10px] text-accent-emerald mt-0.5">{agent.status}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
