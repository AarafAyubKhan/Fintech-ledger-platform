"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Database,
  Search,
  GitBranch,
  Building2,
  FileText,
  Scale,
  TrendingUp,
  ChevronRight,
  Zap,
  Globe,
  Hash,
  ExternalLink,
  Filter,
} from "lucide-react";

type EntityType =
  | "COMPANY"
  | "REGULATION"
  | "METRIC"
  | "INDUSTRY"
  | "PERSON"
  | "EVENT";

interface KGEntity {
  id: string;
  name: string;
  type: EntityType;
  properties: Record<string, string>;
  connections: number;
  documents: number;
}

interface KGRelationship {
  source: string;
  target: string;
  type: string;
}

const entityTypeConfig: Record<
  EntityType,
  { icon: typeof Building2; color: string; bg: string }
> = {
  COMPANY: {
    icon: Building2,
    color: "text-brand-400",
    bg: "bg-brand-500/10 border-brand-500/20",
  },
  REGULATION: {
    icon: Scale,
    color: "text-accent-amber",
    bg: "bg-accent-amber/10 border-accent-amber/20",
  },
  METRIC: {
    icon: TrendingUp,
    color: "text-accent-emerald",
    bg: "bg-accent-emerald/10 border-accent-emerald/20",
  },
  INDUSTRY: {
    icon: Globe,
    color: "text-accent-violet",
    bg: "bg-accent-violet/10 border-accent-violet/20",
  },
  PERSON: {
    icon: Zap,
    color: "text-accent-cyan",
    bg: "bg-accent-cyan/10 border-accent-cyan/20",
  },
  EVENT: {
    icon: Hash,
    color: "text-accent-rose",
    bg: "bg-accent-rose/10 border-accent-rose/20",
  },
};

// Sample data for demonstration
const sampleEntities: KGEntity[] = [
  {
    id: "1",
    name: "HDFC Bank",
    type: "COMPANY",
    properties: { sector: "Banking", exchange: "NSE", ticker: "HDFCBANK" },
    connections: 24,
    documents: 8,
  },
  {
    id: "2",
    name: "ICICI Bank",
    type: "COMPANY",
    properties: { sector: "Banking", exchange: "NSE", ticker: "ICICIBANK" },
    connections: 18,
    documents: 5,
  },
  {
    id: "3",
    name: "Basel III Norms",
    type: "REGULATION",
    properties: { issuer: "RBI", category: "Capital Adequacy" },
    connections: 12,
    documents: 3,
  },
  {
    id: "4",
    name: "Net Interest Margin",
    type: "METRIC",
    properties: { unit: "%", category: "Profitability" },
    connections: 15,
    documents: 6,
  },
  {
    id: "5",
    name: "Banking Sector",
    type: "INDUSTRY",
    properties: { market: "India", regulator: "RBI" },
    connections: 32,
    documents: 12,
  },
  {
    id: "6",
    name: "Digital Lending Guidelines",
    type: "REGULATION",
    properties: { issuer: "RBI", year: "2023" },
    connections: 8,
    documents: 2,
  },
  {
    id: "7",
    name: "Return on Equity",
    type: "METRIC",
    properties: { unit: "%", category: "Profitability" },
    connections: 20,
    documents: 9,
  },
  {
    id: "8",
    name: "Sashidhar Jagdishan",
    type: "PERSON",
    properties: { role: "CEO", company: "HDFC Bank" },
    connections: 5,
    documents: 3,
  },
];

const sampleRelationships: KGRelationship[] = [
  { source: "HDFC Bank", target: "Banking Sector", type: "BELONGS_TO" },
  { source: "ICICI Bank", target: "Banking Sector", type: "BELONGS_TO" },
  { source: "HDFC Bank", target: "Basel III Norms", type: "REGULATED_BY" },
  { source: "HDFC Bank", target: "Net Interest Margin", type: "HAS_METRIC" },
  { source: "HDFC Bank", target: "ICICI Bank", type: "COMPETES_WITH" },
  { source: "Digital Lending Guidelines", target: "Banking Sector", type: "IMPACTS" },
  { source: "Sashidhar Jagdishan", target: "HDFC Bank", type: "LEADS" },
];

const sampleDocuments = [
  { id: "1", title: "HDFC Bank Annual Report FY2024", type: "annual_report", chunks: 45, entities: 18, date: "2024-06-15" },
  { id: "2", title: "RBI Master Direction — Digital Lending", type: "regulatory", chunks: 28, entities: 12, date: "2023-09-02" },
  { id: "3", title: "ICICI Bank Q3 FY2025 Earnings Transcript", type: "earnings_transcript", chunks: 32, entities: 14, date: "2025-01-20" },
  { id: "4", title: "Indian Banking Sector Report — Credit Suisse", type: "research_report", chunks: 56, entities: 22, date: "2024-11-10" },
];

export default function KnowledgePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"entities" | "documents" | "graph">("entities");
  const [selectedEntity, setSelectedEntity] = useState<KGEntity | null>(null);
  const [filterType, setFilterType] = useState<EntityType | "ALL">("ALL");

  const filteredEntities = sampleEntities.filter((e) => {
    const matchesSearch =
      !searchQuery ||
      e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      Object.values(e.properties).some((v) =>
        v.toLowerCase().includes(searchQuery.toLowerCase())
      );
    const matchesType = filterType === "ALL" || e.type === filterType;
    return matchesSearch && matchesType;
  });

  const graphStats = {
    totalEntities: sampleEntities.length,
    totalRelationships: sampleRelationships.length,
    totalDocuments: sampleDocuments.length,
    entityTypes: Object.entries(
      sampleEntities.reduce((acc, e) => {
        acc[e.type] = (acc[e.type] || 0) + 1;
        return acc;
      }, {} as Record<string, number>)
    ),
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-gradient-to-br from-accent-violet to-accent-cyan">
          <Database className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Knowledge Base</h1>
          <p className="text-surface-400">
            Explore your financial knowledge graph, documents, and entity relationships
          </p>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Entities", value: graphStats.totalEntities, icon: GitBranch, color: "text-brand-400" },
          { label: "Relationships", value: graphStats.totalRelationships, icon: Zap, color: "text-accent-violet" },
          { label: "Documents", value: graphStats.totalDocuments, icon: FileText, color: "text-accent-emerald" },
          { label: "Entity Types", value: graphStats.entityTypes.length, icon: Hash, color: "text-accent-amber" },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="glass-card p-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <stat.icon className={`w-4 h-4 ${stat.color}`} />
              <span className="text-xs text-surface-500">{stat.label}</span>
            </div>
            <p className="text-2xl font-bold font-mono">{stat.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 rounded-lg bg-surface-800/50 w-fit">
        {(["entities", "documents", "graph"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors capitalize ${
              activeTab === tab
                ? "bg-brand-500/20 text-brand-400"
                : "text-surface-400 hover:text-surface-200"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Search + Filter */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search entities, documents, or relationships..."
            className="w-full pl-11 pr-4 py-3 rounded-lg bg-surface-800 border border-surface-700 text-surface-100 placeholder-surface-500 focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 transition-colors"
          />
        </div>
        {activeTab === "entities" && (
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as EntityType | "ALL")}
              className="pl-9 pr-8 py-3 rounded-lg bg-surface-800 border border-surface-700 text-surface-200 appearance-none cursor-pointer focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 transition-colors"
            >
              <option value="ALL">All Types</option>
              <option value="COMPANY">Companies</option>
              <option value="REGULATION">Regulations</option>
              <option value="METRIC">Metrics</option>
              <option value="INDUSTRY">Industries</option>
              <option value="PERSON">People</option>
              <option value="EVENT">Events</option>
            </select>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-4">
          <AnimatePresence mode="wait">
            {activeTab === "entities" && (
              <motion.div
                key="entities"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="space-y-3"
              >
                {filteredEntities.map((entity, i) => {
                  const config = entityTypeConfig[entity.type];
                  const Icon = config.icon;
                  return (
                    <motion.div
                      key={entity.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      onClick={() => setSelectedEntity(entity)}
                      className={`glass-card-hover p-4 cursor-pointer ${
                        selectedEntity?.id === entity.id
                          ? "!border-brand-500/40 ring-1 ring-brand-500/20"
                          : ""
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-lg border ${config.bg}`}>
                          <Icon className={`w-4 h-4 ${config.color}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-surface-200">
                              {entity.name}
                            </h3>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${config.bg} ${config.color}`}>
                              {entity.type}
                            </span>
                          </div>
                          <div className="flex gap-4 mt-1.5 text-xs text-surface-500">
                            <span className="flex items-center gap-1">
                              <GitBranch className="w-3 h-3" />
                              {entity.connections} connections
                            </span>
                            <span className="flex items-center gap-1">
                              <FileText className="w-3 h-3" />
                              {entity.documents} documents
                            </span>
                          </div>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {Object.entries(entity.properties).map(([key, val]) => (
                              <span
                                key={key}
                                className="text-[11px] px-2 py-0.5 rounded-full bg-surface-800 text-surface-400 border border-surface-700"
                              >
                                {key}: {val}
                              </span>
                            ))}
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-surface-600 flex-shrink-0 mt-1" />
                      </div>
                    </motion.div>
                  );
                })}
              </motion.div>
            )}

            {activeTab === "documents" && (
              <motion.div
                key="documents"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="space-y-3"
              >
                {sampleDocuments.map((doc, i) => (
                  <motion.div
                    key={doc.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="glass-card-hover p-4"
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-brand-500/10 border border-brand-500/20">
                        <FileText className="w-4 h-4 text-brand-400" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-surface-200">{doc.title}</h3>
                        <div className="flex gap-4 mt-1.5 text-xs text-surface-500">
                          <span>{doc.type.replace("_", " ")}</span>
                          <span>{doc.chunks} chunks</span>
                          <span>{doc.entities} entities</span>
                          <span>{doc.date}</span>
                        </div>
                      </div>
                      <button className="p-1.5 rounded-md hover:bg-surface-800 text-surface-500 hover:text-surface-200 transition-colors">
                        <ExternalLink className="w-4 h-4" />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}

            {activeTab === "graph" && (
              <motion.div
                key="graph"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
              >
                <div className="glass-card p-6">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <GitBranch className="w-5 h-5 text-brand-400" />
                    Relationship Graph
                  </h3>
                  {/* Visual Graph Representation */}
                  <div className="relative min-h-[400px] rounded-lg bg-surface-800/30 border border-surface-700/50 overflow-hidden">
                    {/* Central node */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-brand-500 to-accent-violet flex items-center justify-center shadow-lg shadow-brand-500/20">
                        <Building2 className="w-8 h-8 text-white" />
                      </div>
                      <p className="text-xs text-center mt-2 text-surface-300 font-medium">HDFC Bank</p>
                    </div>
                    {/* Satellite nodes */}
                    {[
                      { name: "ICICI Bank", angle: 0, type: "COMPANY" as EntityType, rel: "COMPETES_WITH" },
                      { name: "Banking Sector", angle: 60, type: "INDUSTRY" as EntityType, rel: "BELONGS_TO" },
                      { name: "Basel III", angle: 120, type: "REGULATION" as EntityType, rel: "REGULATED_BY" },
                      { name: "NIM", angle: 180, type: "METRIC" as EntityType, rel: "HAS_METRIC" },
                      { name: "ROE", angle: 240, type: "METRIC" as EntityType, rel: "HAS_METRIC" },
                      { name: "CEO", angle: 300, type: "PERSON" as EntityType, rel: "LEADS" },
                    ].map((node, i) => {
                      const radius = 140;
                      const x = Math.cos((node.angle * Math.PI) / 180) * radius;
                      const y = Math.sin((node.angle * Math.PI) / 180) * radius;
                      const config = entityTypeConfig[node.type];
                      const NodeIcon = config.icon;
                      return (
                        <motion.div
                          key={node.name}
                          initial={{ opacity: 0, scale: 0 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: 0.3 + i * 0.1 }}
                          className="absolute top-1/2 left-1/2"
                          style={{
                            transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`,
                          }}
                        >
                          <div className={`w-12 h-12 rounded-full border-2 ${config.bg} flex items-center justify-center`}>
                            <NodeIcon className={`w-5 h-5 ${config.color}`} />
                          </div>
                          <p className="text-[10px] text-center mt-1 text-surface-400 whitespace-nowrap">
                            {node.name}
                          </p>
                          <p className="text-[9px] text-center text-surface-600 whitespace-nowrap">
                            {node.rel}
                          </p>
                        </motion.div>
                      );
                    })}
                    {/* Connection lines via SVG */}
                    <svg className="absolute inset-0 w-full h-full pointer-events-none">
                      {[0, 60, 120, 180, 240, 300].map((angle, i) => {
                        const r = 140;
                        const cx = 50;
                        const cy = 50;
                        const x = cx + (Math.cos((angle * Math.PI) / 180) * r * 100) / 400;
                        const y = cy + (Math.sin((angle * Math.PI) / 180) * r * 100) / 400;
                        return (
                          <line
                            key={i}
                            x1={`${cx}%`}
                            y1={`${cy}%`}
                            x2={`${x}%`}
                            y2={`${y}%`}
                            stroke="rgba(59,130,246,0.15)"
                            strokeWidth="1"
                            strokeDasharray="4 4"
                          />
                        );
                      })}
                    </svg>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Entity Detail Panel */}
          {selectedEntity ? (
            <motion.div
              key={selectedEntity.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card p-5"
            >
              <div className="flex items-center gap-3 mb-4">
                {(() => {
                  const config = entityTypeConfig[selectedEntity.type];
                  const Icon = config.icon;
                  return (
                    <div className={`p-2.5 rounded-lg border ${config.bg}`}>
                      <Icon className={`w-5 h-5 ${config.color}`} />
                    </div>
                  );
                })()}
                <div>
                  <h3 className="font-bold text-surface-100">{selectedEntity.name}</h3>
                  <p className="text-xs text-surface-500">{selectedEntity.type}</p>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">
                    Properties
                  </h4>
                  {Object.entries(selectedEntity.properties).map(([key, val]) => (
                    <div key={key} className="flex justify-between py-1.5 border-b border-surface-800">
                      <span className="text-xs text-surface-500">{key}</span>
                      <span className="text-xs text-surface-200 font-medium">{val}</span>
                    </div>
                  ))}
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">
                    Connections
                  </h4>
                  <div className="space-y-1.5">
                    {sampleRelationships
                      .filter(
                        (r) =>
                          r.source === selectedEntity.name ||
                          r.target === selectedEntity.name
                      )
                      .map((rel, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-2 text-xs p-2 rounded-md bg-surface-800/50"
                        >
                          <span className="text-surface-300">
                            {rel.source === selectedEntity.name ? rel.target : rel.source}
                          </span>
                          <span className="px-1.5 py-0.5 rounded-full bg-surface-700 text-surface-500 text-[10px]">
                            {rel.type}
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </motion.div>
          ) : (
            <div className="glass-card p-6 text-center">
              <Database className="w-8 h-8 text-surface-600 mx-auto mb-3" />
              <p className="text-sm text-surface-500">
                Select an entity to view its details and connections
              </p>
            </div>
          )}

          {/* Entity Type Distribution */}
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-surface-300 mb-3">
              Entity Types
            </h3>
            <div className="space-y-2">
              {graphStats.entityTypes.map(([type, count]) => {
                const config = entityTypeConfig[type as EntityType];
                const Icon = config?.icon || Hash;
                const percentage = Math.round((count / graphStats.totalEntities) * 100);
                return (
                  <div key={type} className="flex items-center gap-2">
                    <Icon className={`w-3.5 h-3.5 ${config?.color || "text-surface-500"}`} />
                    <span className="text-xs text-surface-400 flex-1">{type}</span>
                    <span className="text-xs font-mono text-surface-300">{count}</span>
                    <div className="w-16 h-1.5 rounded-full bg-surface-800 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percentage}%` }}
                        className={`h-full rounded-full ${
                          config?.color.replace("text-", "bg-") || "bg-surface-600"
                        }`}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
