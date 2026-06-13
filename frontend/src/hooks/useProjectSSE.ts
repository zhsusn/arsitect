import { useEffect, useRef } from 'react'

export interface ProjectSSEEvent {
  type: string
  data: Record<string, unknown>
}

export function useProjectSSE(
  projectId: string | undefined,
  onEvent: (event: ProjectSSEEvent) => void,
) {
  const onEventRef = useRef(onEvent)

  useEffect(() => {
    onEventRef.current = onEvent
  }, [onEvent])

  useEffect(() => {
    if (!projectId) return

    const source = new EventSource(`/api/v1/events/${projectId}`)

    source.onmessage = (message) => {
      try {
        const event = JSON.parse(message.data) as ProjectSSEEvent
        onEventRef.current(event)
      } catch (err) {
        console.error('Failed to parse SSE message:', err)
      }
    }

    source.onerror = (err) => {
      console.error('SSE error:', err)
    }

    return () => {
      source.close()
    }
  }, [projectId])
}
