/** API 响应类型 — 与 backend/app/api/schemas.py 对应。 */

export interface DocumentSummary {
  id: string;
  file_name: string;
  file_type: string;
  processing_status: string;
  created_at: string | null;
  candidate_count: number;
  pending_count: number;
}

export interface SourceVersionInfo {
  id: string;
  artifact_kind: string;
  role: string;
  provider: string;
  status: string;
  page_count: number;
  line_count: number;
  body_hash: string;
  integrity_hash: string;
  body_text: string | null;
}

export interface FigureInfo {
  id: string;
  figure_id: string;
  page_no: number;
  object_key: string;
  figure_hash: string;
}

export interface CandidateSummary {
  id: string;
  unit_type: string;
  decision_status: string;
  gate_decision: Record<string, unknown> | null;
  created_at: string | null;
}

export interface DocumentDetail {
  document: DocumentSummary;
  source_versions: SourceVersionInfo[];
  figures: FigureInfo[];
  candidates: CandidateSummary[];
}

export interface DocumentListResponse {
  documents: DocumentSummary[];
  total: number;
}

export interface CandidateDetail {
  id: string;
  unit_type: string;
  source_version_id: string;
  annotation_id: string;
  decision_status: string;
  gate_decision: Record<string, unknown> | null;
  build_versions: Record<string, unknown>;
  input_identity: Record<string, unknown>;
  payload: Record<string, unknown>;
  review_trail: Record<string, unknown>[] | null;
  created_at: string | null;
  decided_at: string | null;
  logical_execution_stage: string;
  logical_execution_hash: string;
}

export interface AdminStats {
  pending_review: number;
  running_tasks: number;
  failed_tasks: number;
  approved_today: number;
}

export interface TaskSummary {
  id: string;
  task_type: string;
  status: string;
  current_stage: string | null;
  created_at: string | null;
  decided_at: string | null;
  llm_invocations: number;
}

export interface TaskListResponse {
  tasks: TaskSummary[];
  total: number;
}

export interface ImportResponse {
  document_id: string;
  task_id: string | null;
  sha256: string;
  file_name: string;
  is_new: boolean;
}

export interface SourceQualityReport {
  status: string; // valid / degraded / invalid / ocr_required
  total_chars: number;
  replacement_char_ratio: number;
  non_printable_ratio: number;
  cjk_ratio: number;
  issues: string[];
}

export interface SourceLineInfo {
  line_ref: string;
  seq: number;
  page_no: number;
  line_no_in_page: number;
  text: string;
  block_type: string;
  bbox: Record<string, number> | null;
  line_hash: string;
}

export interface SourceLinesResponse {
  source_version_id: string;
  page_no: number | null;
  total_lines: number;
  lines: SourceLineInfo[];
}
