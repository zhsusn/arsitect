export type ChatRole = 'user' | 'ai' | 'system' | 'thinking'

export type MessageStatus = 'sending' | 'streaming' | 'done' | 'error'

export interface ChatAttachment {
  type: 'file' | 'image' | 'code-snippet'
  name: string
  content?: string
}

export interface ChatCardAction {
  label: string
  command: string
  style?: 'primary' | 'danger' | 'default'
}

export interface ChatCard {
  type: 'fix-proposal' | 'arch-decision' | 'confirm' | 'progress' | 'bug-report'
  title: string
  description?: string
  data: Record<string, unknown>
  actions: ChatCardAction[]
}

export interface ChatMessage {
  id: string
  session_id: string
  role: ChatRole
  content?: string
  card?: ChatCard
  attachments?: ChatAttachment[]
  metadata?: Record<string, unknown>
  created_at: string
  status: MessageStatus
}

export type SocketStatus = 'connecting' | 'open' | 'closed' | 'error'

export type ServerMessageType =
  | 'text'
  | 'thinking'
  | 'card'
  | 'progress'
  | 'error'
  | 'done'
  | 'prompt'
  | 'pong'

export interface ServerProgressPayload {
  current: number
  total: number
  label?: string
}

export interface ServerErrorPayload {
  code: string
  message: string
  detail?: Record<string, unknown>
}

export interface ServerMessage {
  type: ServerMessageType
  session_id: string
  timestamp: number
  payload?: {
    text?: string
    card?: ChatCard
    progress?: ServerProgressPayload
    error?: ServerErrorPayload
  }
}

export type ClientMessageType = 'command' | 'input' | 'action' | 'abort' | 'ping'

export interface ClientMessage {
  type: ClientMessageType
  session_id: string
  payload?: {
    text?: string
    command?: string
    actionType?: string
    metadata?: Record<string, unknown>
  }
}

export interface ChatSession {
  id: string
  project_id: string
  user_id: string
  mode: string
  task_mode: string
  llm_provider?: string
  status: 'active' | 'paused' | 'closed'
  created_at: string
  closed_at?: string | null
}

export type TaskMode = 'free-chat' | 'bug' | 'arch-fix'

export type LLMProviderOption = 'kimi-cli' | 'kimi-api' | 'openai' | 'arsitect-agent'

export interface SkillOption {
  id: string
  label: string
  description?: string
  shortcut: string
}

export interface ChatSessionCreateResponse {
  session: ChatSession
  messages: ChatMessage[]
  history: ChatMessage[]
}
