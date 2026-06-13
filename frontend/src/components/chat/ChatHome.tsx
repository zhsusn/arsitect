import { useState } from 'react'
import ChatComposer from './ChatComposer'
import type { LLMProviderOption } from './types'

interface ChatHomeProps {
  logoText?: string
  placeholder?: string
  onSend: (text: string, provider: LLMProviderOption, agentMode: boolean) => void
}

export default function ChatHome({
  logoText = 'ARSITECT',
  placeholder = '输入“/”可快捷使用技能',
  onSend,
}: ChatHomeProps) {
  const [provider, setProvider] = useState<LLMProviderOption>('kimi-cli')
  const [agentMode, setAgentMode] = useState(false)

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4">
      <h1 className="text-5xl font-black tracking-widest text-gray-900 mb-10">{logoText}</h1>
      <div className="w-full max-w-3xl">
        <ChatComposer
          placeholder={placeholder}
          provider={provider}
          agentMode={agentMode}
          onSend={(text) => onSend(text, provider, agentMode)}
          onProviderChange={setProvider}
          onAgentModeChange={setAgentMode}
        />
      </div>
    </div>
  )
}
