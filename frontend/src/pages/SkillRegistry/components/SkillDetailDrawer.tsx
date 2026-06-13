import { useEffect } from 'react'
import { useSkillRegistryStore } from '../../../stores/skillRegistryStore'

interface SkillDetailDrawerProps {
  skillId: string | null
  onClose: () => void
}

const PLATFORM_ICONS: Record<string, string> = {
  kimi: 'K',
  claude: 'C',
  cursor: 'Cu',
  codex: 'Co',
  gemini: 'G',
  windsurf: 'W',
}

const PLATFORM_COLORS: Record<string, string> = {
  kimi: 'bg-rose-100 text-rose-700',
  claude: 'bg-amber-100 text-amber-700',
  cursor: 'bg-emerald-100 text-emerald-700',
  codex: 'bg-blue-100 text-blue-700',
  gemini: 'bg-purple-100 text-purple-700',
  windsurf: 'bg-cyan-100 text-cyan-700',
}

function CopyablePath({ path, label }: { path: string; label: string }) {
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(path)
    } catch {
      // ignore
    }
  }

  return (
    <div className="mb-3">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div
        className="flex items-center gap-2 p-2 bg-gray-50 rounded text-xs font-mono text-gray-700 cursor-pointer hover:bg-gray-100 transition-colors"
        onClick={handleCopy}
        title="点击复制"
      >
        <span className="truncate flex-1">{path}</span>
        <svg className="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      </div>
    </div>
  )
}

export function SkillDetailDrawer({ skillId, onClose }: SkillDetailDrawerProps) {
  const {
    skillDetail,
    skillExecutions,
    boundStages,
    fetchSkillDetail,
    fetchSkillExecutions,
    fetchBoundStages,
  } = useSkillRegistryStore()

  useEffect(() => {
    if (skillId) {
      fetchSkillDetail(skillId)
      fetchSkillExecutions(skillId)
      fetchBoundStages(skillId)
    }
  }, [skillId, fetchSkillDetail, fetchSkillExecutions, fetchBoundStages])

  const skill = skillDetail

  return (
    <>
      {/* Backdrop */}
      {skillId && (
        <div
          className="fixed inset-0 bg-black/30 z-40 transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <div
        className={`
          fixed top-0 right-0 h-full bg-white shadow-xl z-50
          transition-transform duration-300 ease-in-out
          flex flex-col
          ${skillId ? 'translate-x-0' : 'translate-x-full'}
        `}
        style={{ width: 480 }}
      >
        {skill ? (
          <>
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <div className="flex-1 min-w-0">
                <h2 className="text-lg font-semibold text-gray-900 truncate">
                  {skill.skill_name}
                </h2>
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  <span className="text-xs text-gray-500">v{skill.version}</span>
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700">
                    {skill.pattern}
                  </span>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto px-6 py-4">
              {/* Basic Info */}
              <section className="mb-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">基本信息</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex">
                    <span className="text-gray-500 w-20 shrink-0">描述</span>
                    <span className="text-gray-800">{skill.description || '-'}</span>
                  </div>
                  <div className="flex">
                    <span className="text-gray-500 w-20 shrink-0">状态</span>
                    <span className="text-gray-800">{skill.parse_status}</span>
                  </div>
                  <div className="flex">
                    <span className="text-gray-500 w-20 shrink-0">创建时间</span>
                    <span className="text-gray-800">
                      {skill.created_at ? new Date(skill.created_at).toLocaleString() : '-'}
                    </span>
                  </div>
                  <div className="flex">
                    <span className="text-gray-500 w-20 shrink-0">更新时间</span>
                    <span className="text-gray-800">
                      {skill.updated_at ? new Date(skill.updated_at).toLocaleString() : '-'}
                    </span>
                  </div>
                </div>
              </section>

              {/* File Paths */}
              <section className="mb-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">文件路径</h3>
                <CopyablePath
                  path={`${skill.directory_path}/SKILL.md`}
                  label="SKILL.md"
                />
                <CopyablePath
                  path={`${skill.directory_path}/meta.json`}
                  label="meta.json"
                />
              </section>

              {/* Trigger Condition */}
              {skill.description && (
                <section className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">触发条件</h3>
                  <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700 leading-relaxed">
                    {skill.description}
                  </div>
                </section>
              )}

              {/* Platforms */}
              {skill.platforms && skill.platforms.length > 0 && (
                <section className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">平台兼容性</h3>
                  <div className="flex flex-wrap gap-2">
                    {skill.platforms.map((platform) => (
                      <span
                        key={platform}
                        className={`
                          inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium
                          ${PLATFORM_COLORS[platform] || 'bg-gray-100 text-gray-700'}
                        `}
                      >
                        <span className="mr-1 font-bold">{PLATFORM_ICONS[platform] || '?'}</span>
                        {platform}
                      </span>
                    ))}
                  </div>
                </section>
              )}

              {/* Tags */}
              {skill.tags && skill.tags.length > 0 && (
                <section className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    {skill.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </section>
              )}

              {/* Bound Stages */}
              <section className="mb-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  关联的 Stage
                  <span className="ml-1 text-xs font-normal text-gray-500">
                    ({boundStages.length})
                  </span>
                </h3>
                {boundStages.length === 0 ? (
                  <div className="text-sm text-gray-400">暂无关联 Stage</div>
                ) : (
                  <div className="space-y-2">
                    {boundStages.map((stage) => (
                      <div
                        key={`${stage.stage_id}-${stage.binding_type}`}
                        className="flex items-center justify-between p-2.5 bg-gray-50 rounded-lg"
                      >
                        <span className="text-sm text-gray-800">{stage.stage_name}</span>
                        <span
                          className={`
                            text-xs px-2 py-0.5 rounded-full
                            ${stage.binding_type === 'primary'
                              ? 'bg-blue-50 text-blue-700'
                              : 'bg-gray-200 text-gray-600'
                            }
                          `}
                        >
                          {stage.binding_type === 'primary' ? '主技能' : '辅助'}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              {/* Execution History */}
              <section className="mb-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  执行历史
                  <span className="ml-1 text-xs font-normal text-gray-500">
                    (最近5次)
                  </span>
                </h3>
                {skillExecutions.length === 0 ? (
                  <div className="text-sm text-gray-400">暂无执行记录</div>
                ) : (
                  <div className="space-y-2">
                    {skillExecutions.map((exec) => (
                      <div
                        key={exec.execution_id}
                        className="p-2.5 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-mono text-gray-500">
                            {exec.execution_id.slice(0, 8)}
                          </span>
                          <span
                            className={`
                              text-xs px-2 py-0.5 rounded-full
                              ${exec.overall_status === 'SUCCESS'
                                ? 'bg-green-50 text-green-700'
                                : exec.overall_status === 'FAILED'
                                  ? 'bg-red-50 text-red-700'
                                  : 'bg-yellow-50 text-yellow-700'
                              }
                            `}
                          >
                            {exec.overall_status}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500">
                          {exec.trigger_action} · {new Date(exec.created_at).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            加载中...
          </div>
        )}
      </div>
    </>
  )
}
