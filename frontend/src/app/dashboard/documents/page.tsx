"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Upload, FileText, Trash2, RefreshCw, Check, Clock, AlertCircle, Loader2 } from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { documentsApi, type Document } from "@/lib/api";

const statusConfig = {
  pending: { icon: Clock, color: "text-surface-400", bg: "bg-surface-400/10", label: "Pending" },
  processing: { icon: Loader2, color: "text-accent-amber", bg: "bg-accent-amber/10", label: "Processing", animate: true },
  completed: { icon: Check, color: "text-accent-emerald", bg: "bg-accent-emerald/10", label: "Completed" },
  failed: { icon: AlertCircle, color: "text-accent-rose", bg: "bg-accent-rose/10", label: "Failed" },
};

const docTypes = [
  { value: "annual_report", label: "Annual Report" },
  { value: "quarterly_report", label: "Quarterly Report" },
  { value: "earnings_transcript", label: "Earnings Transcript" },
  { value: "regulatory_circular", label: "Regulatory Circular" },
  { value: "research_report", label: "Research Report" },
  { value: "other", label: "Other" },
];

export default function DocumentsPage() {
  const token = useAuthStore((s) => s.token);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [title, setTitle] = useState("");
  const [docType, setDocType] = useState("other");

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      await handleUpload(files[0]);
    }
  }, [token, title, docType]);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      await handleUpload(files[0]);
    }
  };

  const handleUpload = async (file: File) => {
    if (!token) return;
    setUploading(true);
    try {
      const doc = await documentsApi.upload(
        file,
        { title: title || file.name, document_type: docType },
        token
      );
      setDocuments([doc, ...documents]);
      setTitle("");
    } catch (err: any) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
    }
  };

  const handleIngest = async (docId: string) => {
    if (!token) return;
    try {
      const updated = await documentsApi.triggerIngestion(docId, token);
      setDocuments(documents.map((d) => (d.id === docId ? updated : d)));
    } catch (err) {
      console.error("Ingestion failed:", err);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Documents</h1>
        <p className="text-surface-400 mt-1">
          Upload and manage financial documents for the RAG knowledge base
        </p>
      </div>

      {/* Upload Area */}
      <div className="glass-card p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Document title (optional)"
            className="px-4 py-2.5 rounded-lg bg-surface-800 border border-surface-700 text-surface-100 placeholder-surface-500 focus:border-brand-500 transition-colors"
          />
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="px-4 py-2.5 rounded-lg bg-surface-800 border border-surface-700 text-surface-100 focus:border-brand-500 transition-colors"
          >
            {docTypes.map((dt) => (
              <option key={dt.value} value={dt.value}>{dt.label}</option>
            ))}
          </select>
        </div>

        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-12 text-center transition-all ${
            dragOver
              ? "border-brand-500 bg-brand-500/5"
              : "border-surface-700 hover:border-surface-500"
          }`}
        >
          {uploading ? (
            <Loader2 className="w-10 h-10 text-brand-400 animate-spin mx-auto mb-3" />
          ) : (
            <Upload className="w-10 h-10 text-surface-500 mx-auto mb-3" />
          )}
          <p className="text-surface-300 font-medium">
            {uploading ? "Uploading..." : "Drop files here or click to upload"}
          </p>
          <p className="text-sm text-surface-500 mt-1">
            Supports PDF, DOCX, TXT, HTML (max 50MB)
          </p>
          <input
            type="file"
            accept=".pdf,.docx,.txt,.html"
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="inline-block mt-4 px-6 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium cursor-pointer transition-colors"
          >
            Choose File
          </label>
        </div>
      </div>

      {/* Document List */}
      <div className="glass-card overflow-hidden">
        <table className="w-full fin-table">
          <thead>
            <tr>
              <th>Document</th>
              <th>Type</th>
              <th>Size</th>
              <th>Chunks</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center py-12 text-surface-500">
                  No documents uploaded yet. Upload your first document above.
                </td>
              </tr>
            )}
            {documents.map((doc, i) => {
              const status = statusConfig[doc.status as keyof typeof statusConfig] || statusConfig.pending;
              const StatusIcon = status.icon;
              return (
                <motion.tr
                  key={doc.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <td>
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-surface-500" />
                      <div>
                        <p className="font-medium text-surface-200">{doc.title}</p>
                        <p className="text-xs text-surface-500">{doc.file_name}</p>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className="px-2 py-0.5 text-xs rounded-full border border-surface-700 text-surface-400">
                      {doc.document_type.replace("_", " ")}
                    </span>
                  </td>
                  <td className="font-mono text-xs">{formatFileSize(doc.file_size_bytes)}</td>
                  <td className="font-mono text-xs">{doc.chunk_count ?? "—"}</td>
                  <td>
                    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs rounded-full ${status.bg} ${status.color}`}>
                      <StatusIcon className={`w-3 h-3 ${status.animate ? "animate-spin" : ""}`} />
                      {status.label}
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      {doc.status === "pending" && (
                        <button
                          onClick={() => handleIngest(doc.id)}
                          className="p-1.5 rounded-md hover:bg-surface-700 text-brand-400 transition-colors"
                          title="Process document"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        className="p-1.5 rounded-md hover:bg-surface-700 text-accent-rose transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
