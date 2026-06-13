import { useState, useMemo } from 'react'
import { useSkillRegistryStore } from '../../../stores/skillRegistryStore'

const PATTERN_TABS = [
  { key: '', label: '全部' },
  { key: 'generator', label: 'Generator' },
  { key: 'pipeline', label: 'Pipeline' },
  { key: 'reviewer', label: 'Reviewer' },
  { key: 'analyzer', label: 'Analyzer' },
  { key: 'inversion', label: 'Inversion' },
  { key: 'tool-wrapper', label: 'Tool-wrapper' },
]

const PATTERN_COLORS: Record<string, string> = {
  generator: 'border-l-amber-400',
  pipeline: 'border-l-blue-400',
  reviewer: 'border-l-emerald-400',
  analyzer: 'border-l-purple-400',
  inversion: 'border-l-rose-400',
  'tool-wrapper': 'border-l-cyan-400',
}

export function SkillNodeLibraryPanel({
  collapsed,
  onToggle,
}: {
  collapsed: boolean
  onToggle: () => void
}) {
  const { skills } = useSkillRegistryStore()
  const [search, setSearch] = useState('')
  const [patternTab, setPatternTab] = useState('')

  const filtered = useMemo(() => {
    return skills.filter((s) => {
      if (patternTab && s.pattern !== patternTab) return false
      if (search) {
        const q = search.toLowerCase()
        const matchName = s.skill_name.toLowerCase().includes(q)
        const matchPattern = s.pattern.toLowerCase().includes(q)
        const matchTags = (s.tags || []).some((t) => t.toLowerCase().includes(q))
        if (!matchName && !matchPattern && !matchTags) return false
      }
      return true
    })
  }, [skills, search, patternTab])

  const handleDragStart = (event: React.DragEvent, skill: typeof skills[0]) => {
    event.dataTransfer.setData('application/skill', JSON.stringify(skill))
    event.dataTransfer.effectAllowed = 'copy'
  }

  return (
    <div
      className={`
        flex flex-col bg-white border-r border-gray-200 transition-all duration-300
        ${collapsed ? 'w-10' : 'w-64'}
      `}
    >
      {/* Toggle */}
      <button
        onClick={onToggle}
        className="flex items-center justify-center h-10 border-b border-gray-100 hover:bg-gray-50 text-gray-500"
        title={collapsed ? '展开节点库' : '收起节点库'}
      >
        <svg
          className={`w-4 h-4 transition-transform ${collapsed ? '' : 'rotate-180'}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      {!collapsed && (
        <>
          {/* Search */}
          <div className="p-3 border-b border-gray-100">
            <div className="relative">
              <input
                type="text"
                placeholder="搜索 Skill..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <svg
                className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          {/* Pattern Tabs */}
          <div className="flex gap-1 p-2 overflow-x-auto border-b border-gray-100">
            {PATTERN_TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setPatternTab(tab.key)}
                className={`
                  px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors
                  ${patternTab === tab.key
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-gray-600 hover:bg-gray-50'
                  }
                `}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Skill List */}
          <div className="flex-1 overflow-auto p-2 space-y-2">
            {filtered.length === 0 && (
              <div className="text-center text-xs text-gray-400 py-8">无匹配结果</div>
            )}
            {filtered.map((skill) => (
              <div
                key={skill.skill_id}
                draggable
                onDragStart={(e) => handleDragStart(e, skill)}
                className={`
                  p-2.5 rounded-lg border border-l-4 bg-gray-50 cursor-grab active:cursor-grabbing
                  hover:bg-white hover:shadow-sm transition-all
                  ${PATTERN_COLORS[skill.pattern] || 'border-l-gray-300'}
                `}
                title={`拖拽到画布添加节点`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-800 truncate">
                    {skill.skill_name}
                  </span>
                  <span className="text-[10px] text-gray-500 shrink-0 ml-1">
                    v{skill.version}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-white text-gray-600 border border-gray-100">
                    {skill.pattern}
                  </span>
                  {(skill.platforms || []).slice(0, 2).map((p) => (
                    <span key={p} className="text-[10px] text-gray-400">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Count */}
          <div className="px-3 py-2 border-t border-gray-100 text-[10px] text-gray-400 text-center">
            {filtered.length} / {skills.length} Skills
          </div>
        </>
      )}
    </div>
  )
}
