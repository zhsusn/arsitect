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
const RECONNECT_DELAY_MS = 1000

// Shared state across all hook instances for the same project/mode.
// This prevents React StrictMode double-mount from creating duplicate sessions.
let sharedSession: CliSession | null = null
let sharedWs: WebSocket | null = null
let sharedStatus: SocketStatus = 'connecting'
let sharedRetryCount = 0
let sharedProjectId = ''
let sharedMode: CliMode = 'bug'
let refCount = 0
let connectTimeoutId: number | null = null
let retryTimeoutId: number | null = null

const messageListeners = new Set<(response: CliResponse) => void>()
const cardListeners = new Set<(card: CliCard) => void>()
const statusListeners = new Set<(status: SocketStatus) => void>()
const queue: QueuedMessage[] = []

function notifyMessage(response: CliResponse) {
  messageListeners.forEach((fn) => fn(response))
}

function notifyCard(card: CliCard) {
  cardListeners.forEach((fn) => fn(card))
}

function notifyStatus(status: SocketStatus) {
  sharedStatus = status
  statusListeners.forEach((fn) => fn(status))
}

function flushQueue() {
  const ws = sharedWs
  if (!ws || ws.readyState !== WebSocket.OPEN) return

  while (queue.length > 0) {
    const item = queue.shift()
    if (!item || !sharedSession) continue

    const request: CliRequest =
      item.type === 'command'
        ? {
            type: 'command',
            session_id: sharedSession.id,
            payload: { text: item.text, metadata: item.metadata },
          }
        : {
            type: 'action',
            session_id: sharedSession.id,
            payload: { command: item.command, metadata: item.metadata },
          }
    ws.send(JSON.stringify(request))
  }
}

function closeSocket() {
  if (connectTimeoutId !== null) {
    window.clearTimeout(connectTimeoutId)
    connectTimeoutId = null
  }
  if (retryTimeoutId !== null) {
    window.clearTimeout(retryTimeoutId)
    retryTimeoutId = null
  }
  const ws = sharedWs
  if (ws) {
    ws.onclose = null
    ws.onerror = null
    ws.onmessage = null
    ws.onopen = null
    ws.close()
    sharedWs = null
  }
}

function connect(sessionId: string) {
  closeSocket()
  notifyStatus('connecting')

  const url = `${WS_BASE}/api/v1/cli/ws/${sessionId}`
  const ws = new WebSocket(url)
  sharedWs = ws

  ws.onopen = () => {
    sharedRetryCount = 0
    notifyStatus('open')
    flushQueue()
  }

  ws.onmessage = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data as string) as CliResponse
      notifyMessage(data)
      if (data.type === 'card' && data.payload?.card) {
        notifyCard(data.payload.card)
      }
    } catch {
      // Ignore malformed messages
    }
  }

  ws.onerror = () => {
    notifyStatus('error')
  }

  ws.onclose = () => {
    notifyStatus('closed')
    sharedWs = null
    if (sharedRetryCount < MAX_RETRIES) {
      sharedRetryCount += 1
      retryTimeoutId = window.setTimeout(() => {
        retryTimeoutId = null
        if (sharedSession) {
          connect(sharedSession.id)
        }
      }, RECONNECT_DELAY_MS * sharedRetryCount)
    }
  }
}

async function createSession(projectId: string, mode: CliMode) {
  if (sharedSession && sharedProjectId === projectId && sharedMode === mode) {
    connect(sharedSession.id)
    return
  }

  try {
    const res = await api.post<CliSession>('/v1/cli/sessions', {
      project_id: projectId,
      mode,
    })
    sharedSession = res.data
    sharedProjectId = projectId
    sharedMode = mode
    connect(sharedSession.id)
  } catch {
    notifyStatus('error')
  }
}

function send(item: QueuedMessage) {
  const ws = sharedWs
  if (!sharedSession || !ws || ws.readyState !== WebSocket.OPEN) {
    queue.push(item)
    return
  }

  const request: CliRequest =
    item.type === 'command'
      ? {
          type: 'command',
          session_id: sharedSession.id,
          payload: { text: item.text, metadata: item.metadata },
        }
      : {
          type: 'action',
          session_id: sharedSession.id,
          payload: { command: item.command, metadata: item.metadata },
        }
  ws.send(JSON.stringify(request))
}

export function useCliSession({ projectId, mode, onMessage, onCard }: UseCliSessionOptions): UseCliSessionReturn {
  const [status, setStatus] = useState<SocketStatus>(sharedStatus)
  const onMessageRef = useRef(onMessage)
  const onCardRef = useRef(onCard)

  useEffect(() => {
    onMessageRef.current = onMessage
    onCardRef.current = onCard
  })

  useEffect(() => {
    const handleMessage = (response: CliResponse) => {
      onMessageRef.current?.(response)
    }
    const handleCard = (card: CliCard) => {
      onCardRef.current?.(card)
    }
    const handleStatus = (newStatus: SocketStatus) => {
      setStatus(newStatus)
    }

    messageListeners.add(handleMessage)
    cardListeners.add(handleCard)
    statusListeners.add(handleStatus)
    refCount += 1

    if (!sharedSession || sharedProjectId !== projectId || sharedMode !== mode) {
      // Delay slightly so StrictMode double-mount can reuse the same session.
      connectTimeoutId = window.setTimeout(() => {
        connectTimeoutId = null
        void createSession(projectId, mode)
      }, 0)
    } else if (!sharedWs || sharedWs.readyState !== WebSocket.OPEN) {
      connect(sharedSession.id)
    }

    return () => {
      messageListeners.delete(handleMessage)
      cardListeners.delete(handleCard)
      statusListeners.delete(handleStatus)
      refCount -= 1

      if (connectTimeoutId !== null) {
        window.clearTimeout(connectTimeoutId)
        connectTimeoutId = null
      }

      // Delay closing the shared socket to allow StrictMode remounts to reuse it.
      window.setTimeout(() => {
        if (refCount === 0) {
          closeSocket()
          sharedSession = null
          sharedProjectId = ''
          sharedMode = 'bug'
          sharedRetryCount = 0
          queue.length = 0
        }
      }, 300)
    }
  }, [projectId, mode])

  const sendCommand = useCallback((text: string, metadata?: Record<string, unknown>) => {
    send({ type: 'command', text, metadata })
  }, [])

  const sendAction = useCallback((command: string, metadata?: Record<string, unknown>) => {
    send({ type: 'action', command, metadata })
  }, [])

  const clearSession = useCallback(() => {
    closeSocket()
    sharedSession = null
    sharedProjectId = ''
    sharedMode = 'bug'
    sharedRetryCount = 0
    queue.length = 0
    notifyStatus('connecting')
    void createSession(projectId, mode)
  }, [projectId, mode])

  const reconnect = useCallback(() => {
    sharedRetryCount = 0
    if (sharedSession) {
      connect(sharedSession.id)
    } else {
      void createSession(projectId, mode)
    }
  }, [projectId, mode])

  return {
    session: sharedSession,
    status,
    mode,
    sendCommand,
    sendAction,
    clearSession,
    reconnect,
  }
}
