import { useCallback, useEffect, useRef, useState } from 'react'
import { Cpu, Plus, Send } from 'lucide-react'
import type { LLMProviderOption, SkillOption } from './types'

const SKILLS: SkillOption[] = [
  { id: 'bug', label: 'Bug 修复', description: '粘贴异常信息或错误描述', shortcut: '/bug' },
  { id: 'arch', label: '架构治理', description: '扫描并修复架构一致性问题', shortcut: '/arch' },
  { id: 'fix', label: '执行修复', description: '应用已生成的修复方案', shortcut: '/fix' },
  { id: 'scan', label: '架构扫描', description: '触发一次架构扫描', shortcut: '/scan' },
  { id: 'explain', label: '解释代码', description: '解释选中的代码片段', shortcut: '/explain' },
]

const PROVIDERS: { value: LLMProviderOption; label: string }[] = [
  { value: 'kimi-cli', label: 'Kimi CLI' },
  { value: 'kimi-api', label: 'Kimi API' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'arsitect-agent', label: 'Arsitect Agent' },
]

interface ChatComposerProps {
  placeholder?: string
  disabled?: boolean
  provider?: LLMProviderOption
  agentMode?: boolean
  onSend: (text: string, metadata?: Record<string, unknown>) => void
  onProviderChange?: (provider: LLMProviderOption) => void
  onAgentModeChange?: (enabled: boolean) => void
}

export default function ChatComposer({
  placeholder = '输入“/”可快捷使用技能',
  disabled = false,
  provider = 'kimi-cli',
  agentMode = false,
  onSend,
  onProviderChange,
  onAgentModeChange,
}: ChatComposerProps) {
  const [text, setText] = useState('')
  const [showSkills, setShowSkills] = useState(false)
  const [skillQuery, setSkillQuery] = useState('')
  const [selectedSkillIndex, setSelectedSkillIndex] = useState(0)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

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

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setText(value)

    const cursorPosition = e.target.selectionStart
    const lastSlashIndex = value.lastIndexOf('/', cursorPosition)

    if (lastSlashIndex !== -1 && lastSlashIndex === 0 && cursorPosition <= value.length) {
      const query = value.slice(lastSlashIndex + 1, cursorPosition)
      // Only show skill panel if slash is at start or after whitespace
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

  const insertSkill = (skill: SkillOption) => {
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
        setSelectedSkillIndex((i) => (i - 1 + filteredSkills.length) % filteredSkills.length)
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

  const handleSubmit = () => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    setShowSkills(false)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  return (
    <div className="relative rounded-2xl border border-gray-200 bg-white shadow-sm focus-within:ring-2 focus-within:ring-blue-100 focus-within:border-blue-300 transition-all">
      {showSkills && (
        <div className="absolute bottom-full left-0 mb-2 w-64 rounded-lg border border-gray-200 bg-white shadow-lg py-1 z-10">
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
        className="w-full resize-none bg-transparent px-4 py-3 text-sm text-gray-800 placeholder-gray-400 outline-none min-h-[56px] max-h-[200px]"
        placeholder={placeholder}
      />

      <div className="flex items-center justify-between px-3 pb-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={disabled}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 text-gray-500 disabled:opacity-50"
            title="添加附件（MVP 占位）"
          >
            <Plus size={18} />
          </button>

          <button
            type="button"
            onClick={() => onAgentModeChange?.(!agentMode)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
              agentMode
                ? 'bg-blue-50 border-blue-200 text-blue-700'
                : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
            } disabled:opacity-50`}
          >
            <Cpu size={14} />
            <span>Agent</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={provider}
            onChange={(e) => onProviderChange?.(e.target.value as LLMProviderOption)}
            disabled={disabled}
            className="text-xs text-gray-600 bg-transparent border-none outline-none cursor-pointer disabled:opacity-50"
          >
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={disabled || !text.trim()}
            className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-40 disabled:bg-gray-300 transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}
