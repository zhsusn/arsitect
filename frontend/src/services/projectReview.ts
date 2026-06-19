import api from './api'

export interface ProjectReview {
  review_id: string
  project_id: string
  review_type: string
  item_id: string
  item_type: string
  status: string
  notes: string | null
  reviewer_id: string | null
  created_at: string | null
  updated_at: string | null
}

export interface ProjectReviewCreateDTO {
  review_type: string
  item_id: string
  item_type: string
  status?: string
  notes?: string
  reviewer_id?: string
}

export interface ProjectReviewUpdateDTO {
  status?: string
  notes?: string
  reviewer_id?: string
}

export interface ProjectReviewListResponse {
  data: ProjectReview[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

export async function listProjectReviews(
  projectId: string,
  reviewType?: string,
  itemType?: string,
  page: number = 1,
  pageSize: number = 100,
): Promise<ProjectReview[]> {
  const params = new URLSearchParams()
  if (reviewType) params.append('review_type', reviewType)
  if (itemType) params.append('item_type', itemType)
  params.append('page', String(page))
  params.append('page_size', String(pageSize))

  const response = await api.get<ProjectReviewListResponse>(
    `/v1/projects/${projectId}/reviews?${params.toString()}`
  )
  return response.data.data
}

export async function createProjectReview(
  projectId: string,
  dto: ProjectReviewCreateDTO,
): Promise<ProjectReview> {
  const response = await api.post<ProjectReview>(
    `/v1/projects/${projectId}/reviews`,
    dto,
  )
  return response.data
}

export async function updateProjectReview(
  projectId: string,
  reviewId: string,
  dto: ProjectReviewUpdateDTO,
): Promise<ProjectReview> {
  const response = await api.put<ProjectReview>(
    `/v1/projects/${projectId}/reviews/${reviewId}`,
    dto,
  )
  return response.data
}

export async function deleteProjectReview(
  projectId: string,
  reviewId: string,
): Promise<void> {
  await api.delete(`/v1/projects/${projectId}/reviews/${reviewId}`)
}

export async function batchUpsertProjectReviews(
  projectId: string,
  items: ProjectReviewCreateDTO[],
): Promise<ProjectReview[]> {
  const response = await api.post<ProjectReview[]>(
    `/v1/projects/${projectId}/reviews/batch`,
    items,
  )
  return response.data
}
