import { useEffect, useState } from 'react'
import { Plus, Trash2, Edit2 } from 'lucide-react'
import {
  configNodeApi,
  type ConfigNode,
  type ConfigNodeCreate,
} from '../../../services/configNode'

const CATEGORIES = [
  { value: 'file_read', label: '文件读取' },
  { value: 'file_write', label: '文件写入' },
  { value: 'terminal', label: '终端执行' },
  { value: 'web_fetch', label: '网页抓取' },
  { value: 'external_api', label: '外部 API' },
]

const DECISIONS = [
  { value: 'allow', label: '允许', color: 'text-green-600 bg-green-50' },
  { value: 'ask', label: '询问', color: 'text-amber-600 bg-amber-50' },
  { value: 'deny', label: '拒绝', color: 'text-red-600 bg-red-50' },
]

const DEFAULT_MODES = [
  { value: 'allow', label: '全部允许' },
  { value: 'ask', label: '默认询问' },
  { value: 'deny', label: '全部拒绝' },
]

interface PermissionRule {
  category: string
  decision: 'allow' | 'ask' | 'deny'
  path?: string
  command?: string
  domain?: string
  description?: string
}

interface PolicyFormData {
  scope: 'global' | 'project' | 'user'
  scope_target: string
  key: string
  name: string
  description: string
  default_mode: 'allow' | 'ask' | 'deny'
  rules: PermissionRule[]
  priority: number
}

function initialFormData(node?: ConfigNode): PolicyFormData {
  const config = node?.config_json || { default_mode: 'ask', rules: [] }
  return {
    scope: (node?.scope as 'global' | 'project' | 'user') || 'global',
    scope_target: node?.scope_target || '',
    key: node?.key || '',
    name: node?.name || '',
    description: node?.description || '',
    default_mode: (config.default_mode as 'allow' | 'ask' | 'deny') || 'ask',
    rules: ((config.rules as PermissionRule[]) || []).map((r) => ({ ...r })),
    priority: node?.priority || 0,
  }
}

function buildCreatePayload(data: PolicyFormData): ConfigNodeCreate {
  return {
    node_type: 'llm_permission',
    scope: data.scope,
    scope_target: data.scope_target || null,
    key: data.key,
    name: data.name,
    description: data.description || undefined,
    priority: data.priority,
    config_json: {
      default_mode: data.default_mode,
      rules: data.rules,
    },
  }
}

interface PermissionPolicyPanelProps {
  projectId?: string
}

export default function PermissionPolicyPanel({ projectId }: PermissionPolicyPanelProps) {
  const [nodes, setNodes] = useState<ConfigNode[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editingNode, setEditingNode] = useState<ConfigNode | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<PolicyFormData>(initialFormData())

  const fetchNodes = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await configNodeApi.list({ node_type: 'llm_permission' })
      setNodes(data.items)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchNodes()
  }, [])

  useEffect(() => {
    if (editingNode) {
      setForm(initialFormData(editingNode))
    } else {
      const next = initialFormData()
      if (projectId) {
        next.scope = 'project'
        next.scope_target = projectId
      }
      setForm(next)
    }
  }, [editingNode, showForm, projectId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      if (editingNode) {
        await configNodeApi.update(editingNode.id, buildCreatePayload(form))
      } else {
        await configNodeApi.create(buildCreatePayload(form))
      }
      setShowForm(false)
      setEditingNode(null)
      await fetchNodes()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    }
  }

  const handleDelete = async (node: ConfigNode) => {
    if (!window.confirm(`确定删除权限策略「${node.name}」？`)) return
    try {
      await configNodeApi.remove(node.id)
      await fetchNodes()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  const addRule = () => {
    setForm((f) => ({
      ...f,
      rules: [
        ...f.rules,
        { category: 'file_read', decision: 'allow', path: '${PROJECT_ROOT}/**' },
      ],
    }))
  }

  const updateRule = (index: number, patch: Partial<PermissionRule>) => {
    setForm((f) => ({
      ...f,
      rules: f.rules.map((r, i) => (i === index ? { ...r, ...patch } : r)),
    }))
  }

  const removeRule = (index: number) => {
    setForm((f) => ({ ...f, rules: f.rules.filter((_, i) => i !== index) }))
  }

  const getPatternField = (rule: PermissionRule, idx: number) => {
    if (rule.category === 'file_read' || rule.category === 'file_write') {
      return (
        <input
          type="text"
          value={rule.path || ''}
          onChange={(e) => updateRule(idx, { path: e.target.value })}
          placeholder="路径 glob，如 ${PROJECT_ROOT}/**"
          className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
        />
      )
    }
    if (rule.category === 'terminal') {
      return (
        <input
          type="text"
          value={rule.command || ''}
          onChange={(e) => updateRule(idx, { command: e.target.value })}
          placeholder="命令前缀，如 pytest*"
          className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
        />
      )
    }
    return (
      <input
        type="text"
        value={rule.domain || ''}
        onChange={(e) => updateRule(idx, { domain: e.target.value })}
        placeholder="域名，如 docs.python.org 或 *"
        className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
      />
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">LLM 权限策略</h3>
          <p className="text-sm text-gray-500">配置 AI 对文件、终端、外部资源的访问控制</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setEditingNode(null)
            setShowForm(true)
          }}
          className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm hover:bg-gray-800"
        >
          <Plus size={16} />
          新增策略
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>
      )}

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-white border border-gray-200 rounded-xl p-6 space-y-4"
        >
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">名称</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">标识 key</label>
              <input
                type="text"
                value={form.key}
                disabled={!!editingNode}
                onChange={(e) => setForm({ ...form, key: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-100"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">作用域</label>
              <select
                value={form.scope}
                disabled={!!editingNode}
                onChange={(e) =>
                  setForm({
                    ...form,
                    scope: e.target.value as 'global' | 'project' | 'user',
                    scope_target:
                      e.target.value === 'project' && projectId ? projectId : '',
                  })
                }
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-100"
              >
                <option value="global">全局</option>
                <option value="project">项目</option>
                <option value="user">用户</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">目标 ID</label>
              <input
                type="text"
                value={form.scope_target}
                disabled={!!editingNode || form.scope === 'global'}
                onChange={(e) => setForm({ ...form, scope_target: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">优先级</label>
              <input
                type="number"
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: parseInt(e.target.value, 10) })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">描述</label>
            <input
              type="text"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">默认模式</label>
            <select
              value={form.default_mode}
              onChange={(e) =>
                setForm({
                  ...form,
                  default_mode: e.target.value as 'allow' | 'ask' | 'deny',
                })
              }
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            >
              {DEFAULT_MODES.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-gray-700">规则列表</label>
              <button
                type="button"
                onClick={addRule}
                className="inline-flex items-center gap-1 text-xs text-gray-700 hover:text-gray-900"
              >
                <Plus size={12} /> 添加规则
              </button>
            </div>
            <div className="space-y-2">
              {form.rules.map((rule, index) => (
                <div
                  key={index}
                  className="grid grid-cols-12 gap-2 items-start bg-gray-50 rounded-lg p-3"
                >
                  <div className="col-span-2">
                    <select
                      value={rule.category}
                      onChange={(e) => updateRule(index, { category: e.target.value })}
                      className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
                    >
                      {CATEGORIES.map((c) => (
                        <option key={c.value} value={c.value}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-2">
                    <select
                      value={rule.decision}
                      onChange={(e) =>
                        updateRule(index, {
                          decision: e.target.value as 'allow' | 'ask' | 'deny',
                        })
                      }
                      className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
                    >
                      {DECISIONS.map((d) => (
                        <option key={d.value} value={d.value}>
                          {d.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-4">{getPatternField(rule, index)}</div>
                  <div className="col-span-3">
                    <input
                      type="text"
                      value={rule.description || ''}
                      onChange={(e) => updateRule(index, { description: e.target.value })}
                      placeholder="说明"
                      className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
                    />
                  </div>
                  <div className="col-span-1 flex justify-end">
                    <button
                      type="button"
                      onClick={() => removeRule(index)}
                      className="p-1 text-gray-400 hover:text-red-600"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
              {form.rules.length === 0 && (
                <div className="text-xs text-gray-400 py-2">暂无规则，将使用默认模式</div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => {
                setShowForm(false)
                setEditingNode(null)
              }}
              className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
            >
              取消
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-800"
            >
              保存
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="text-sm text-gray-500 py-8 text-center">加载中...</div>
      ) : nodes.length === 0 ? (
        <div className="text-sm text-gray-500 py-8 text-center">暂无权限策略</div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-3 text-left font-medium">名称</th>
                <th className="px-4 py-3 text-left font-medium">作用域</th>
                <th className="px-4 py-3 text-left font-medium">默认模式</th>
                <th className="px-4 py-3 text-left font-medium">规则数</th>
                <th className="px-4 py-3 text-right font-medium">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {nodes.map((node) => {
                const cfg = node.config_json as {
                  default_mode?: string
                  rules?: unknown[]
                }
                return (
                  <tr key={node.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{node.name}</div>
                      <div className="text-xs text-gray-400">{node.key}</div>
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {node.scope}
                      {node.scope_target ? ` / ${node.scope_target}` : ''}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${
                          DECISIONS.find((d) => d.value === cfg.default_mode)?.color || ''
                        }`}
                      >
                        {DECISIONS.find((d) => d.value === cfg.default_mode)?.label ||
                          cfg.default_mode ||
                          '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{(cfg.rules || []).length}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            setEditingNode(node)
                            setShowForm(true)
                          }}
                          className="p-1.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded"
                        >
                          <Edit2 size={14} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(node)}
                          className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
