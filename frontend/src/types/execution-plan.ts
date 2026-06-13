export interface ExecutionPlan {
  plan_id: string
  project_id: string
  project_name?: string
  version: string
  is_frozen: boolean
  status?: string
  template_level: string | null
  node_order: string[]
  parallel_groups: ParallelGroup[]
  dependency_matrix: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface PlanNode {
  node_id: string
  plan_id: string
  skill_id: string
  stage_id: string
  order_index: number
  node_type: 'primary' | 'auxiliary'
  module_id: string | null
  status: string
}

export interface ParallelGroup {
  group_id: string
  stage_id: string
  skill_ids: string[]
  group_type: 'primary_serial' | 'auxiliary_parallel'
}

export interface ExecutionPlanDetail extends ExecutionPlan {
  nodes: PlanNode[]
}

export interface ExecutionPlanItem {
  plan_id: string
  project_id: string
  project_name: string | null
  version: string
  status: 'Draft' | 'Frozen' | 'Running' | 'Completed' | 'Failed'
  template_level: string | null
  created_at: string
  updated_at: string
}
