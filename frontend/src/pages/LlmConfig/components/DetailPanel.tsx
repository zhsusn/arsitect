import type { LlmPolicy, LlmProvider } from '../../../services/llm'
import { isProvider, type TabKey } from '../types'
import PermissionDetail from './PermissionDetail'
import ProviderDetail from './ProviderDetail'

interface DetailPanelProps {
  tab: TabKey
  node: LlmProvider | LlmPolicy | null
  isNew: boolean
  onSaved: () => void
  onCancel: () => void
  onDeleted: () => void
  onMarkUnsaved?: () => void
}

export default function DetailPanel({
  tab,
  node,
  isNew,
  onSaved,
  onCancel,
  onDeleted,
  onMarkUnsaved,
}: DetailPanelProps) {
  if (!node) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-400 p-8">
        <div className="text-sm">在左侧选择一项查看详情</div>
        <div className="text-xs mt-2">或点击「新增」创建配置节点</div>
      </div>
    )
  }

  if (tab === 'provider' && isProvider(node)) {
    return (
      <ProviderDetail
        provider={node}
        isNew={isNew}
        onSaved={onSaved}
        onCancel={onCancel}
        onDeleted={onDeleted}
        onMarkUnsaved={onMarkUnsaved}
      />
    )
  }

  return (
    <PermissionDetail
      policy={node as LlmPolicy}
      isNew={isNew}
      onSaved={onSaved}
      onCancel={onCancel}
      onDeleted={onDeleted}
      onMarkUnsaved={onMarkUnsaved}
    />
  )
}
