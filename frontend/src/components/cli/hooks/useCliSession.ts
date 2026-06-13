import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '@/services/api'
import type { CliMode, CliSession, CliResponse, CliCard, SocketStatus, CliRequest } from '../types'

const WS_SCHEME = window.location.protocol === 'https:' ? 'wss' : 'ws'
const WS_BASE = `${WS_SCHEME}://${window.location.host}/ws`

export interface UseCliSessionOptions {
  projectId: string
  mode: CliMode
  onMessage?: (response: CliResponse) => void
  onCard?: (card: CliCard) => void
}

export interface UseCliSessionReturn {
  session: CliSession | null
  status: SocketStatus
  mode: CliMode
  sendCommand: (text: string, metadata?: Record<string, unknown>) => void
  sendAction: (command: string, metadata?: Record<string, unknown>) => void
  clearSession: () => void
  reconnect: () => void
}

interface QueuedMessage {
  type: 'command' | 'action'
  text?: string
  command?: string
  metadata?: Record<string, unknown>
}

const MAX_RETRIES = 3

export function useCliSession({ projectId, mode, onMessage, onCard }: UseCliSessionOptions): UseCliSessionReturn {
  const [session, setSession] = useState<CliSession | null>(null)
  const [status, setStatus] = useState<SocketStatus>('connecting')
  const wsRef = useRef<WebSocket | null>(null)
  const retryCountRef = useRef(0)
  const retryTimeoutRef = useRef<number | null>(null)
  const mountedRef = useRef(true)
  const onMessageRef = useRef(onMessage)
  const onCardRef = useRef(onCard)
  const queueRef = useRef<QueuedMessage[]>([])

  useEffect(() => {
    onMessageRef.current = onMessage
    onCardRef.current = onCard
  })

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  const closeSocket = useCallback(() => {
    if (retryTimeoutRef.current) {
      window.clearTimeout(retryTimeoutRef.current)
      retryTimeoutRef.current = null
    }
    const ws = wsRef.current
    if (ws) {
      ws.onclose = null
      ws.onerror = null
      ws.onmessage = null
      ws.onopen = null
      ws.close()
      wsRef.current = null
    }
  }, [])

  const flushQueue = useCallback(() => {
    const ws = wsRef.current
    const currentSession = session
    if (!currentSession || !ws || ws.readyState !== WebSocket.OPEN) return

    while (queueRef.current.length > 0) {
      const item = queueRef.current.shift()
      if (!item) continue

      const request: CliRequest =
        item.type === 'command'
          ? {
              type: 'command',
              session_id: currentSession.id,
              payload: { text: item.text, metadata: item.metadata },
            }
          : {
              type: 'action',
              session_id: currentSession.id,
              payload: { command: item.command, metadata: item.metadata },
            }
      ws.send(JSON.stringify(request))
    }
  }, [session])

  const enqueue = useCallback((item: QueuedMessage) => {
    queueRef.current.push(item)
  }, [])

  const send = useCallback(
    (item: QueuedMessage) => {
      const ws = wsRef.current
      const currentSession = session
      if (!currentSession || !ws || ws.readyState !== WebSocket.OPEN) {
        enqueue(item)
        return
      }

      const request: CliRequest =
        item.type === 'command'
          ? {
              type: 'command',
              session_id: currentSession.id,
              payload: { text: item.text, metadata: item.metadata },
            }
          : {
              type: 'action',
              session_id: currentSession.id,
              payload: { command: item.command, metadata: item.metadata },
            }
      ws.send(JSON.stringify(request))
    },
    [session, enqueue],
  )

  const connectRef = useRef<(sessionId: string) => void>(() => {})
  const connect = useCallback(
    (sessionId: string) => {
      closeSocket()
      queueRef.current = []
      setStatus('connecting')
      const url = `${WS_BASE}/api/v1/cli/ws/${sessionId}`
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        if (!mountedRef.current) return
        setStatus('open')
        retryCountRef.current = 0
        // Flush any messages that were queued before the connection opened.
        flushQueue()
      }

      ws.onmessage = (event: MessageEvent) => {
        if (!mountedRef.current) return
        try {
          const data = JSON.parse(event.data as string) as CliResponse
          onMessageRef.current?.(data)
          if (data.type === 'card' && data.payload?.card) {
            onCardRef.current?.(data.payload.card)
          }
        } catch {
          // Ignore malformed messages
        }
      }

      ws.onerror = () => {
        if (!mountedRef.current) return
        setStatus('error')
      }

      ws.onclose = () => {
        if (!mountedRef.current) {
          wsRef.current = null
          return
        }
        setStatus('closed')
        wsRef.current = null
        if (retryCountRef.current < MAX_RETRIES) {
          retryCountRef.current += 1
          retryTimeoutRef.current = window.setTimeout(() => {
            retryTimeoutRef.current = null
            connectRef.current(sessionId)
          }, 1000 * retryCountRef.current)
        }
      }
    },
    [closeSocket, flushQueue],
  )
  connectRef.current = connect

  const createSession = useCallback(async () => {
    try {
      const res = await api.post<CliSession>('/v1/cli/sessions', {
        project_id: projectId,
        mode,
      })
      if (!mountedRef.current) return
      setSession(res.data)
      connectRef.current(res.data.id)
    } catch {
      if (!mountedRef.current) return
      setStatus('error')
    }
  }, [projectId, mode])

  useEffect(() => {
    if (!projectId) return
    void createSession()
    return () => {
      closeSocket()
      queueRef.current = []
    }
  }, [projectId, mode, createSession, closeSocket])

  const sendCommand = useCallback(
    (text: string, metadata?: Record<string, unknown>) => {
      send({ type: 'command', text, metadata })
    },
    [send],
  )

  const sendAction = useCallback(
    (command: string, metadata?: Record<string, unknown>) => {
      send({ type: 'action', command, metadata })
    },
    [send],
  )

  const clearSession = useCallback(() => {
    closeSocket()
    setSession(null)
    setStatus('connecting')
    retryCountRef.current = 0
    queueRef.current = []
    void createSession()
  }, [closeSocket, createSession])

  const reconnect = useCallback(() => {
    retryCountRef.current = 0
    queueRef.current = []
    if (session) {
      connectRef.current(session.id)
    } else {
      void createSession()
    }
  }, [session, createSession])

  return {
    session,
    status,
    mode,
    sendCommand,
    sendAction,
    clearSession,
    reconnect,
  }
}
