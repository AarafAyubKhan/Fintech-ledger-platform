/**
 * FinSight AI — API Client
 * Type-safe HTTP client for the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  token?: string;
}

class APIError extends Error {
  status: number;
  detail: string;

  constructor(status: number, message: string, detail: string) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = "GET", body, headers = {}, token } = options;

  const requestHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...headers,
  };

  if (token) {
    requestHeaders["Authorization"] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    method,
    headers: requestHeaders,
    credentials: "include",
  };

  if (body && method !== "GET") {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${API_PREFIX}${endpoint}`, config);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new APIError(
      response.status,
      errorData.message || `HTTP ${response.status}`,
      errorData.detail || "An error occurred"
    );
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// ═══════════════════════════════════════════════════════
// Auth API
// ═══════════════════════════════════════════════════════

export const authApi = {
  signup: (data: { email: string; password: string; name: string }) =>
    request<{ access_token: string; refresh_token: string }>("/auth/signup", {
      method: "POST",
      body: data,
    }),

  login: (data: { email: string; password: string }) =>
    request<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST",
      body: data,
    }),

  refresh: (refreshToken: string) =>
    request<{ access_token: string; refresh_token: string }>("/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
    }),

  logout: () => request("/auth/logout", { method: "POST" }),

  getGoogleAuthUrl: () =>
    request<{ authorization_url: string }>("/auth/google"),
};

// ═══════════════════════════════════════════════════════
// User API
// ═══════════════════════════════════════════════════════

export const userApi = {
  getProfile: (token: string) =>
    request<UserProfile>("/users/me", { token }),

  updateProfile: (data: Partial<UserProfile>, token: string) =>
    request<UserProfile>("/users/me", {
      method: "PATCH",
      body: data,
      token,
    }),
};

// ═══════════════════════════════════════════════════════
// Documents API
// ═══════════════════════════════════════════════════════

export const documentsApi = {
  list: (params: { page?: number; pageSize?: number } = {}, token: string) =>
    request<DocumentListResponse>(
      `/documents/?page=${params.page || 1}&page_size=${params.pageSize || 20}`,
      { token }
    ),

  get: (id: string, token: string) =>
    request<Document>(`/documents/${id}`, { token }),

  upload: async (file: File, metadata: DocumentUploadMeta, token: string) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", metadata.title);
    if (metadata.description) formData.append("description", metadata.description);
    if (metadata.document_type) formData.append("document_type", metadata.document_type);
    if (metadata.company_id) formData.append("company_id", metadata.company_id);

    const response = await fetch(
      `${API_BASE}${API_PREFIX}/documents/upload`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
        credentials: "include",
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new APIError(response.status, error.message || "Upload failed", error.detail || "");
    }

    return response.json() as Promise<Document>;
  },

  delete: (id: string, token: string) =>
    request(`/documents/${id}`, { method: "DELETE", token }),

  triggerIngestion: (id: string, token: string) =>
    request<Document>(`/documents/${id}/ingest`, { method: "POST", token }),
};

// ═══════════════════════════════════════════════════════
// Research API
// ═══════════════════════════════════════════════════════

export const researchApi = {
  analyze: (data: ResearchRequest, token: string) =>
    request<ResearchResponse>("/research/analyze", {
      method: "POST",
      body: data,
      token,
    }),

  compare: (data: CompareRequest, token: string) =>
    request<ResearchResponse>("/research/compare", {
      method: "POST",
      body: data,
      token,
    }),

  portfolioReport: (data: PortfolioReportRequest, token: string) =>
    request<ResearchResponse>("/research/portfolio-report", {
      method: "POST",
      body: data,
      token,
    }),
};

// ═══════════════════════════════════════════════════════
// Conversations API
// ═══════════════════════════════════════════════════════

export const conversationsApi = {
  list: (token: string) =>
    request<Conversation[]>("/conversations/", { token }),

  get: (id: string, token: string) =>
    request<ConversationDetail>(`/conversations/${id}`, { token }),

  create: (title: string, token: string) =>
    request<Conversation>("/conversations/", {
      method: "POST",
      body: { title },
      token,
    }),

  sendMessage: (conversationId: string, content: string, token: string) =>
    request<Message>(`/conversations/${conversationId}/message`, {
      method: "POST",
      body: { content },
      token,
    }),

  delete: (id: string, token: string) =>
    request(`/conversations/${id}`, { method: "DELETE", token }),
};

// ═══════════════════════════════════════════════════════
// Reports API
// ═══════════════════════════════════════════════════════

export const reportsApi = {
  list: (token: string) =>
    request<ReportListResponse>("/reports/", { token }),

  get: (id: string, token: string) =>
    request<Report>(`/reports/${id}`, { token }),

  exportPdf: async (id: string, token: string) => {
    const response = await fetch(
      `${API_BASE}${API_PREFIX}/reports/${id}/export/pdf`,
      {
        headers: { Authorization: `Bearer ${token}` },
        credentials: "include",
      }
    );
    return response.blob();
  },

  exportDocx: async (id: string, token: string) => {
    const response = await fetch(
      `${API_BASE}${API_PREFIX}/reports/${id}/export/docx`,
      {
        headers: { Authorization: `Bearer ${token}` },
        credentials: "include",
      }
    );
    return response.blob();
  },
};

// ═══════════════════════════════════════════════════════
// Admin API
// ═══════════════════════════════════════════════════════

export const adminApi = {
  getStats: (token: string) =>
    request<AdminStats>("/admin/stats", { token }),

  getUsers: (token: string) =>
    request<UserProfile[]>("/admin/users", { token }),

  updateUserRole: (userId: string, role: string, token: string) =>
    request<UserProfile>(`/admin/users/${userId}/role`, {
      method: "PATCH",
      body: { role },
      token,
    }),

  getAuditLogs: (token: string) =>
    request<AuditLog[]>("/admin/audit-logs", { token }),
};

// ═══════════════════════════════════════════════════════
// Type Definitions
// ═══════════════════════════════════════════════════════

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: string;
  avatar_url: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Document {
  id: string;
  title: string;
  description: string | null;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  document_type: string;
  status: string;
  company_id: string | null;
  page_count: number | null;
  chunk_count: number | null;
  created_at: string;
}

export interface DocumentUploadMeta {
  title: string;
  description?: string;
  document_type?: string;
  company_id?: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
}

export interface Conversation {
  id: string;
  title: string;
  status: string;
  message_count: number;
  total_tokens: number;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  source: string;
  page: number | null;
  chunk_id: string | null;
  content_preview: string | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  agent_name: string | null;
  citations: Citation[] | null;
  execution_steps: AgentStep[] | null;
  latency_ms: number | null;
  created_at: string;
}

export interface ConversationDetail {
  conversation: Conversation;
  messages: Message[];
}

export interface AgentStep {
  agent_name: string;
  status: string;
  message: string;
  data: Record<string, unknown> | null;
  timestamp: string;
}

export interface ResearchRequest {
  query: string;
  companies?: string[];
  include_regulations?: boolean;
  include_market_data?: boolean;
}

export interface CompareRequest {
  companies: string[];
  metrics?: string[];
}

export interface PortfolioReportRequest {
  company_name: string;
  ticker?: string;
  include_charts?: boolean;
  include_risk_analysis?: boolean;
  include_regulatory_impact?: boolean;
}

export interface ResearchResponse {
  id: string;
  query: string;
  answer: string;
  citations: Citation[];
  agent_steps: AgentStep[];
  report_id: string | null;
  latency_ms: number;
}

export interface Report {
  id: string;
  title: string;
  report_type: string;
  executive_summary: string | null;
  key_findings: string | null;
  detailed_analysis: string | null;
  opportunities: string | null;
  risks: string | null;
  regulatory_impact: string | null;
  recommendation: string | null;
  companies: string[] | null;
  citations: Citation[] | null;
  financial_metrics: Record<string, unknown> | null;
  charts_data: Record<string, unknown> | null;
  word_count: number | null;
  source_count: number | null;
  created_at: string;
}

export interface ReportListResponse {
  reports: Report[];
  total: number;
}

export interface AdminStats {
  total_users: number;
  total_documents: number;
  total_conversations: number;
  total_reports: number;
  active_users_today: number;
  documents_processed: number;
  avg_response_time_ms: number;
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}
