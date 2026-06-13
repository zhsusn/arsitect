import { useState } from 'react'
import { useSkillRegistryStore, type Skill, type SkillConflict, type ConflictResolution } from '../../../stores/skillRegistryStore'
import { ConflictResolveModal } from './ConflictResolveModal'

interface SkillImportModalProps {
  onClose: () => void
}

export function SkillImportModal({ onClose }: SkillImportModalProps) {
  const { scanSkills, confirmImport } = useSkillRegistryStore()
  const [directoryPath, setDirectoryPath] = useState('.agents/skills')
  const [scanning, setScanning] = useState(false)
  const [result, setResult] = useState<{
    parsed: Skill[]
    conflicts: SkillConflict[]
    errors: string[]
  } | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [importing, setImporting] = useState(false)
  const [showConflictModal, setShowConflictModal] = useState(false)

  const handleScan = async () => {
    setScanning(true)
    try {
      const res = await scanSkills(directoryPath)
      setResult({
        parsed: res.parsed_skills,
        conflicts: res.conflicts,
        errors: res.errors,
      })
      setSelected(new Set(res.parsed_skills.map((s) => s.skill_name)))
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : '扫描失败')
    } finally {
      setScanning(false)
    }
  }

  const toggleSelect = (name: string) => {
    const next = new Set(selected)
    if (next.has(name)) {
      next.delete(name)
    } else {
      next.add(name)
    }
    setSelected(next)
  }

  const handleConfirm = async () => {
    if (!result) return
    const toImport = result.parsed.filter((s) => selected.has(s.skill_name))
    if (toImport.length === 0 && result.conflicts.length === 0) {
      alert('请至少选择一项')
      return
    }
    if (result.conflicts.length > 0) {
      setShowConflictModal(true)
      return
    }
    await doImport(toImport)
  }

  const doImport = async (toImport: Skill[], resolutions?: ConflictResolution[]) => {
    setImporting(true)
    try {
      await confirmImport(toImport, resolutions)
      onClose()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : '导入失败')
    } finally {
      setImporting(false)
    }
  }

  const handleResolveConflicts = (resolutions: ConflictResolution[]) => {
    if (!result) return
    const toImport = result.parsed.filter((s) => selected.has(s.skill_name))
    // Also import conflict skills that are not skipped
    const conflictSkills = result.conflicts
      .filter((c) => {
        const res = resolutions.find((r) => r.skill_name === c.new_skill.skill_name)
        return res && res.action !== 'skip'
      })
      .map((c) => c.new_skill)

    // Apply rename if needed
    conflictSkills.forEach((skill) => {
      const res = resolutions.find((r) => r.skill_name === skill.skill_name)
      if (res && res.action === 'rename' && res.new_name) {
        skill.skill_name = res.new_name
      }
    })

    setShowConflictModal(false)
    doImport([...toImport, ...conflictSkills], resolutions)
  }

  return (
    <>
      <div
        className="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
        onClick={onClose}
      >
        <div
          className="bg-white rounded-xl shadow-2xl p-6 w-[600px] max-h-[80vh] overflow-auto"
          onClick={(e) => e.stopPropagation()}
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-4">导入 Skill</h2>

          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={directoryPath}
              onChange={(e) => setDirectoryPath(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Skill 目录路径"
            />
            <button
              onClick={handleScan}
              disabled={scanning}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {scanning ? '扫描中...' : '扫描'}
            </button>
          </div>

          {result && (
            <>
              {result.errors.length > 0 && (
                <div className="text-red-600 text-sm mb-3 p-3 bg-red-50 rounded-lg">
                  错误: {result.errors.join(', ')}
                </div>
              )}

              {result.conflicts.length > 0 && (
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-sm font-medium text-amber-700">
                      冲突 ({result.conflicts.length})
                    </h3>
                    <button
                      onClick={() => setShowConflictModal(true)}
                      className="text-xs px-2 py-1 rounded bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors"
                    >
                      去处理
                    </button>
                  </div>
                  {result.conflicts.map((c) => (
                    <div
                      key={c.new_skill.skill_name}
                      className="p-2.5 bg-amber-50 rounded-lg mb-1.5 text-sm text-amber-800 flex justify-between items-center"
                    >
                      <span>
                        {c.new_skill.skill_name} v{c.new_skill.version}
                      </span>
                      <span className="text-xs text-amber-600">
                        现有 v{c.existing_skill?.version || '?'}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {result.parsed.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    可导入 ({result.parsed.length})
                  </h3>
                  {result.parsed.map((s) => (
                    <label
                      key={s.skill_name}
                      className="flex items-center gap-3 p-2.5 bg-gray-50 rounded-lg mb-1.5 cursor-pointer hover:bg-gray-100 transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={selected.has(s.skill_name)}
                        onChange={() => toggleSelect(s.skill_name)}
                        className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                      />
                      <span className="text-sm text-gray-800">
                        {s.skill_name} <span className="text-gray-500">v{s.version}</span>
                        <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-white border border-gray-200 text-gray-600">
                          {s.pattern}
                        </span>
                      </span>
                    </label>
                  ))}
                </div>
              )}

              <div className="flex justify-end gap-2">
                <button
                  onClick={onClose}
                  disabled={importing}
                  className="px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleConfirm}
                  disabled={importing || (result.parsed.length === 0 && result.conflicts.length === 0)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                >
                  {importing ? '导入中...' : '确认导入'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {showConflictModal && result && result.conflicts.length > 0 && (
        <ConflictResolveModal
          conflicts={result.conflicts}
          onResolve={handleResolveConflicts}
          onClose={() => setShowConflictModal(false)}
        />
      )}
    </>
  )
}
