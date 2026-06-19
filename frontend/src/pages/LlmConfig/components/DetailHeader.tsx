import { FileText, Pencil, Plus } from 'lucide-react'
import { type TabKey } from '../types'

interface DetailHeaderProps {
  mode: 'read' | 'edit' | 'new'
  tab: TabKey
  name?: string
  className?: string
}

export default function DetailHeader({ mode, tab, name, className = '' }: DetailHeaderProps) {
  const label = tab === 'provider' ? 'Provider 节点' : '权限策略'

  let icon: React.ReactNode
  let title: string

  if (mode === 'new') {
    icon = <Plus size={18} />
    title = `新增${label}`
  } else if (mode === 'edit') {
    icon = <Pencil size={18} />
    title = `编辑：${name || label}`
  } else {
    icon = <FileText size={18} />
    title = name || label
  }

  return (
    <div className={`flex items-center gap-2 pb-4 mb-4 border-b border-gray-200 ${className}`}>
      <span className="text-gray-700">{icon}</span>
      <h2 className="text-base font-semibold text-gray-900">{title}</h2>
    </div>
  )
}
