import api from './api'

export interface UserStory {
  story_id: string
  project_id: string
  title: string
  description: string | null
  acceptance_criteria: string | null
  page_desc: string | null
  priority: string
  status: string
  created_at: string | null
  updated_at: string | null
}

export interface UserStoryCreatePayload {
  title: string
  description?: string | null
  acceptance_criteria?: string | null
  page_desc?: string | null
  priority?: string
  status?: string
}

export interface UserStoryUpdatePayload {
  title?: string
  description?: string | null
  acceptance_criteria?: string | null
  page_desc?: string | null
  priority?: string
  status?: string
}

export async function listUserStories(projectId: string): Promise<UserStory[]> {
  const res = await api.get<UserStory[]>(`/v1/projects/${projectId}/user-stories`)
  return res.data
}

export async function createUserStory(projectId: string, payload: UserStoryCreatePayload): Promise<UserStory> {
  const res = await api.post<UserStory>(`/v1/projects/${projectId}/user-stories`, payload)
  return res.data
}

export async function getUserStory(storyId: string): Promise<UserStory> {
  const res = await api.get<UserStory>(`/v1/user-stories/${storyId}`)
  return res.data
}

export async function updateUserStory(storyId: string, payload: UserStoryUpdatePayload): Promise<UserStory> {
  const res = await api.patch<UserStory>(`/v1/user-stories/${storyId}`, payload)
  return res.data
}

export async function deleteUserStory(storyId: string): Promise<void> {
  await api.delete(`/v1/user-stories/${storyId}`)
}

export interface UserStoryImportResult {
  imported_count: number
  skipped_count: number
  stories: Array<{ story_id: string; title: string }>
}

export async function importUserStoriesFromRequirements(
  projectId: string,
): Promise<UserStoryImportResult> {
  const res = await api.post<UserStoryImportResult>(
    `/v1/projects/${projectId}/user-stories/import-from-requirements`,
  )
  return res.data
}
