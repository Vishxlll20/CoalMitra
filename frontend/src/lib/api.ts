/** Typed API client for the FastAPI backend. All routes proxy through Vite. */

import type {
  Anomaly,
  AuthUser,
  ChatMessage,
  Coalfield,
  DashboardPayload,
  DemoAccount,
  Document,
  FieldExtraction,
  Health,
  MetricPoint,
  MetricSummary,
  PageResult,
  Report,
  TextEmission,
  Topic,
  TopicDocument,
  TopicDrift,
  UploadProgress,
  WordStat,
} from "../types";

const BASE = "/api";

async function raw<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: init?.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    credentials: "same-origin",
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail ?? j.message ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  health: () => raw<Health>("/health"),

  auth: {
    demoAccounts: () => raw<DemoAccount[]>("/auth/demo-accounts"),
    login: (email: string, password: string) =>
      raw<AuthUser>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
    register: (name: string, email: string, password: string) =>
      raw<AuthUser>("/auth/register", { method: "POST", body: JSON.stringify({ name, email, password }) }),
    me: () => raw<AuthUser | null>("/auth/me"),
    logout: () => raw<void>("/auth/logout", { method: "POST" }),
  },

  documents: {
    list: () => raw<Document[]>("/documents"),
    get: (id: string) => raw<Document>(`/documents/${id}`),
    status: (id: string) => raw<UploadProgress>(`/documents/${id}/status`),
    pages: (id: string) => raw<PageResult[]>(`/documents/${id}/pages`),
    fields: (id: string) => raw<FieldExtraction[]>(`/documents/${id}/fields`),
    correctField: (documentId: string, fieldId: string, value: string) =>
      raw<FieldExtraction>(`/documents/${documentId}/fields/${fieldId}`, {
        method: "PATCH",
        body: JSON.stringify({ value }),
      }),
    emissions: (id: string) => raw<TextEmission[]>(`/documents/${id}/emissions`),
    fileUrl: (id: string) => `${BASE}/documents/${id}/file`,
    upload: (files: File[]) => {
      const fd = new FormData();
      for (const f of files) fd.append("files", f);
      return raw<Document[]>("/documents/upload", { method: "POST", body: fd });
    },
    delete: (id: string) => raw<{ ok: boolean }>(`/documents/${id}`, { method: "DELETE" }),
    coalfields: () => raw<Coalfield[]>("/documents/coalfields"),
  },

  reports: {
    list: () => raw<Report[]>("/reports"),
    get: (id: string) => raw<Report>(`/reports/${id}`),
    generate: (documentId?: string) =>
      raw<Report>("/reports/generate", { method: "POST", body: JSON.stringify({ document_id: documentId }) }),
    exportUrl: (id: string) => `${BASE}/reports/${id}/export.pdf`,
  },

  insights: {
    wordcloud: () => raw<WordStat[]>("/insights/wordcloud"),
    topics: () => raw<Topic[]>("/insights/topics"),
    drift: () => raw<TopicDrift[]>("/insights/topic-drift"),
    topicDocuments: (id: string) => raw<TopicDocument[]>(`/insights/topics/${id}/documents`),
  },

  anomalies: {
    list: () => raw<Anomaly[]>(`/anomalies?status=open`),
    all: () => raw<Anomaly[]>(`/anomalies`),
    acknowledge: (id: string) => raw<Anomaly>(`/anomalies/${id}/ack`, { method: "POST" }),
  },

  chat: {
    sessions: () => raw<{ id: string; title: string; language: string }[]>("/chat/sessions"),
    create: (title?: string) =>
      raw<{ id: string; title: string; language: string }>("/chat/sessions", { method: "POST", body: JSON.stringify({ title }) }),
    messages: (sessionId: string) => raw<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`),
    query: (sessionId: string, text: string, language: string) =>
      raw<ChatMessage>(`/chat/sessions/${sessionId}/query`, {
        method: "POST",
        body: JSON.stringify({ text, language }),
      }),
    voice: (sessionId: string, audioBlob: Blob, language: string) => {
      const fd = new FormData();
      fd.append("audio", audioBlob, "query.wav");
      fd.append("language", language);
      return raw<ChatMessage>(`/chat/sessions/${sessionId}/voice`, { method: "POST", body: fd });
    },
  },

  metrics: {
    summary: () => raw<MetricSummary>("/metrics/summary"),
    trends: () => raw<MetricPoint[]>("/metrics/trends"),
  },

  dashboard: {
    role: (role: string) => raw<DashboardPayload>(`/dashboard/${role}`),
  },
};

export { BASE }; // for file URLs built outside api object