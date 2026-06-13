export type ExecutionOverallStatus =
  | 'NOT_STARTED'
  | 'RUNNING'
  | 'SUCCESS'
  | 'FAILED'
  | 'STOPPED'
  | 'UNKNOWN'

export type ExecutionPhaseStatus = 'RUNNING' | 'COMPLETED' | 'FAILED' | 'STOPPED'

export interface SkillExecution {
  execution_id: string
  project_id: string
  stage_id: string
  skill_id: string
  skill_name: string
  trigger_action: string
  current_phase: string
  phase_status: ExecutionPhaseStatus
  overall_status: ExecutionOverallStatus
  retry_count: number
  previous_execution_id: string | null
  is_release_skill: boolean
  release_confirmed: boolean
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface LogEntry {
  timestamp: string
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
  content: string
}

export interface LogQueryResult {
  log_entries: LogEntry[]
  total_count: number
  next_anchor: string | null
}
