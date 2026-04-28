// --- Upload ---
export interface ColumnInfo {
  name: string
  detected_type: 'name' | 'binary' | 'categorical' | 'numeric' | 'pincode' | 'unknown'
  sample_values: string[]
  null_pct: number
}

export interface SuggestedOutcome {
  column: string
  positive_value: string
  confidence: number
  method: string
}

export interface SuggestedSensitive {
  column: string
  reason: string
  confidence: number
}

export interface UploadResponse {
  file_id: string
  row_count: number
  column_count: number
  columns: ColumnInfo[]
  preview_rows: Record<string, unknown>[]
  suggested_outcome: SuggestedOutcome | null
  suggested_sensitive: SuggestedSensitive[]
}

export interface ColumnMapping {
  outcome_column: string
  outcome_positive_value: string
  sensitive_columns: string[]
}

// --- Inspect ---
export interface GroupStat {
  label: string
  count: number
  hire_rate: number
}

export interface ColumnDistribution {
  column: string
  type: string
  skew_flag: boolean
  skew_reason?: string
  distribution: GroupStat[]
}

export interface InspectResponse {
  dataset_health: {
    total_rows: number
    usable_rows: number
    hire_rate_overall: number
  }
  column_distributions: ColumnDistribution[]
}

// --- Audit ---
export type Severity = 'high' | 'medium' | 'compliant'

export interface ProxyFinding {
  id: string
  column: string
  proxy_type: 'caste' | 'socioeconomic' | 'class'
  proxy_mechanism: string
  affected_group: string
  comparison_group: string
  affected_hire_rate: number
  comparison_hire_rate: number
  disparity_ratio: number
  sample_size_affected: number
  severity: Severity
  legal_note: string
}

export interface ByGroupMetrics {
  selection_rate: number
  true_positive_rate: number
}

export interface BiasMetrics {
  model_accuracy: number | null
  demographic_parity_difference: number | null
  equalized_odds_difference: number | null
  disparate_impact_ratio: number | null
  disparate_impact_flag: boolean
  disparate_impact_legal_threshold: number
  by_group: Record<string, Record<string, ByGroupMetrics>>
}

export interface MitigationMetrics {
  method: string
  demographic_parity_difference_after: number | null
  equalized_odds_difference_after: number | null
  disparate_impact_ratio_after: number | null
  accuracy_after: number | null
  accuracy_delta: number | null
}

export interface AuditResponse {
  proxy_findings: ProxyFinding[]
  bias_metrics: BiasMetrics
  mitigation_metrics: MitigationMetrics
}

// --- Narrative ---
export interface NarrativeParagraph {
  section: string
  heading: string
  text: string
}

export interface DpdpItem {
  article: string
  description: string
  status: 'non_compliant' | 'at_risk' | 'review_required' | 'compliant'
  finding_id?: string
}

export interface NarrativeResponse {
  narrative_paragraphs: NarrativeParagraph[]
  dpdp_checklist: DpdpItem[]
}

// --- App State ---
export type AuditStep = 'upload' | 'inspect' | 'audit' | 'report'

export interface AuditState {
  step: AuditStep
  file_id: string | null
  upload_response: UploadResponse | null
  column_mapping: ColumnMapping | null
  inspect_response: InspectResponse | null
  audit_response: AuditResponse | null
  narrative_response: NarrativeResponse | null
  company_name: string
  loading: boolean
  error: string | null
}
