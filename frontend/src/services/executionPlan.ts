import api from './api'
import type {
  ExecutionPlanDetail,
  ExecutionPlanItem,
  PlanNode,
} from '@/types/execution-plan'
import type { LogQueryResult } from '@/types/skill-execution'

export interface CreatePlanPayload {
  template_level: string | null
  skill_nodes?: Record<string, unknown>[]
}

export interface BypassRequestPayload {
  stage_id: string
  skill_id: string
  authorization_token: string
  acknowledged: boolean
  reason?: string
}

export async function fetchExecutionPlans(): Promise<ExecutionPlanItem[]> {
  const res = await api.get<ExecutionPlanItem[]>('/v1/execution-plans')
  return res.data
}

export async function fetchProjectExecutionPlans(
  projectId: string,
): Promise<ExecutionPlanDetail[]> {
  const res = await api.get<ExecutionPlanDetail[]>(
    `/v1/projects/${projectId}/execution-plans`,
  )
  return res.data
}

export async function createExecutionPlan(
  projectId: string,
  payload: CreatePlanPayload,
): Promise<ExecutionPlanDetail> {
  const res = await api.post<ExecutionPlanDetail>(
    `/v1/projects/${projectId}/execution-plans`,
    payload,
  )
  return res.data
}

export async function getExecutionPlan(
  planId: string,
): Promise<ExecutionPlanDetail> {
  const res = await api.get<ExecutionPlanDetail>(`/v1/execution-plans/${planId}`)
  return res.data
}

export async function deleteExecutionPlan(planId: string): Promise<void> {
  await api.delete(`/v1/execution-plans/${planId}`)
}

export async function freezeExecutionPlan(
  planId: string,
): Promise<ExecutionPlanDetail> {
  const res = await api.post<ExecutionPlanDetail>(
    `/v1/execution-plans/${planId}/freeze`,
  )
  return res.data
}

export async function executeExecutionPlan(
  planId: string,
): Promise<{ stage_id: string; status: string }> {
  const res = await api.post<{ stage_id: string; status: string }>(
    `/v1/execution-plans/${planId}/execute`,
  )
  return res.data
}

export async function cancelExecutionPlan(
  planId: string,
): Promise<ExecutionPlanDetail> {
  const res = await api.post<ExecutionPlanDetail>(
    `/v1/execution-plans/${planId}/cancel`,
  )
  return res.data
}

export async function pauseExecutionPlan(
  planId: string,
): Promise<{ plan_id: string; action: string; message: string }> {
  const res = await api.post<{ plan_id: string; action: string; message: string }>(
    `/v1/execution-plans/${planId}/pause`,
  )
  return res.data
}

export async function resumeExecutionPlan(
  planId: string,
): Promise<{ plan_id: string; action: string; message: string }> {
  const res = await api.post<{ plan_id: string; action: string; message: string }>(
    `/v1/execution-plans/${planId}/resume`,
  )
  return res.data
}

export async function getExecutionStatus(
  planId: string,
): Promise<{ execution_id: string; plan_id: string; nodes: Pick<PlanNode, 'node_id' | 'status'>[] }> {
  const res = await api.get<{
    execution_id: string
    plan_id: string
    nodes: Pick<PlanNode, 'node_id' | 'status'>[]
  }>(`/v1/execution-plans/${planId}/status`)
  return res.data
}

export async function getExecutionLogs(
  planId: string,
  anchor?: string | null,
): Promise<LogQueryResult> {
  const params = anchor ? { anchor } : {}
  const res = await api.get<LogQueryResult>(`/v1/executions/${planId}/logs`, {
    params,
  })
  return res.data
}

export async function createBypass(
  planId: string,
  payload: BypassRequestPayload,
): Promise<unknown> {
  const res = await api.post(`/v1/executions/${planId}/bypass`, payload)
  return res.data
}

export async function listBypassRecords(planId: string): Promise<unknown[]> {
  const res = await api.get<unknown[]>(`/v1/executions/${planId}/bypass-status`)
  return res.data
}
