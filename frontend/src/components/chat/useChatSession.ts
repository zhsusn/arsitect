import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '@/services/api'
import type {
  ChatCard,
  ChatMessage,
  ChatSession,
  ChatSessionCreateResponse,
  ClientMessage,
  ServerMessage,
  SocketStatus,
} from './types'

const WS_SCHEME = window.location.protocol === 'https:' ? 'wss' : 'ws'
const WS_BASE = `${WS_SCHEME}://${window.location.host}/ws`

export interface UseChatSessionOptions {
  projectId: string
  sessionId?: string
  taskMode?: string
  llmProvider?: string
  onMessage?: (message: ChatMessage) => void
  onCard?: (card: ChatCard) => void
}

export interface UseChatSessionReturn {
  session: ChatSession | null
  status: SocketStatus
  messages: ChatMessage[]
  sendCommand: (text: string, metadata?: Record<string, unknown>) => void
  sendAction: (command: string, metadata?: Record<string, unknown>) => void
  clearSession: (newTaskMode?: string, newLlmProvider?: string) => void
  reconnect: () => void
}

interface QueuedMessage {
  type: 'command' | 'action'
  text?: string
  command?: string
  metadata?: Record<string, unknown>
}

const MAX_RETRIES = 3
const RECONNECT_DELAY_MS = 1000

function generateMessageId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function serverMessageToChatMessage(msg: ServerMessage): ChatMessage | null {
  const base: ChatMessage = {
    id: generateMessageId(),
    session_id: msg.session_id,
    role: 'system',
    created_at: new Date(msg.timestamp).toISOString(),
    status: 'done',
  }

  switch (msg.type) {
    case 'text':
      return {
        ...base,
        role: 'ai',
        content: msg.payload?.text || '',
      }
    case 'thinking':
      return {
        ...base,
        role: 'thinking',
        content: msg.payload?.text || '',
      }
    case 'card':
      if (!msg.payload?.card) return null
      return {
        ...base,
        role: 'ai',
        card: msg.payload.card,
      }
    case 'progress':
      return {
        ...base,
        role: 'system',
        content: msg.payload?.progress
          ? `${msg.payload.progress.label || '进度'} ${msg.payload.progress.current}/${msg.payload.progress.total}`
          : '处理中...',
        metadata: { progress: msg.payload?.progress },
      }
    case 'error':
      return {
        ...base,
        role: 'system',
        content: msg.payload?.error?.message || '未知错误',
        metadata: { error: msg.payload?.error },
      }
    case 'done':
      return {
        ...base,
        role: 'system',
        content: '任务完成',
      }
    default:
      return null
  }
}

export function useChatSession({
  projectId,
  sessionId: initialSessionId,
  taskMode,
  llmProvider,
  onMessage,
  onCard,
}: UseChatSessionOptions): UseChatSessionReturn {
  const [session, setSession] = useState<ChatSession | null>(null)
  const [status, setStatus] = useState<SocketStatus>('connecting')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const retryCountRef = useRef(0)
  const queueRef = useRef<QueuedMessage[]>([])
  const sessionRef = useRef(session)
  const onMessageRef = useRef(onMessage)
  const onCardRef = useRef(onCard)
  const currentSessionIdRef = useRef<string | undefined>(initialSessionId)
  const currentProjectIdRef = useRef(projectId)
  const taskModeRef = useRef(taskMode)
  const llmProviderRef = useRef(llmProvider)
  const initializedRef = useRef(false)
  const createGenerationRef = useRef(0)

  useEffect(() => {
    sessionRef.current = session
  }, [session])

  useEffect(() => {
    onMessageRef.current = onMessage
    onCardRef.current = onCard
  })

  useEffect(() => {
    taskModeRef.current = taskMode
  }, [taskMode])

  useEffect(() => {
    llmProviderRef.current = llmProvider
  }, [llmProvider])

  const appendMessage = useCallback((msg: ChatMessage) => {
    setMessages((prev) => {
      // Merge consecutive thinking chunks from the same streaming response.
      if (msg.role === 'thinking' && prev.length > 0) {
        const last = prev[prev.length - 1]
        if (last.role === 'thinking' && last.status === 'streaming') {
          const updated: ChatMessage = {
            ...last,
            content: (last.content || '') + (msg.content || ''),
          }
          return [...prev.slice(0, -1), updated]
        }
      }
      return [...prev, msg]
    })
    onMessageRef.current?.(msg)
    if (msg.card) {
      onCardRef.current?.(msg.card)
    }
  }, [])

  const closeSocket = useCallback(() => {
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
    const currentSession = sessionRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN || !currentSession) return

    while (queueRef.current.length > 0) {
      const item = queueRef.current.shift()
      if (!item) continue

      const request: ClientMessage =
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
  }, [])

  const connect = useCallback(
    (sid: string) => {
      closeSocket()
      setStatus('connecting')

      const url = `${WS_BASE}/api/v1/chat/ws/${sid}`
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        retryCountRef.current = 0
        setStatus('open')
        flushQueue()
      }

      ws.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data as string) as ServerMessage
          const chatMsg = serverMessageToChatMessage(data)
          if (chatMsg) {
            appendMessage(chatMsg)
          }
        } catch {
          // Ignore malformed messages
        }
      }

      ws.onerror = () => {
        setStatus('error')
      }

      ws.onclose = () => {
        setStatus('closed')
        wsRef.current = null
        if (retryCountRef.current < MAX_RETRIES) {
          retryCountRef.current += 1
          window.setTimeout(() => {
            if (currentSessionIdRef.current) {
              connect(currentSessionIdRef.current)
            }
          }, RECONNECT_DELAY_MS * retryCountRef.current)
        }
      }
    },
    [closeSocket, flushQueue, appendMessage],
  )

  const createSession = useCallback(async () => {
    createGenerationRef.current += 1
    const generation = createGenerationRef.current
    try {
      const res = await api.post<ChatSessionCreateResponse>('/v1/chat/sessions', {
        project_id: projectId,
        task_mode: taskModeRef.current || 'free-chat',
        llm_provider: llmProviderRef.current,
      })
      // Ignore stale responses if clearSession/reconnect started a newer creation.
      if (generation !== createGenerationRef.current) return
      const newSession = res.data.session
      setSession(newSession)
      currentSessionIdRef.current = newSession.id
      connect(newSession.id)
    } catch {
      if (generation === createGenerationRef.current) {
        setStatus('error')
      }
    }
  }, [projectId, connect])

  useEffect(() => {
    currentProjectIdRef.current = projectId
  }, [projectId])

  useEffect(() => {
    if (initializedRef.current) return
    initializedRef.current = true

    if (initialSessionId) {
      // TODO: fetch session metadata and history
      currentSessionIdRef.current = initialSessionId
      connect(initialSessionId)
    } else {
      void createSession()
    }

    return () => {
      closeSocket()
    }
  }, [initialSessionId, createSession, connect, closeSocket])

  const send = useCallback((item: QueuedMessage) => {
    const ws = wsRef.current
    const currentSession = sessionRef.current
    if (!currentSession || !ws || ws.readyState !== WebSocket.OPEN) {
      queueRef.current.push(item)
      return
    }

    const request: ClientMessage =
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
  }, [])

  const sendCommand = useCallback(
    (text: string, metadata?: Record<string, unknown>) => {
      const userMsg: ChatMessage = {
        id: generateMessageId(),
        session_id: sessionRef.current?.id || '',
        role: 'user',
        content: text,
        metadata,
        created_at: new Date().toISOString(),
        status: 'done',
      }
      appendMessage(userMsg)
      send({ type: 'command', text, metadata })
    },
    [send, appendMessage],
  )

  const sendAction = useCallback(
    (command: string, metadata?: Record<string, unknown>) => {
      send({ type: 'action', command, metadata })
    },
    [send],
  )

  const clearSession = useCallback(
    (newTaskMode?: string, newLlmProvider?: string) => {
      if (newTaskMode !== undefined) {
        taskModeRef.current = newTaskMode
      }
      if (newLlmProvider !== undefined) {
        llmProviderRef.current = newLlmProvider
      }
      // Bump generation so any in-flight createSession result is discarded.
      createGenerationRef.current += 1
      closeSocket()
      setSession(null)
      setMessages([])
      retryCountRef.current = 0
      queueRef.current = []
      currentSessionIdRef.current = undefined
      setStatus('connecting')
      void createSession()
    },
    [closeSocket, createSession],
  )

  const reconnect = useCallback(() => {
    retryCountRef.current = 0
    if (currentSessionIdRef.current) {
      connect(currentSessionIdRef.current)
    } else {
      void createSession()
    }
  }, [connect, createSession])

  return {
    session,
    status,
    messages,
    sendCommand,
    sendAction,
    clearSession,
    reconnect,
  }
}
