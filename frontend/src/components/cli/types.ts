export type CliMode = 'bug' | 'arch'

export type SocketStatus = 'connecting' | 'open' | 'closed' | 'error'

export interface CliSession {
  id: string
  project_id: string
  user_id: string
  mode: CliMode
  status: 'active' | 'paused' | 'closed'
  created_at: string
  closed_at?: string | null
}

export interface CliCardAction {
  label: string
  command: string
  style?: 'primary' | 'danger' | 'default'
}

export interface CliCard {
  type: 'bug-report' | 'fix-proposal' | 'arch-decision' | 'progress' | 'confirm'
  data: Record<string, unknown>
  actions: CliCardAction[]
}

export interface CliMessage {
  id: string
  session_id: string
  message_type: 'user' | 'ai' | 'system' | 'error' | 'success' | 'card' | 'progress' | 'thinking'
  content?: string | null
  card_data?: CliCard | null
  metadata?: Record<string, unknown> | null
  sequence_no: number
  created_at: string
}

export interface ErrorResponse {
  code: string
  message: string
  detail?: Record<string, unknown> | null
}

export interface CliRequest {
  type: 'command' | 'input' | 'action' | 'abort' | 'ping'
  session_id: string
  payload?: {
    text?: string
    command?: string
    actionType?: string
    metadata?: Record<string, unknown>
  }
}

export interface CliResponse {
  type: 'text' | 'card' | 'progress' | 'error' | 'done' | 'prompt' | 'pong' | 'thinking'
  session_id: string
  payload?: {
    text?: string
    card?: CliCard
    progress?: {
      current: number
      total: number
      label?: string
    }
    error?: ErrorResponse
  }
  timestamp: number
}
