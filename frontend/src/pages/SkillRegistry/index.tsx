import { useEffect, useState } from 'react'
import { useSkillRegistryStore } from '../../stores/skillRegistryStore'
import { SkillImportModal } from './components/SkillImportModal'
import { SkillDAGCanvas } from './components/SkillDAGCanvas'
import { SkillDetailDrawer } from './components/SkillDetailDrawer'

export default function SkillRegistry() {
  const {
    loading,
    error,
    searchQuery,
    patternFilter,
    statusFilter,
    fetchSkills,
    setSearchQuery,
    setPatternFilter,
    setStatusFilter,
    filteredSkills,
    selectedSkillId,
    setSelectedSkillId,
  } = useSkillRegistryStore()

  const [showImport, setShowImport] = useState(false)
  const [view, setView] = useState<'list' | 'dag'>('list')

  useEffect(() => {
    fetchSkills()
  }, [fetchSkills])

  const filtered = filteredSkills()

  if (loading) return <div className="p-6 text-gray-600">加载中...</div>
  if (error) return <div className="p-6 text-red-500">错误: {error}</div>

  return (
    <div className="max-w-[1200px]">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Skill 注册中心</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setView(view === 'list' ? 'dag' : 'list')}
            className="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            {view === 'list' ? 'DAG 画布' : '列表视图'}
          </button>
          <button
            onClick={() => setShowImport(true)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            + 导入 Skill
          </button>
        </div>
      </div>

      {view === 'list' ? (
        <>
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              placeholder="按名称搜索..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <select
              value={patternFilter}
              onChange={(e) => setPatternFilter(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">全部 Pattern</option>
              <option value="generator">generator</option>
              <option value="pipeline">pipeline</option>
              <option value="reviewer">reviewer</option>
              <option value="analyzer">analyzer</option>
              <option value="inversion">inversion</option>
              <option value="tool-wrapper">tool-wrapper</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">全部状态</option>
              <option value="PARSED">PARSED</option>
              <option value="MANUAL_REQUIRED">MANUAL_REQUIRED</option>
            </select>
          </div>

          {filtered.length === 0 ? (
            <div className="py-10 text-center text-gray-400 border-2 border-dashed border-gray-200 rounded-lg">
              {searchQuery || patternFilter || statusFilter
                ? '无匹配结果'
                : '暂无 Skill，点击右上角导入'}
            </div>
          ) : (
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200 text-left text-gray-600">
                    <th className="px-4 py-3 font-medium">名称</th>
                    <th className="px-4 py-3 font-medium">版本</th>
                    <th className="px-4 py-3 font-medium">Pattern</th>
                    <th className="px-4 py-3 font-medium">状态</th>
                    <th className="px-4 py-3 font-medium">平台</th>
                    <th className="px-4 py-3 font-medium">路径</th>
                    <th className="px-4 py-3 font-medium text-right">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((skill) => (
                    <tr
                      key={skill.skill_id}
                      className="border-b border-gray-100 hover:bg-gray-50/50 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <button
                          onClick={() => setSelectedSkillId(skill.skill_id)}
                          className="text-indigo-600 hover:text-indigo-800 font-medium text-left"
                        >
                          {skill.skill_name}
                        </button>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{skill.version}</td>
                      <td className="px-4 py-3">
                        <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700">
                          {skill.pattern}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`
                            inline-block px-2 py-0.5 rounded text-xs font-medium
                            ${skill.parse_status === 'PARSED'
                              ? 'bg-green-50 text-green-700'
                              : 'bg-yellow-50 text-yellow-700'
                            }
                          `}
                        >
                          {skill.parse_status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {(skill.platforms || []).join(', ') || '-'}
                      </td>
                      <td
                        className="px-4 py-3 text-gray-400 text-xs max-w-[200px] truncate"
                        title={skill.directory_path}
                      >
                        {skill.directory_path}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => setSelectedSkillId(skill.skill_id)}
                          className="text-xs px-2.5 py-1.5 rounded-md bg-gray-50 text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors"
                        >
                          详情
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      ) : (
        <SkillDAGCanvas />
      )}

      {showImport && <SkillImportModal onClose={() => setShowImport(false)} />}

      <SkillDetailDrawer
        skillId={selectedSkillId}
        onClose={() => setSelectedSkillId(null)}
      />
    </div>
  )
}
