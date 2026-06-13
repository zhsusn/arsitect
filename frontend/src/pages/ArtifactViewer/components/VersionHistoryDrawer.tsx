import { useState } from 'react'
import type { ArtifactVersion } from '../../../stores/artifactViewerStore'
import DiffViewerModal from './DiffViewerModal'
import RollbackConfirmDialog from './RollbackConfirmDialog'

interface VersionHistoryDrawerProps {
  versions: ArtifactVersion[]
  onRollback: (versionNumber: number, backupCurrent: boolean) => void
  currentVersion: number
}

export default function VersionHistoryDrawer({
  versions,
  onRollback,
  currentVersion,
}: VersionHistoryDrawerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedVersions, setSelectedVersions] = useState<number[]>([])
  const [showDiff, setShowDiff] = useState(false)
  const [rollbackTarget, setRollbackTarget] = useState<number | null>(null)

  const toggleVersion = (versionNumber: number) => {
    setSelectedVersions((prev) => {
      if (prev.includes(versionNumber)) {
        return prev.filter((v) => v !== versionNumber)
      }
      if (prev.length >= 2) {
        return [prev[1], versionNumber]
      }
      return [...prev, versionNumber]
    })
  }

  const [fromVersion, toVersion] =
    selectedVersions.length === 2
      ? [Math.min(...selectedVersions), Math.max(...selectedVersions)]
      : [null, null]

  const fromContent = versions.find((v) => v.version_number === fromVersion)?.content || ''
  const toContent = versions.find((v) => v.version_number === toVersion)?.content || ''
  const rollbackVersionInfo = versions.find((v) => v.version_number === rollbackTarget)

  const handleRollbackClick = (versionNumber: number, e: React.MouseEvent) => {
    e.stopPropagation()
    setRollbackTarget(versionNumber)
  }

  const handleConfirmRollback = (backupCurrent: boolean) => {
    if (rollbackTarget !== null) {
      onRollback(rollbackTarget, backupCurrent)
    }
    setRollbackTarget(null)
  }

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-gray-100"
      >
        版本历史
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex">
          <div className="flex-1 bg-black/30" onClick={() => setIsOpen(false)} />
          <div className="w-96 bg-white shadow-xl flex flex-col h-full">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
              <h3 className="font-semibold text-gray-800">版本历史</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-auto p-4">
              <div className="mb-4 text-sm text-gray-500">
                当前版本: <span className="font-medium text-gray-800">v{currentVersion}</span>
              </div>

              {versions.length === 0 ? (
                <div className="text-center text-gray-400 py-8">暂无版本记录</div>
              ) : (
                <div className="space-y-2">
                  {versions.map((version) => (
                    <div
                      key={version.version_id}
                      className={`p-3 rounded border cursor-pointer transition-colors ${
                        selectedVersions.includes(version.version_number)
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                      onClick={() => toggleVersion(version.version_number)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-sm">v{version.version_number}</span>
                        <span
                          className={`text-xs px-1.5 py-0.5 rounded ${
                            version.operation_type === 'rollback'
                              ? 'bg-orange-100 text-orange-600'
                              : 'bg-green-100 text-green-600'
                          }`}
                        >
                          {version.operation_type === 'rollback' ? '回滚' : '快照'}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        {version.created_by || '系统'} · {new Date(version.created_at).toLocaleString()}
                      </div>
                      {version.version_number !== currentVersion && (
                        <button
                          onClick={(e) => handleRollbackClick(version.version_number, e)}
                          className="mt-2 text-xs px-2 py-1 rounded border border-orange-300 text-orange-600 hover:bg-orange-50"
                        >
                          回滚到此版本
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {fromVersion !== null && toVersion !== null && (
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-sm">
                      已选择: v{fromVersion} → v{toVersion}
                    </h4>
                    <button
                      onClick={() => setShowDiff(true)}
                      className="text-xs px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
                    >
                      对比
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {showDiff && fromVersion !== null && toVersion !== null && (
        <DiffViewerModal
          oldContent={fromContent}
          newContent={toContent}
          oldVersion={fromVersion}
          newVersion={toVersion}
          onClose={() => setShowDiff(false)}
        />
      )}

      {rollbackTarget !== null && rollbackVersionInfo && (
        <RollbackConfirmDialog
          versionNumber={rollbackTarget}
          versionInfo={{
            created_at: rollbackVersionInfo.created_at,
            operation_type: rollbackVersionInfo.operation_type,
          }}
          onConfirm={handleConfirmRollback}
          onCancel={() => setRollbackTarget(null)}
        />
      )}
    </>
  )
}
