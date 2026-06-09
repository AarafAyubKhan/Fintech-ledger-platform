"use client";

import { motion } from "framer-motion";
import { FileText, Download, Calendar, Building2, BarChart3 } from "lucide-react";

export default function ReportsPage() {
  const reports = [
    {
      id: "1",
      title: "HDFC Bank Equity Research Report",
      type: "portfolio_report",
      companies: ["HDFC Bank"],
      created_at: "2025-06-05",
      word_count: 3200,
      source_count: 12,
    },
    {
      id: "2",
      title: "ICICI vs Axis Bank Comparative Analysis",
      type: "comparative_analysis",
      companies: ["ICICI Bank", "Axis Bank"],
      created_at: "2025-06-04",
      word_count: 2800,
      source_count: 8,
    },
    {
      id: "3",
      title: "RBI Digital Lending Impact Assessment",
      type: "regulatory_impact",
      companies: ["Banking Sector"],
      created_at: "2025-06-03",
      word_count: 1900,
      source_count: 6,
    },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Reports</h1>
        <p className="text-surface-400 mt-1">
          View and export your generated financial reports
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reports.map((report, index) => (
          <motion.div
            key={report.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass-card-hover p-6 group"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="p-2 rounded-lg bg-brand-500/10">
                <BarChart3 className="w-5 h-5 text-brand-400" />
              </div>
              <span className="px-2 py-0.5 text-[10px] font-medium rounded-full border border-surface-700 text-surface-400">
                {report.type.replace("_", " ").toUpperCase()}
              </span>
            </div>

            <h3 className="font-semibold text-surface-200 group-hover:text-white transition-colors mb-2">
              {report.title}
            </h3>

            <div className="flex flex-wrap gap-2 mb-4">
              {report.companies.map((company) => (
                <span key={company} className="inline-flex items-center gap-1 text-xs text-surface-400">
                  <Building2 className="w-3 h-3" />
                  {company}
                </span>
              ))}
            </div>

            <div className="flex items-center justify-between text-xs text-surface-500">
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {report.created_at}
              </span>
              <span>{report.word_count.toLocaleString()} words • {report.source_count} sources</span>
            </div>

            <div className="flex gap-2 mt-4 pt-4 border-t border-surface-800">
              <button className="flex-1 py-2 rounded-lg border border-surface-700 hover:border-brand-500/30 hover:text-brand-400 text-surface-400 text-xs font-medium flex items-center justify-center gap-1.5 transition-colors">
                <Download className="w-3.5 h-3.5" />
                PDF
              </button>
              <button className="flex-1 py-2 rounded-lg border border-surface-700 hover:border-brand-500/30 hover:text-brand-400 text-surface-400 text-xs font-medium flex items-center justify-center gap-1.5 transition-colors">
                <Download className="w-3.5 h-3.5" />
                DOCX
              </button>
              <button className="flex-1 py-2 rounded-lg border border-surface-700 hover:border-brand-500/30 hover:text-brand-400 text-surface-400 text-xs font-medium flex items-center justify-center gap-1.5 transition-colors">
                <FileText className="w-3.5 h-3.5" />
                View
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
