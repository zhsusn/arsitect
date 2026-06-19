import { useEffect, useRef } from 'react'
import { SSEClient, type ProjectSSEEvent } from '../services/sse'

export type { ProjectSSEEvent }
export { SSEClient }

export function useProjectSSE(
  projectId: string | undefined,
  onEvent: (event: ProjectSSEEvent) => void,
) {
  const onEventRef = useRef(onEvent)

  useEffect(() => {
    onEventRef.current = onEvent
  }, [onEvent])

  useEffect(() => {
    if (!projectId) return undefined
    const client = new SSEClient(projectId, (event) => {
      onEventRef.current(event)
    })
    return () => {
      client.close()
    }
  }, [projectId])
}
