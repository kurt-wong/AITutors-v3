/** Typed API client — 只做 HTTP 调用，不含业务逻辑。 */

import type {
  AdminStats,
  CandidateDetail,
  DocumentDetail,
  DocumentListResponse,
  SourceLinesResponse,
  SourceQualityReport,
  TaskListResponse,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

// ------------------------------------------------------------------ Documents
export function listDocuments(params?: {
  status?: string;
  page?: number;
  limit?: number;
}): Promise<DocumentListResponse> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.page) qs.set("page", String(params.page));
  if (params?.limit) qs.set("limit", String(params.limit));
  const suffix = qs.toString() ? `?${qs}` : "";
  return request(`/documents${suffix}`);
}

export function getDocument(id: string): Promise<DocumentDetail> {
  return request(`/documents/${id}`);
}

export function getSourceQuality(
  documentId: string,
): Promise<SourceQualityReport> {
  return request(`/documents/${documentId}/source-quality`);
}

export function getSourceLines(
  documentId: string,
  params?: { page_no?: number; source_version_id?: string },
): Promise<SourceLinesResponse> {
  const qs = new URLSearchParams();
  if (params?.page_no) qs.set("page_no", String(params.page_no));
  if (params?.source_version_id) qs.set("source_version_id", params.source_version_id);
  const suffix = qs.toString() ? `?${qs}` : "";
  return request(`/documents/${documentId}/source-lines${suffix}`);
}

// ------------------------------------------------------------------ Candidates
export function getCandidate(id: string): Promise<CandidateDetail> {
  return request(`/candidates/${id}`);
}

export function approveCandidate(
  id: string,
  body: { reviewer_id: string; confirmed_fields: string[] },
): Promise<CandidateDetail> {
  return request(`/candidates/${id}/approve`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function rejectCandidate(
  id: string,
  body: { reviewer_id: string; reasons: string[] },
): Promise<CandidateDetail> {
  return request(`/candidates/${id}/reject`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ------------------------------------------------------------------ Admin
export function getAdminStats(): Promise<AdminStats> {
  return request("/admin/stats");
}

// ------------------------------------------------------------------ Tasks
export function listTasks(params?: {
  status?: string;
  limit?: number;
}): Promise<TaskListResponse> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.limit) qs.set("limit", String(params.limit));
  const suffix = qs.toString() ? `?${qs}` : "";
  return request(`/tasks${suffix}`);
}
