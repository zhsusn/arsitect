import api from './api'

export interface ExecutionTask {
  task_id: string
  project_id: string
  name: string
  type: 'coding' | 'test' | 'bugfix'
  status: 'not_started' | 'in_progress' | 'passed' | 'failed' | 'blocked'
  input_artifacts: string | null
  assigned_skill_id: string | null
  parent_module: string | null
  output_artifact_path: string | null
  retry_count: number
  created_at: string
  updated_at: string
}

export interface ExecutionIssue {
  issue_id: string
  project_id: string
  task_id: string
  issue_type: 'compile_error' | 'test_failure' | 'arch_mismatch' | 'interface_mismatch' | 'other'
  error_log: string | null
  related_artifacts: string | null
  suggested_action: 'retry' | 'feedback' | 'skip' | null
  feedback_to_architecture: boolean
  target_artifact_id: string | null
  change_request_id: string | null
  status: 'open' | 'resolved' | 'closed'
  created_at: string
  updated_at: string
}

export interface CreateTaskPayload {
  name: string
  type: 'coding' | 'test' | 'bugfix'
  input_artifacts?: string[]
  assigned_skill_id?: string
  parent_module?: string
}

export interface UpdateTaskPayload {
  name?: string
  type?: 'coding' | 'test' | 'bugfix'
  status?: 'not_started' | 'in_progress' | 'passed' | 'failed' | 'blocked'
  input_artifacts?: string[]
  assigned_skill_id?: string
  parent_module?: string
}

export interface CreateIssuePayload {
  task_id: string
  issue_type: 'compile_error' | 'test_failure' | 'arch_mismatch' | 'interface_mismatch' | 'other'
  error_log?: string
  related_artifacts?: string[]
  suggested_action?: 'retry' | 'feedback' | 'skip'
  target_artifact_id?: string
}

export interface IssueFeedbackPayload {
  feedback_to_architecture: boolean
  change_request_id?: string
}

export async function fetchTasks(projectId: string): Promise<ExecutionTask[]> {
  const res = await api.get<ExecutionTask[]>(`/v1/execution/${projectId}/tasks`)
  return res.data
}

export async function createTask(projectId: string, payload: CreateTaskPayload): Promise<ExecutionTask> {
  const res = await api.post<ExecutionTask>(`/v1/execution/${projectId}/tasks`, payload)
  return res.data
}

export async function updateTask(
  projectId: string,
  taskId: string,
  payload: UpdateTaskPayload,
): Promise<ExecutionTask> {
  const res = await api.patch<ExecutionTask>(`/v1/execution/${projectId}/tasks/${taskId}`, payload)
  return res.data
}

export async function executeTask(projectId: string, taskId: string): Promise<void> {
  await api.post(`/v1/execution/${projectId}/tasks/${taskId}/execute`)
}

export async function retryTask(projectId: string, taskId: string): Promise<void> {
  await api.post(`/v1/execution/${projectId}/tasks/${taskId}/retry`)
}

export interface MarkBugPayload {
  errorLog: string
  issueType: 'compile_error' | 'test_failure' | 'arch_mismatch' | 'interface_mismatch' | 'other'
}

export async function markBug(
  projectId: string,
  taskId: string,
  payload: MarkBugPayload,
): Promise<{ taskId: string; issueId: string }> {
  const res = await api.post<{ taskId: string; issueId: string }>(
    `/v1/execution/${projectId}/tasks/${taskId}/mark-bug`,
    payload,
  )
  return res.data
}

export async function fetchIssues(projectId: string): Promise<ExecutionIssue[]> {
  const res = await api.get<ExecutionIssue[]>(`/v1/execution/${projectId}/issues`)
  return res.data
}

export async function createIssue(
  projectId: string,
  payload: CreateIssuePayload,
): Promise<ExecutionIssue> {
  const res = await api.post<ExecutionIssue>(`/v1/execution/${projectId}/issues`, payload)
  return res.data
}

export async function feedbackIssue(
  projectId: string,
  issueId: string,
  payload: IssueFeedbackPayload,
): Promise<ExecutionIssue> {
  const res = await api.patch<ExecutionIssue>(
    `/v1/execution/${projectId}/issues/${issueId}/feedback`,
    payload,
  )
  return res.data
}
