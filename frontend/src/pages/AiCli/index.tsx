import { useCallback, useEffect, useRef, useState } from 'react'
import { Bug, Cpu, MessageSquare, Plus, Send } from 'lucide-react'
import { useChatSession } from '@/components/chat/useChatSession'
import type { ChatCard, ChatMessage, LLMProviderOption, TaskMode } from '@/components/chat/types'
import MessageItem from '@/components/chat/MessageItem'
import { configNodeApi, type ConfigNode } from '@/services/configNode'

const LS_PROJECT_KEY = 'arsitect:lastProjectId'

const MODES: { value: TaskMode; label: string; icon: React.ReactNode }[] = [
  { value: 'free-chat', label: '自由对话', icon: <MessageSquare size={14} /> },
  { value: 'bug', label: 'Bug 修复', icon: <Bug size={14} /> },
  { value: 'arch-fix', label: '架构治理', icon: <Cpu size={14} /> },
]

const FALLBACK_PROVIDERS: { value: LLMProviderOption; label: string }[] = [
  { value: 'kimi-cli', label: 'Kimi CLI' },
  { value: 'kimi-api', label: 'Kimi API' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'arsitect-agent', label: 'Arsitect Agent' },
]

const SKILLS = [
  { id: 'bug', shortcut: '/bug', label: 'Bug 修复', description: '粘贴异常信息或错误描述' },
  { id: 'arch', shortcut: '/arch', label: '架构治理', description: '扫描并修复架构一致性问题' },
  { id: 'fix', shortcut: '/fix', label: '执行修复', description: '应用已生成的修复方案' },
  { id: 'scan', shortcut: '/scan', label: '架构扫描', description: '触发一次架构扫描' },
  { id: 'explain', shortcut: '/explain', label: '解释代码', description: '解释选中的代码片段' },
]

function StatusBadge({ status }: { status: string }) {
  const color =
    status === 'open'
      ? 'bg-green-100 text-green-700 border-green-200'
      : status === 'error'
        ? 'bg-red-100 text-red-700 border-red-200'
        : status === 'closed'
          ? 'bg-gray-100 text-gray-600 border-gray-200'
          : 'bg-amber-100 text-amber-700 border-amber-200'
  const label =
    status === 'open' ? '已连接' : status === 'error' ? '连接失败' : status === 'closed' ? '已断开' : '连接中'
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border ${color}`}>{label}</span>
  )
}

function WelcomeScreen({
  mode,
  onModeChange,
}: {
  mode: TaskMode
  onModeChange: (mode: TaskMode) => void
}) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4">
      <h1 className="text-5xl font-bold tracking-tight text-gray-900 mb-10">AI CLI</h1>
      <div className="flex gap-3 mb-10">
        {MODES.map((m) => (
          <button
            key={m.value}
            type="button"
            onClick={() => onModeChange(m.value)}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border transition-all ${
              mode === m.value
                ? 'bg-gray-900 text-white border-gray-900'
                : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
            }`}
          >
            {m.icon}
            {m.label}
          </button>
        ))}
      </div>
      <div className="text-sm text-gray-400">输入 “/” 可快捷使用技能</div>
    </div>
  )
}

function EmptyState({ mode }: { mode: TaskMode }) {
  const hints: Record<TaskMode, string> = {
    'free-chat': '可以问我关于项目、代码、架构的任何问题',
    bug: '粘贴异常堆栈或错误描述，我将分析根因并给出修复建议',
    'arch-fix': '描述架构问题，或从架构治理中心选择问题进入修复流程',
  }
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 text-center">
      <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
        <MessageSquare className="text-gray-400" size={24} />
      </div>
      <p className="text-gray-500 text-sm max-w-md">{hints[mode]}</p>
    </div>
  )
}

export default function AiCliPage() {
  const [projectId] = useState(() => {
    try {
      return localStorage.getItem(LS_PROJECT_KEY) || 'default'
    } catch {
      return 'default'
    }
  })
  const [mode, setMode] = useState<TaskMode>('free-chat')
  const [provider, setProvider] = useState<LLMProviderOption>('kimi-cli')
  const [providers, setProviders] = useState<ConfigNode[]>([])
  const [providersLoading, setProvidersLoading] = useState(false)
  const [agentMode, setAgentMode] = useState(false)
  const [text, setText] = useState('')
  const [showSkills, setShowSkills] = useState(false)
  const [skillQuery, setSkillQuery] = useState('')
  const [selectedSkillIndex, setSelectedSkillIndex] = useState(0)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const composerRef = useRef<HTMLDivElement>(null)

  const { status, messages, sendCommand, sendAction, clearSession } = useChatSession({
    projectId,
    taskMode: mode,
    llmProvider: provider,
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    let cancelled = false
    setProvidersLoading(true)
    Promise.all([
      configNodeApi.list({ node_type: 'llm_provider', is_enabled: true }),
      configNodeApi.defaultProvider(),
    ])
      .then(([list, defaultConfig]) => {
        if (cancelled) return
        setProviders(list.items)
        const defaultProvider = String(defaultConfig.provider || 'kimi-cli') as LLMProviderOption
        if (defaultProvider) {
          setProvider(defaultProvider)
        }
      })
      .catch((err) => {
        console.error('Failed to load providers:', err)
      })
      .finally(() => {
        if (!cancelled) setProvidersLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const filteredSkills = skillQuery
    ? SKILLS.filter(
        (s) =>
          s.label.toLowerCase().includes(skillQuery.toLowerCase()) ||
          s.shortcut.toLowerCase().includes(skillQuery.toLowerCase()),
      )
    : SKILLS

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [])

  useEffect(() => {
    adjustHeight()
  }, [text, adjustHeight])

  const handleModeChange = useCallback(
    (newMode: TaskMode) => {
      setMode(newMode)
      clearSession(newMode, provider)
    },
    [clearSession, provider],
  )

  const handleProviderChange = useCallback(
    (newProvider: LLMProviderOption) => {
      setProvider(newProvider)
      clearSession(mode, newProvider)
    },
    [clearSession, mode],
  )

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setText(value)

    const cursorPosition = e.target.selectionStart
    const lastSlashIndex = value.lastIndexOf('/', cursorPosition)

    if (lastSlashIndex !== -1 && lastSlashIndex === 0 && cursorPosition <= value.length) {
      const query = value.slice(lastSlashIndex + 1, cursorPosition)
      const charBeforeSlash = value[lastSlashIndex - 1]
      if (!charBeforeSlash || /\s/.test(charBeforeSlash)) {
        setSkillQuery(query)
        setShowSkills(true)
        setSelectedSkillIndex(0)
        return
      }
    }
    setShowSkills(false)
  }

  const insertSkill = (skill: (typeof SKILLS)[0]) => {
    const el = textareaRef.current
    if (!el) return
    const cursorPosition = el.selectionStart
    const lastSlashIndex = text.lastIndexOf('/', cursorPosition)
    if (lastSlashIndex === -1) return

    const before = text.slice(0, lastSlashIndex)
    const after = text.slice(cursorPosition)
    const newText = `${before}${skill.shortcut} ${after}`
    setText(newText)
    setShowSkills(false)
    setTimeout(() => {
      el.focus()
      const newCursor = lastSlashIndex + skill.shortcut.length + 1
      el.setSelectionRange(newCursor, newCursor)
    }, 0)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (showSkills && filteredSkills.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedSkillIndex((i) => (i + 1) % filteredSkills.length)
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedSkillIndex(
          (i) => (i - 1 + filteredSkills.length) % filteredSkills.length,
        )
        return
      }
      if (e.key === 'Enter') {
        e.preventDefault()
        insertSkill(filteredSkills[selectedSkillIndex])
        return
      }
      if (e.key === 'Escape') {
        setShowSkills(false)
        return
      }
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const canSend = text.trim().length > 0 && status !== 'error' && status !== 'closed'

  const handleSubmit = () => {
    const trimmed = text.trim()
    if (!canSend) return
    sendCommand(trimmed, { provider, agent_mode: agentMode })
    setText('')
    setShowSkills(false)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleCardAction = useCallback(
    (command: string, _card: ChatCard, metadata?: Record<string, unknown>) => {
      sendAction(command, metadata)
    },
    [sendAction],
  )

  const handlePaste = useCallback(async () => {
    try {
      const clipboardText = await navigator.clipboard.readText()
      setText(clipboardText)
      adjustHeight()
    } catch {
      // ignore
    }
  }, [adjustHeight])

  const hasMessages = messages.length > 0

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
        <div className="flex items-center gap-2">
          {MODES.map((m) => (
            <button
              key={m.value}
              type="button"
              onClick={() => handleModeChange(m.value)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                mode === m.value
                  ? 'bg-gray-900 text-white border-gray-900'
                  : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
              }`}
            >
              {m.icon}
              {m.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={status} />
          <button
            type="button"
            onClick={() => clearSession()}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded hover:bg-gray-100"
            title="新会话"
          >
            <Plus size={14} />
            新会话
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden flex flex-col relative">
        {!hasMessages ? (
          mode === 'free-chat' ? (
            <WelcomeScreen mode={mode} onModeChange={handleModeChange} />
          ) : (
            <EmptyState mode={mode} />
          )
        ) : (
          <div className="flex-1 overflow-y-auto px-4 py-6">
            <div className="max-w-[1400px] mx-auto space-y-5">
              {messages.map((message: ChatMessage) => (
                <MessageItem
                  key={message.id}
                  message={message}
                  onCardAction={handleCardAction}
                  onCopy={(copyText) => void navigator.clipboard.writeText(copyText)}
                />
              ))}
              <div ref={bottomRef} />
            </div>
          </div>
        )}
      </div>

      {/* Composer */}
      <div className="p-4 bg-white border-t border-gray-200">
        <div className="max-w-[1400px] mx-auto">
          <div
            ref={composerRef}
            className="relative rounded-3xl border border-gray-200 bg-white shadow-sm focus-within:ring-2 focus-within:ring-gray-100 focus-within:border-gray-300 transition-all"
          >
            {showSkills && (
              <div className="absolute bottom-full left-0 mb-2 w-64 rounded-xl border border-gray-200 bg-white shadow-lg py-1 z-10">
                {filteredSkills.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-gray-400">无匹配技能</div>
                ) : (
                  filteredSkills.map((skill, index) => (
                    <button
                      key={skill.id}
                      type="button"
                      onClick={() => insertSkill(skill)}
                      className={`w-full text-left px-3 py-2 hover:bg-gray-50 transition-colors ${
                        index === selectedSkillIndex ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="text-sm font-medium text-gray-800">
                        {skill.shortcut} {skill.label}
                      </div>
                      {skill.description && (
                        <div className="text-xs text-gray-500 mt-0.5">{skill.description}</div>
                      )}
                    </button>
                  ))
                )}
              </div>
            )}

            <textarea
              ref={textareaRef}
              value={text}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              rows={1}
              className="w-full resize-none bg-transparent px-5 py-4 text-sm text-gray-800 placeholder-gray-400 outline-none min-h-[60px] max-h-[200px]"
              placeholder="输入“/”可快捷使用技能"
            />

            <div className="flex items-center justify-between px-3 pb-3">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handlePaste}
                  className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 text-gray-500 disabled:opacity-50"
                  title="粘贴剪贴板"
                >
                  <Plus size={18} />
                </button>

                <button
                  type="button"
                  onClick={() => setAgentMode((v) => !v)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                    agentMode
                      ? 'bg-blue-50 border-blue-200 text-blue-700'
                      : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Cpu size={14} />
                  <span>Agent</span>
                </button>
              </div>

              <div className="flex items-center gap-2">
                <select
                  value={provider}
                  disabled={providersLoading}
                  onChange={(e) => handleProviderChange(e.target.value as LLMProviderOption)}
                  className="text-xs text-gray-600 bg-transparent border-none outline-none cursor-pointer disabled:opacity-50"
                >
                  {(providers.length > 0
                    ? providers.map((n) => ({
                        value: String(n.config_json.provider || n.key) as LLMProviderOption,
                        label: n.name,
                      }))
                    : FALLBACK_PROVIDERS
                  ).map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label}
                    </option>
                  ))}
                </select>

                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={!canSend}
                  className="w-9 h-9 flex items-center justify-center rounded-full bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-40 disabled:bg-gray-300 transition-colors"
                >
                  <Send size={16} />
                </button>
              </div>
            </div>
          </div>
          <div className="text-center mt-2 text-xs text-gray-400">
            AI 生成内容仅供参考，请仔细甄别
          </div>
        </div>
      </div>
    </div>
  )
}
