export interface StageSkill {
  skill_id: string | null
  skill_name: string
  version: string
  pattern: string
  tags: string[] | null
  platforms: string[] | null
  description: string | null
  directory_path: string
  parse_status: string
}

export interface StageExecution {
  execution_id: string
  project_id: string
  stage_id: string
  skill_id: string
  skill_name: string
  trigger_action: string
  current_phase: string
  phase_status: string
  overall_status: string
  retry_count: number
  previous_execution_id: string | null
  is_release_skill: boolean
  release_confirmed: boolean
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface StageArtifactFile {
  artifact_id: string
  file_name: string
  file_type: string
  file_size_bytes: number
  current_version: number
  external_status: string
  stale_flag: boolean
  updated_at: string | null
}

export interface StageArtifactDirectory {
  directory: string
  files: StageArtifactFile[]
}

export interface StageLogEntry {
  timestamp: string
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
  content: string
}

export interface StageLogResult {
  log_entries: StageLogEntry[]
  total_count: number
  next_anchor: string | null
}

export interface StageAnnotation {
  annotation_id: string
  stage_id: string
  author: string
  content: string
  annotation_type: string
  status: string
  viewed_at: string | null
}

export interface StageGate {
  decision_id: string
  gate_id: string
  project_id: string
  gate_type: string
  status: 'pending' | 'passed' | 'rejected' | 'bypassed'
  confidence: string | null
  decision_type: string | null
  decision_by: string | null
  decision_at: string | null
  duration_sec: number | null
  reason: string | null
  unlocked_stages: string[]
  created_at: string | null
  updated_at: string | null
}

export interface ProjectStage {
  project_stage_id: string
  project_id: string
  stage_id: string
  order_index: number
  status: string
  primary_skill_id: string | null
  skippable: boolean
  is_frozen: boolean
  merge_group_id: string | null
  execution_status: string
}
