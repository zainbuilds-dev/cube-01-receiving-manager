export interface POLineItem {
  sku: string
  asin?: string | null
  product_title?: string | null
  spec_colour?: string | null
  spec_variant?: string | null
  spec_components?: string[] | null
  cartons_ordered?: number | null
  units_per_carton_ordered?: number | null
  qty_ordered: number
}
export interface PO {
  unit_id: string
  po_number: string
  po_line: number
  supplier?: string | null
  operator_id?: string | null
  line_items: POLineItem[]
}
export interface EvidenceItem {
  type: string; image_id?: string | null; quote?: string | null
  description: string; strength: number
}
export type Verdict = 'PASS' | 'FAIL' | 'UNCERTAIN' | 'NOT_APPLICABLE'
export interface CheckResult {
  check_key: string; verdict: Verdict; confidence: number; detail: string
  evidence: EvidenceItem[]; model_version: string; latency_ms: number
  uncertainty_reason?: string | null; summary_value?: string | null
}
export interface Outcome {
  decision: string; disposition: string; decided_by: string
  decided_at: string; policy_version: string; reason: string
}
export interface ImageEntry { image_id: string; sha256: string; filename: string }
export interface ReceivingSummary {
  identity_match: string; carton_damage: string; unit_damage: string
  cartons_received: string; units_per_carton_counted: string
  qty_received: string; quality_flags: string[]; note?: string | null
    qty_received_source?: string | null
}
export interface EvidenceRecord {
  record_id: string; schema_version: string; organization_id: string; client_id: string
  agent: { name: string; version: string }
  subject: {
    unit_id: string; po_number: string; po_line: number
    supplier?: string | null; operator_id?: string | null; line_items: POLineItem[]
  }
  captured_at: string; operator_label?: string | null
  images: ImageEntry[]; checks: CheckResult[]; receiving_summary?: ReceivingSummary | null
  outcome: Outcome; inspection_status?: string
  overrides: unknown[]; status: string; content_hash: string
}
export interface RecordSummary {
  record_id: string; unit_id: string; status: string
  decision?: string | null; created_at: string
}