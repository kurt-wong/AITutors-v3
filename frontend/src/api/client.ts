/** Typed API client — 只做 HTTP 调用，不含业务逻辑。 */

import type {
  AdminStats,
  CandidateDetail,
  DatabaseInfo,
  DatabaseListResponse,
  DocumentDetail,
  DocumentListResponse,
  FeedbackCreateRequest,
  FeedbackListResponse,
  FeedbackOut,
  QuestionDetail,
  QuestionListResponse,
  SourceLinesResponse,
  SourceQualityReport,
  StudentQuestionDetail,
  StudentQuestionListResponse,
  TaskListResponse,
} from "./types";

const BASE = "/api";

// DSH-F1 加固：库上下文随请求显式传递（X-Inspect-Db），不依赖进程级活动库，
// 消除并行任务/脚本切换活动库导致同一 URL 读到另一卷数据的竞态。
let inspectDb: string | null = null;

export function setInspectDb(name: string | null) {
  const n = (name ?? "").trim();
  inspectDb = n || null;
}

export function getInspectDb(): string | null {
  return inspectDb;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (inspectDb) headers["X-Inspect-Db"] = inspectDb;
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { ...headers, ...((init?.headers as Record<string, string>) ?? {}) },
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

// ------------------------------------------------------------------ Questions (M3a)
export function listQuestions(params?: {
  document_id?: string;
  subject?: string;
  publish?: string;
  limit?: number;
  offset?: number;
}): Promise<QuestionListResponse> {
  const qs = new URLSearchParams();
  if (params?.document_id) qs.set("document_id", params.document_id);
  if (params?.subject) qs.set("subject", params.subject);
  if (params?.publish) qs.set("publish", params.publish);
  if (params?.limit != null) qs.set("limit", String(params.limit));
  if (params?.offset != null) qs.set("offset", String(params.offset));
  const suffix = qs.toString() ? `?${qs}` : "";
  return request(`/questions${suffix}`);
}

export function getQuestion(id: string): Promise<QuestionDetail> {
  return request(`/questions/${id}`);
}

// ------------------------------------------------------- Student view (VIS-INSPECT-V1)
export function listStudentQuestions(params?: {
  subject?: string;
  document_id?: string;
  limit?: number;
  offset?: number;
}): Promise<StudentQuestionListResponse> {
  const qs = new URLSearchParams();
  if (params?.subject) qs.set("subject", params.subject);
  if (params?.document_id) qs.set("document_id", params.document_id);
  if (params?.limit != null) qs.set("limit", String(params.limit));
  if (params?.offset != null) qs.set("offset", String(params.offset));
  const suffix = qs.toString() ? `?${qs}` : "";
  return request(`/student/questions${suffix}`);
}

export function getStudentQuestion(id: string): Promise<StudentQuestionDetail> {
  return request(`/student/questions/${id}`);
}

// ------------------------------------------------------- Inspect volumes (VIS-INSPECT-V1)
export function listDatabases(): Promise<DatabaseListResponse> {
  return request("/inspect/databases");
}

export function activateDatabase(db_name: string): Promise<DatabaseInfo> {
  return request("/inspect/activate", {
    method: "POST",
    body: JSON.stringify({ db_name }),
  });
}

export function getActiveDatabase(): Promise<DatabaseInfo> {
  return request("/inspect/active");
}

// ------------------------------------------------------------------ Feedback (M3b)
export function createFeedback(
  body: FeedbackCreateRequest,
): Promise<FeedbackOut> {
  return request("/feedbacks", { method: "POST", body: JSON.stringify(body) });
}

export function listFeedbacks(params?: {
  question_id?: string;
  status?: string;
  limit?: number;
}): Promise<FeedbackListResponse> {
  const qs = new URLSearchParams();
  if (params?.question_id) qs.set("question_id", params.question_id);
  if (params?.status) qs.set("status", params.status);
  if (params?.limit != null) qs.set("limit", String(params.limit));
  const suffix = qs.toString() ? `?${qs}` : "";
  return request(`/feedbacks${suffix}`);
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
