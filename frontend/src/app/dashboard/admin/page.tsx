"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Shield,
  Users,
  BarChart3,
  Activity,
  FileText,
  Cpu,
  TrendingUp,
  TrendingDown,
  Search,
  ChevronDown,
  MoreHorizontal,
  Clock,
  AlertCircle,
  CheckCircle2,
  Filter,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";

// Sample data
const platformStats = [
  { label: "Total Users", value: "1,247", change: "+12%", trend: "up", icon: Users, color: "text-brand-400", bg: "from-brand-500/20 to-brand-500/5" },
  { label: "Documents", value: "3,891", change: "+8%", trend: "up", icon: FileText, color: "text-accent-emerald", bg: "from-accent-emerald/20 to-accent-emerald/5" },
  { label: "Reports Generated", value: "856", change: "+23%", trend: "up", icon: BarChart3, color: "text-accent-violet", bg: "from-accent-violet/20 to-accent-violet/5" },
  { label: "Agent Invocations", value: "12.4K", change: "-3%", trend: "down", icon: Cpu, color: "text-accent-amber", bg: "from-accent-amber/20 to-accent-amber/5" },
];

const users = [
  { id: "1", name: "Arjun Mehta", email: "arjun@example.com", role: "admin", status: "active", lastLogin: "2 hours ago", documents: 45, reports: 12 },
  { id: "2", name: "Priya Sharma", email: "priya@example.com", role: "analyst", status: "active", lastLogin: "5 hours ago", documents: 78, reports: 24 },
  { id: "3", name: "Rahul Verma", email: "rahul@example.com", role: "user", status: "active", lastLogin: "1 day ago", documents: 12, reports: 3 },
  { id: "4", name: "Sneha Patel", email: "sneha@example.com", role: "analyst", status: "active", lastLogin: "3 hours ago", documents: 56, reports: 18 },
  { id: "5", name: "Vikram Singh", email: "vikram@example.com", role: "user", status: "inactive", lastLogin: "2 weeks ago", documents: 5, reports: 1 },
  { id: "6", name: "Ananya Gupta", email: "ananya@example.com", role: "user", status: "active", lastLogin: "30 min ago", documents: 23, reports: 7 },
];

const auditLogs = [
  { id: "1", user: "Arjun Mehta", action: "user_role_changed", resource: "user:3", details: "Changed Rahul to analyst", timestamp: "2 min ago", level: "info" },
  { id: "2", user: "System", action: "agent_pipeline_error", resource: "conversation:42", details: "Verification agent timeout", timestamp: "15 min ago", level: "error" },
  { id: "3", user: "Priya Sharma", action: "document_uploaded", resource: "doc:189", details: "HDFC_Annual_Report_FY24.pdf", timestamp: "1 hour ago", level: "info" },
  { id: "4", user: "System", action: "report_generated", resource: "report:67", details: "ICICI Bank Equity Research", timestamp: "2 hours ago", level: "success" },
  { id: "5", user: "Sneha Patel", action: "user_login", resource: "user:4", details: "OAuth (Google)", timestamp: "3 hours ago", level: "info" },
  { id: "6", user: "System", action: "ingestion_completed", resource: "doc:188", details: "45 chunks, 12 entities extracted", timestamp: "4 hours ago", level: "success" },
];

const usageData = [
  { date: "Mon", users: 45, documents: 12, reports: 8 },
  { date: "Tue", users: 52, documents: 18, reports: 11 },
  { date: "Wed", users: 48, documents: 15, reports: 14 },
  { date: "Thu", users: 61, documents: 22, reports: 9 },
  { date: "Fri", users: 55, documents: 19, reports: 16 },
  { date: "Sat", users: 32, documents: 8, reports: 5 },
  { date: "Sun", users: 28, documents: 6, reports: 3 },
];

const roleColors: Record<string, string> = {
  admin: "bg-accent-rose/10 text-accent-rose border-accent-rose/20",
  analyst: "bg-accent-violet/10 text-accent-violet border-accent-violet/20",
  user: "bg-surface-700/50 text-surface-400 border-surface-600",
};

const logLevelColors: Record<string, string> = {
  info: "text-brand-400",
  error: "text-accent-rose",
  success: "text-accent-emerald",
  warning: "text-accent-amber",
};

export default function AdminPage() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"overview" | "users" | "audit">("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");

  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      !searchQuery ||
      u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === "all" || u.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const maxUsage = Math.max(...usageData.map((d) => d.users));

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-gradient-to-br from-accent-rose to-accent-violet">
          <Shield className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Admin Panel</h1>
          <p className="text-surface-400">
            Platform management, user administration, and system monitoring
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {platformStats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="glass-card p-5 relative overflow-hidden"
          >
            <div className={`absolute inset-0 bg-gradient-to-br ${stat.bg} pointer-events-none`} />
            <div className="relative">
              <div className="flex items-center justify-between mb-3">
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
                <span className={`flex items-center gap-1 text-xs font-medium ${
                  stat.trend === "up" ? "text-accent-emerald" : "text-accent-rose"
                }`}>
                  {stat.trend === "up" ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                  {stat.change}
                </span>
              </div>
              <p className="text-2xl font-bold font-mono">{stat.value}</p>
              <p className="text-xs text-surface-500 mt-1">{stat.label}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 rounded-lg bg-surface-800/50 w-fit">
        {(["overview", "users", "audit"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors capitalize ${
              activeTab === tab
                ? "bg-brand-500/20 text-brand-400"
                : "text-surface-400 hover:text-surface-200"
            }`}
          >
            {tab === "audit" ? "Audit Logs" : tab}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Usage Chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6"
          >
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-brand-400" />
              Weekly Usage
            </h3>
            <div className="flex items-end gap-3 h-48">
              {usageData.map((day, i) => (
                <div key={day.date} className="flex-1 flex flex-col items-center gap-2">
                  <div className="w-full flex flex-col gap-1 items-center">
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: `${(day.users / maxUsage) * 100}%` }}
                      transition={{ delay: i * 0.05, duration: 0.5 }}
                      className="w-full rounded-t-sm bg-gradient-to-t from-brand-500/80 to-brand-400/40"
                      style={{ minHeight: "4px" }}
                    />
                  </div>
                  <span className="text-[10px] text-surface-500">{day.date}</span>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-4 mt-4 pt-3 border-t border-surface-800">
              <span className="flex items-center gap-1.5 text-xs text-surface-400">
                <span className="w-2 h-2 rounded-full bg-brand-500" /> Active Users
              </span>
            </div>
          </motion.div>

          {/* Recent Audit Logs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-card p-6"
          >
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-accent-amber" />
              Recent Activity
            </h3>
            <div className="space-y-3 max-h-[280px] overflow-y-auto custom-scrollbar">
              {auditLogs.slice(0, 5).map((log) => (
                <div key={log.id} className="flex items-start gap-3 p-2 rounded-lg hover:bg-surface-800/30 transition-colors">
                  <div className={`mt-1 ${logLevelColors[log.level]}`}>
                    {log.level === "error" ? (
                      <AlertCircle className="w-4 h-4" />
                    ) : log.level === "success" ? (
                      <CheckCircle2 className="w-4 h-4" />
                    ) : (
                      <Activity className="w-4 h-4" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-surface-200">{log.details}</p>
                    <p className="text-xs text-surface-500 mt-0.5">
                      {log.user} · {log.timestamp}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Agent Performance */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-6 lg:col-span-2"
          >
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-accent-violet" />
              Agent Performance
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full fin-table">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th>Invocations</th>
                    <th>Avg Latency</th>
                    <th>Success Rate</th>
                    <th>Avg Tokens</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { name: "Planner", invocations: "2,340", latency: "1.2s", success: "99.2%", tokens: "820" },
                    { name: "Financial Research", invocations: "2,180", latency: "3.4s", success: "97.8%", tokens: "1,540" },
                    { name: "Regulatory", invocations: "1,890", latency: "2.8s", success: "98.1%", tokens: "1,320" },
                    { name: "Market Intel", invocations: "1,650", latency: "2.1s", success: "96.5%", tokens: "980" },
                    { name: "Analysis", invocations: "2,100", latency: "4.2s", success: "98.9%", tokens: "2,100" },
                    { name: "Verification", invocations: "2,050", latency: "2.5s", success: "99.5%", tokens: "1,180" },
                    { name: "Report Generation", invocations: "856", latency: "6.8s", success: "97.3%", tokens: "3,200" },
                  ].map((agent) => (
                    <tr key={agent.name}>
                      <td className="font-medium">{agent.name}</td>
                      <td className="font-mono">{agent.invocations}</td>
                      <td className="font-mono">{agent.latency}</td>
                      <td>
                        <span className={`font-mono ${
                          parseFloat(agent.success) >= 98
                            ? "text-accent-emerald"
                            : parseFloat(agent.success) >= 96
                            ? "text-accent-amber"
                            : "text-accent-rose"
                        }`}>
                          {agent.success}
                        </span>
                      </td>
                      <td className="font-mono">{agent.tokens}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </div>
      )}

      {/* Users Tab */}
      {activeTab === "users" && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6"
        >
          {/* Search & Filter */}
          <div className="flex gap-4 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search users..."
                className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-surface-800 border border-surface-700 text-surface-100 placeholder-surface-500 focus:border-brand-500 transition-colors text-sm"
              />
            </div>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" />
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="pl-9 pr-8 py-2.5 rounded-lg bg-surface-800 border border-surface-700 text-surface-200 text-sm appearance-none cursor-pointer focus:border-brand-500 transition-colors"
              >
                <option value="all">All Roles</option>
                <option value="admin">Admin</option>
                <option value="analyst">Analyst</option>
                <option value="user">User</option>
              </select>
            </div>
          </div>

          {/* Users Table */}
          <div className="overflow-x-auto">
            <table className="w-full fin-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Last Login</th>
                  <th>Documents</th>
                  <th>Reports</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500/80 to-accent-violet/80 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                          {u.name.charAt(0)}
                        </div>
                        <div>
                          <p className="font-medium text-surface-200">{u.name}</p>
                          <p className="text-xs text-surface-500">{u.email}</p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full border ${roleColors[u.role]} uppercase`}>
                        {u.role}
                      </span>
                    </td>
                    <td>
                      <span className={`flex items-center gap-1.5 text-xs ${
                        u.status === "active" ? "text-accent-emerald" : "text-surface-500"
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${
                          u.status === "active" ? "bg-accent-emerald" : "bg-surface-600"
                        }`} />
                        {u.status}
                      </span>
                    </td>
                    <td className="text-xs text-surface-400">{u.lastLogin}</td>
                    <td className="font-mono">{u.documents}</td>
                    <td className="font-mono">{u.reports}</td>
                    <td>
                      <button className="p-1 rounded-md hover:bg-surface-800 text-surface-500 hover:text-surface-200 transition-colors">
                        <MoreHorizontal className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-4 pt-4 border-t border-surface-800">
            <p className="text-xs text-surface-500">
              Showing {filteredUsers.length} of {users.length} users
            </p>
          </div>
        </motion.div>
      )}

      {/* Audit Logs Tab */}
      {activeTab === "audit" && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6"
        >
          <div className="space-y-3">
            {auditLogs.map((log, i) => (
              <motion.div
                key={log.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-start gap-4 p-4 rounded-lg bg-surface-800/30 border border-surface-700/50 hover:border-surface-600/50 transition-colors"
              >
                <div className={`mt-0.5 ${logLevelColors[log.level]}`}>
                  {log.level === "error" ? (
                    <AlertCircle className="w-5 h-5" />
                  ) : log.level === "success" ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : (
                    <Activity className="w-5 h-5" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-surface-200">{log.action.replace(/_/g, " ")}</span>
                    <span className="px-1.5 py-0.5 text-[10px] rounded bg-surface-800 text-surface-500 font-mono">
                      {log.resource}
                    </span>
                  </div>
                  <p className="text-sm text-surface-400 mt-0.5">{log.details}</p>
                  <p className="text-xs text-surface-600 mt-1">
                    {log.user} · {log.timestamp}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
