import { useState } from 'react'
import type { SkillConflict, ConflictResolution } from '../../../stores/skillRegistryStore'

interface ConflictResolveModalProps {
  conflicts: SkillConflict[]
  onResolve: (resolutions: ConflictResolution[]) => void
  onClose: () => void
}

export function ConflictResolveModal({ conflicts, onResolve, onClose }: ConflictResolveModalProps) {
  const [resolutions, setResolutions] = useState<Record<string, ConflictResolution>>(() => {
    const initial: Record<string, ConflictResolution> = {}
    conflicts.forEach((c) => {
      initial[c.new_skill.skill_name] = {
        skill_name: c.new_skill.skill_name,
        action: 'skip',
        new_name: null,
      }
    })
    return initial
  })
  const [renameMap, setRenameMap] = useState<Record<string, string>>({})
  const [currentIndex, setCurrentIndex] = useState(0)

  const currentConflict = conflicts[currentIndex]

  const setAction = (skillName: string, action: string) => {
    setResolutions((prev) => ({
      ...prev,
      [skillName]: {
        ...prev[skillName],
        action,
        new_name: action === 'rename' ? (renameMap[skillName] || `${skillName}_new`) : null,
      },
    }))
  }

  const setRename = (skillName: string, newName: string) => {
    setRenameMap((prev) => ({ ...prev, [skillName]: newName }))
    setResolutions((prev) => ({
      ...prev,
      [skillName]: {
        ...prev[skillName],
        new_name: newName,
      },
    }))
  }

  const handleAllAction = (action: string) => {
    const next: Record<string, ConflictResolution> = {}
    conflicts.forEach((c) => {
      next[c.new_skill.skill_name] = {
        skill_name: c.new_skill.skill_name,
        action,
        new_name: action === 'rename' ? `${c.new_skill.skill_name}_new` : null,
      }
    })
    setResolutions(next)
  }

  const handleConfirm = () => {
    onResolve(Object.values(resolutions))
  }

  const isLast = currentIndex >= conflicts.length - 1

  return (
    <div
      className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-2xl w-[680px] max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Skill 导入冲突</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              发现 {conflicts.length} 个同名 Skill，请处理冲突
              {conflicts.length > 1 && ` (${currentIndex + 1}/${conflicts.length})`}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleAllAction('overwrite')}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-50 text-amber-700 hover:bg-amber-100 transition-colors"
            >
              全部覆盖
            </button>
            <button
              onClick={() => handleAllAction('skip')}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-50 text-gray-700 hover:bg-gray-100 transition-colors"
            >
              全部跳过
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto px-6 py-4">
          {conflicts.length > 1 && (
            <div className="flex gap-1.5 mb-4 overflow-x-auto pb-1">
              {conflicts.map((c, idx) => (
                <button
                  key={c.new_skill.skill_name}
                  onClick={() => setCurrentIndex(idx)}
                  className={`
                    px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors
                    ${idx === currentIndex
                      ? 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200'
                      : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                    }
                    ${resolutions[c.new_skill.skill_name]?.action === 'overwrite'
                      ? 'border-amber-300 border'
                      : resolutions[c.new_skill.skill_name]?.action === 'skip'
                        ? 'border-gray-300 border'
                        : resolutions[c.new_skill.skill_name]?.action === 'rename'
                          ? 'border-blue-300 border'
                          : ''
                    }
                  `}
                >
                  {c.new_skill.skill_name}
                </button>
              ))}
            </div>
          )}

          {currentConflict && (
            <div className="space-y-4">
              {/* Comparison */}
              <div className="grid grid-cols-2 gap-4">
                {/* Existing */}
                <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
                    现有 Skill
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex">
                      <span className="text-gray-500 w-14 shrink-0">名称</span>
                      <span className="text-gray-900 font-medium">
                        {currentConflict.existing_skill?.skill_name || '-'}
                      </span>
                    </div>
                    <div className="flex">
                      <span className="text-gray-500 w-14 shrink-0">版本</span>
                      <span className="text-gray-900">
                        {currentConflict.existing_skill?.version || '-'}
                      </span>
                    </div>
                    <div className="flex">
                      <span className="text-gray-500 w-14 shrink-0">更新于</span>
                      <span className="text-gray-900">
                        {currentConflict.existing_skill?.updated_at
                          ? new Date(currentConflict.existing_skill.updated_at).toLocaleString()
                          : '-'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* New */}
                <div className="p-4 bg-indigo-50/50 rounded-xl border border-indigo-100">
                  <div className="text-xs font-medium text-indigo-600 uppercase tracking-wider mb-3">
                    新导入 Skill
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex">
                      <span className="text-gray-500 w-14 shrink-0">名称</span>
                      <span className="text-gray-900 font-medium">
                        {currentConflict.new_skill.skill_name}
                      </span>
                    </div>
                    <div className="flex">
                      <span className="text-gray-500 w-14 shrink-0">版本</span>
                      <span
                        className={`
                          ${currentConflict.existing_skill &&
                            currentConflict.existing_skill.version !== currentConflict.new_skill.version
                            ? 'text-amber-700 font-medium bg-amber-100 px-1.5 py-0.5 rounded'
                            : 'text-gray-900'
                          }
                        `}
                      >
                        {currentConflict.new_skill.version}
                      </span>
                    </div>
                    <div className="flex">
                      <span className="text-gray-500 w-14 shrink-0">路径</span>
                      <span className="text-gray-900 truncate">
                        {currentConflict.new_skill.directory_path}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Diff Highlight */}
              {currentConflict.existing_skill &&
                currentConflict.existing_skill.version !== currentConflict.new_skill.version && (
                <div className="flex items-center gap-3 p-3 bg-amber-50 rounded-lg border border-amber-100">
                  <svg className="w-5 h-5 text-amber-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span className="text-sm text-amber-800">
                    版本号不同：现有 <strong>{currentConflict.existing_skill.version}</strong> → 新导入 <strong>{currentConflict.new_skill.version}</strong>
                  </span>
                </div>
              )}

              {/* Actions */}
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">处理方式</div>
                <div className="flex gap-2">
                  {(['overwrite', 'skip', 'rename'] as const).map((action) => (
                    <button
                      key={action}
                      onClick={() => setAction(currentConflict.new_skill.skill_name, action)}
                      className={`
                        flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-all
                        ${resolutions[currentConflict.new_skill.skill_name]?.action === action
                          ? action === 'overwrite'
                            ? 'bg-amber-100 text-amber-800 ring-2 ring-amber-300'
                            : action === 'skip'
                              ? 'bg-gray-200 text-gray-800 ring-2 ring-gray-300'
                              : 'bg-blue-100 text-blue-800 ring-2 ring-blue-300'
                          : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                        }
                      `}
                    >
                      {action === 'overwrite' && '覆盖'}
                      {action === 'skip' && '跳过'}
                      {action === 'rename' && '重命名'}
                    </button>
                  ))}
                </div>

                {resolutions[currentConflict.new_skill.skill_name]?.action === 'rename' && (
                  <div className="mt-3">
                    <label className="text-xs text-gray-500 mb-1 block">新名称</label>
                    <input
                      type="text"
                      value={renameMap[currentConflict.new_skill.skill_name] || `${currentConflict.new_skill.skill_name}_new`}
                      onChange={(e) => setRename(currentConflict.new_skill.skill_name, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 flex justify-between items-center">
          <div className="text-xs text-gray-500">
            已处理 {Object.values(resolutions).filter((r) => r.action !== 'skip' || conflicts.find((c) => c.new_skill.skill_name === r.skill_name)).length} / {conflicts.length}
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              取消
            </button>
            {conflicts.length > 1 && !isLast && (
              <button
                onClick={() => setCurrentIndex((i) => i + 1)}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
              >
                下一个
              </button>
            )}
            {(isLast || conflicts.length === 1) && (
              <button
                onClick={handleConfirm}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
              >
                确认导入
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
