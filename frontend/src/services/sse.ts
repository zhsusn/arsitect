import { useEffect, useRef } from 'react'

export interface ProjectSSEEvent {
  type: string
  data: Record<string, unknown>
}

export type ConnectionStatus = 'connecting' | 'open' | 'closed' | 'error'

export interface SSEClientOptions {
  maxReconnectDelay?: number
  initialReconnectDelay?: number
}

export class SSEClient {
  private projectId: string
  private onEvent: (event: ProjectSSEEvent) => void
  private onError?: (error: Event) => void
  private options: Required<SSEClientOptions>
  private source: EventSource | null = null
  private status: ConnectionStatus = 'connecting'
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectDelay: number
  private closed = false
  private statusSubscribers = new Set<(status: ConnectionStatus) => void>()

  constructor(
    projectId: string,
    onEvent: (event: ProjectSSEEvent) => void,
    onError?: (error: Event) => void,
    options: SSEClientOptions = {},
  ) {
    this.projectId = projectId
    this.onEvent = onEvent
    this.onError = onError
    this.options = {
      maxReconnectDelay: options.maxReconnectDelay ?? 5000,
      initialReconnectDelay: options.initialReconnectDelay ?? 1000,
    }
    this.reconnectDelay = this.options.initialReconnectDelay
    this.connect()
  }

  private setStatus(next: ConnectionStatus) {
    this.status = next
    this.statusSubscribers.forEach((cb) => cb(next))
  }

  private connect() {
    if (this.closed || typeof window === 'undefined') return
    this.setStatus('connecting')
    const source = new EventSource(`/api/v1/projects/${this.projectId}/sse`)
    this.source = source

    source.onopen = () => {
      this.setStatus('open')
      this.reconnectDelay = this.options.initialReconnectDelay
    }

    source.onmessage = (message) => {
      try {
        const event = JSON.parse(message.data) as ProjectSSEEvent
        this.onEvent(event)
      } catch (err) {
        console.error('Failed to parse SSE message:', err)
      }
    }

    source.onerror = (err) => {
      this.setStatus('error')
      if (this.onError) this.onError(err)
      this.scheduleReconnect()
    }
  }

  private scheduleReconnect() {
    if (this.closed) return
    this.cleanupSource()
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.reconnectTimer = setTimeout(() => {
      this.reconnectDelay = Math.min(
        this.reconnectDelay * 2,
        this.options.maxReconnectDelay,
      )
      this.connect()
    }, this.reconnectDelay)
  }

  private cleanupSource() {
    if (this.source) {
      this.source.close()
      this.source = null
    }
  }

  close() {
    this.closed = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.cleanupSource()
    this.setStatus('closed')
  }

  getStatus(): ConnectionStatus {
    return this.status
  }

  subscribeStatus(callback: (status: ConnectionStatus) => void): () => void {
    this.statusSubscribers.add(callback)
    callback(this.status)
    return () => {
      this.statusSubscribers.delete(callback)
    }
  }
}

export function useProjectSSE(
  projectId: string | null | undefined,
  handlers: Partial<Record<string, (data: Record<string, unknown>) => void>>,
) {
  const handlersRef = useRef(handlers)

  useEffect(() => {
    handlersRef.current = handlers
  }, [handlers])

  useEffect(() => {
    if (!projectId) return undefined
    const client = new SSEClient(projectId, (event) => {
      const handler = handlersRef.current[event.type]
      if (handler) {
        handler(event.data)
      }
    })
    return () => {
      client.close()
    }
  }, [projectId])
}
