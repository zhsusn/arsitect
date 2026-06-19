import api from './api'

export async function getArtifactContent(artifactId: string): Promise<string> {
  const res = await api.get<{ content: string }>(`/v1/artifacts/${artifactId}/content`)
  return res.data.content
}

export async function saveArtifactContent(
  artifactId: string,
  content: string,
): Promise<void> {
  await api.put(`/v1/artifacts/${artifactId}/content`, { content })
}
