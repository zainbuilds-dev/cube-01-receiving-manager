export interface POLineItem {
  sku: string
  product_name?: string | null
  expected_qty: number
  variant?: string | null
  expected_cartons?: number | null
  units_per_carton?: number | null
  components?: string[] | null
}
export interface PO { po_number: string; supplier?: string | null; line_items: POLineItem[] }
export interface EvidenceItem {
  type: string; image_id?: string | null; quote?: string | null
  description: string; strength: number
}
export type Verdict = 'PASS' | 'FAIL' | 'UNCERTAIN' | 'NOT_APPLICABLE'
export interface CheckResult {
  check_key: string; verdict: Verdict; confidence: number; detail: string
  evidence: EvidenceItem[]; model_version: string; latency_ms: number
  uncertainty_reason?: string | null
}
export interface Outcome {
  decision: string; disposition: string; decided_by: string
  decided_at: string; policy_version: string; reason: string
}
export interface ImageEntry { image_id: string; sha256: string; filename: string }
export interface EvidenceRecord {
  record_id: string; schema_version: string; organization_id: string; client_id: string
  agent: { name: string; version: string }
  subject: { po_number: string; supplier?: string | null; line_items: POLineItem[] }
  captured_at: string; operator_label?: string | null
  images: ImageEntry[]; checks: CheckResult[]; outcome: Outcome
  overrides: unknown[]; status: string; content_hash: string
}
export interface RecordSummary { record_id: string; status: string; decision?: string | null; created_at: string }