/** Shared TypeScript types mirroring the FastAPI contract. */

export type Role = "GEOLOGIST" | "MINISTRY_OFFICIAL" | "AUDITOR";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: Role;
  title: string;
  subsidiary: string;
}

export interface DemoAccount {
  email: string;
  password: string;
  role: Role;
  name: string;
  title: string;
}

export type DocCategory =
  | "GEOLOGICAL_REPORT"
  | "PROSPECTING"
  | "PRODUCTION"
  | "ENVIRONMENTAL"
  | "RESERVES";

export type DocStatus =
  | "UPLOADING"
  | "OCR"
  | "EXTRACTING"
  | "INDEXING"
  | "READY"
  | "FAILED";

export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

/** Normalized 0–1 bounding box (matches backend JSONB). */
export interface BBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface Coalfield {
  id: string;
  name: string;
  state: string;
  subsidiary: string;
  area_sqkm: number;
  baseline_gcv?: number;
  baseline_ash?: number;
  baseline_ob_ratio?: number;
  reserve_mt?: number;
}

export interface Document {
  id: string;
  title: string;
  category: DocCategory;
  coalfield_id: string;
  coalfield_name?: string;
  block: string;
  district: string;
  source_type: string;
  status: DocStatus;
  ingestion_progress: { step: string; pct: number; message: string };
  page_count: number;
  size_bytes: number;
  total_confidence: number;
  report_date: string;
  uploaded_at: string;
  pages_dir: string;
}

export interface PageResult {
  page_number: number;
  image_path: string;
  width: number;
  height: number;
  text: string;
  ocr_conf_mean: number;
}

export interface FieldExtraction {
  id: string;
  field_key: string;
  field_label: string;
  value: string;
  unit: string;
  confidence: number;
  bbox: BBox;
  matched_text: string;
  page_number: number;
  method: string;
  numeric_value: number | null;
}

export interface TextEmission {
  id: string;
  page_id: string;
  text: string;
  bbox: BBox;
  confidence: number;
  is_heading: boolean;
  char_start: number;
  char_end: number;
}

/** Traceability contract — everything clickable carries one of these. */
export interface SourceRef {
  value?: string | number;
  display: string;
  document_id: string;
  document_title?: string;
  page: number;
  bbox: BBox;
  confidence: number;
}

export interface ReportSection {
  kind: "narrative" | "table";
  title: string;
  content: Record<string, unknown>;
  refs: SourceRef[];
}

export interface Report {
  id: string;
  title: string;
  document_id: string;
  document_title?: string;
  role: Role;
  summary: string;
  status: string;
  generated_at: string;
  sections: ReportSection[];
  total_refs?: number;
}

export interface Anomaly {
  id: string;
  field_key: string;
  field_label: string;
  coalfield_id: string;
  block: string;
  expected_value: string;
  actual_value: string;
  deviation_pct: number;
  severity: Severity;
  rationale: string;
  primary_doc_id: string;
  baseline_doc_id: string;
  baseline_page_number: number;
  baseline_bbox: BBox;
  baseline_confidence: number;
  status: "open" | "reviewed";
  detected_at: string;
}

export interface WordStat {
  word: string;
  count: number;
}

export interface Topic {
  id: string;
  key: string;
  label: string;
  color: string;
  weight: number;
  quarter: string;
  doc_count: number;
}

export interface TopicDocument {
  id: string;
  title: string;
  block: string;
  coalfield: string;
  report_date: string;
}

export interface TopicDrift {
  quarter: string;
  topics: { key: string; label: string; color: string; weight: number }[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  language: "en" | "hi";
  mode: "text" | "voice";
  confidence: number;
  response_ms: number;
  citations: Citation[];
}

export interface Citation {
  id: string;
  rank: number;
  snippet: string;
  document_id: string;
  document_title: string;
  page_number: number;
  bbox: BBox;
  score: number;
}

export interface MetricSummary {
  report_prep_reduction_pct: number;
  extraction_accuracy_pct: number;
  automation_pct: number;
  query_resolution_pct: number;
  docs_processed: number;
  docs_total: number;
  anomalies_open: number;
  avg_response_ms: number;
  trend: "up" | "down" | "flat";
}

export interface MetricPoint {
  captured_on: string;
  report_prep_min: number;
  extraction_accuracy_pct: number;
  automation_pct: number;
  query_resolution_pct: number;
}

export interface DashboardPayload {
  role: Role;
  stats: Record<string, number | string>;
  items: Record<string, unknown>[];
  highlights: { label: string; value: string; icon: string; tone: string }[];
}

export interface Health {
  status: string;
  demo_mode: boolean;
  documents: number;
  database: string;
}

export interface UploadProgress {
  document_id: string;
  step: string;
  pct: number;
  message: string;
  status: string;
}