export interface AnalysisIssue {
  rule_id: string
  severity: string
  message: string
  node_ids?: string[]
  fix_hint: string
}

export interface ConsistencyIssue {
  rule_id: string
  severity: string
  message: string
  c4_node_id: string
  code_entity_id: string
  fix_hint: string
  fix_action: string
}

export interface LevelAnalysis {
  level: string
  passed: boolean
  issues: AnalysisIssue[]
  summary: Record<string, number>
}

export interface ConsistencyReport {
  passed: boolean
  issues: ConsistencyIssue[]
  summary: Record<string, number>
  code_scan_summary: Record<string, number>
}

export interface AnalyzeResponse {
  project_id: string
  overall_passed: boolean
  levels: LevelAnalysis[]
  consistency: ConsistencyReport | null
}

export interface C4ChangeSet {
  action: string
  target_path: string
  before?: string
  after?: string
  rationale: string
  risk_level: string
  auto_applicable: boolean
  requires_confirmation: boolean
  issue_id: string
}

export interface C4FixPlanItem {
  issue_ids: string[]
  changes: C4ChangeSet[]
  dry_run: boolean
}

export interface C4FixPlanResponse {
  project_id: string
  plans: C4FixPlanItem[]
  analysis?: string
  strategy_prompt?: string
}
