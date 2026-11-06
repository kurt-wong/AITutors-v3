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

// ------------------------------------------------------------------ Questions (M3a)
export interface QuestionSummary {
  id: string;
  subject: string | null;
  grade: string | null;
  canonical_question_type: string;
  instance_id: string;
  document_id: string;
  source_version_id: string;
  question_number: string;
  question_number_range: string;
  page_no: number;
  instance_order: number;
  created_at: string | null;
  // QUESTION-VISUAL-INSPECTION-V1：真实内容摘要 + 发布状态
  document_file_name: string | null;
  stem_excerpt: string;
  option_count: number;
  answer_count: number;
  explanation_count: number;
  /** official / withheld_review / mixed / none（answer 行 answer_status.publish 聚合） */
  answer_publish: string;
}

export interface QuestionListResponse {
  questions: QuestionSummary[];
  total: number;
}

export interface InstanceRoleContentInfo {
  id: string;
  role: string;
  label: string | null;
  role_index: number;
  text: string;
  text_hash: string;
  source_span: Record<string, unknown>;
  answer_status: Record<string, unknown> | null;
}

export interface QuestionInstanceInfo {
  id: string;
  document_id: string;
  document_file_name: string | null;
  source_version_id: string;
  source_role: string | null;
  source_artifact_kind: string | null;
  question_number: string;
  question_number_range: string;
  page_no: number;
  instance_order: number;
  occurrence_key: string;
  contents: InstanceRoleContentInfo[];
}

export interface QuestionDetail {
  id: string;
  subject: string | null;
  grade: string | null;
  canonical_question_type: string;
  dedup_key: string;
  created_at: string | null;
  instances: QuestionInstanceInfo[];
}

// ------------------------------------------------------------------ Feedback (M3b)
export interface FeedbackOut {
  id: string;
  question_id: string;
  instance_id: string | null;
  source_version_id: string | null;
  producer_unit_id: string | null;
  source_evidence: Record<string, unknown>;
  content_snapshot: Record<string, unknown>;
  category: string;
  description: string;
  status: string;
  created_by: string;
  created_at: string | null;
  review_note: string | null;
}

export interface FeedbackListResponse {
  feedbacks: FeedbackOut[];
  total: number;
  categories: string[];
}

export interface FeedbackCreateRequest {
  question_id: string;
  instance_id?: string | null;
  category: string;
  description: string;
  created_by?: string;
  producer_unit_id?: string | null;
}

// ------------------------------------------------------- Student view (VIS-INSPECT-V1)
// 学生实际视图出参：无诊断字段；非 official 答案/解析文本恒空（服务端门控）。
export interface StudentRoleContentInfo {
  role: string;
  label: string | null;
  role_index: number;
  text: string;
}

export interface StudentInstanceInfo {
  question_number: string;
  question_number_range: string;
  page_no: number;
  contents: StudentRoleContentInfo[];
}

export interface StudentQuestionDetail {
  id: string;
  subject: string | null;
  grade: string | null;
  canonical_question_type: string;
  question_number: string;
  question_number_range: string;
  answer_publish: string;
  student_answer_visible: boolean;
  instances: StudentInstanceInfo[];
}

export interface StudentQuestionSummary {
  id: string;
  subject: string | null;
  grade: string | null;
  canonical_question_type: string;
  question_number: string;
  question_number_range: string;
  page_no: number;
  stem_excerpt: string;
  answer_publish: string;
  student_answer_visible: boolean;
}

export interface StudentQuestionListResponse {
  questions: StudentQuestionSummary[];
  total: number;
}

// ------------------------------------------------------- Inspect volumes (VIS-INSPECT-V1)
export interface DatabaseInfo {
  db_name: string;
  is_default: boolean;
  is_active: boolean;
  series: string | null;
  subject: string | null;
  subject_hint: string | null;
  year: string | null;
  region: string | null;
  question_count: number | null;
}

export interface DatabaseListResponse {
  databases: DatabaseInfo[];
  active_db_name: string;
  default_db_name: string;
}
