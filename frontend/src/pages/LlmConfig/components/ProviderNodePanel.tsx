import { useEffect, useMemo, useState } from 'react'
import { Plus, Trash2, Copy, TestTube, Star, Edit2 } from 'lucide-react'
import {
  configNodeApi,
  type ConfigNode,
  type ConfigNodeCreate,
  type ConfigNodeUpdate,
  type ProviderTestResult,
} from '../../../services/configNode'

const PROVIDER_TYPES = [
  { value: 'kimi-cli', label: 'Kimi CLI' },
  { value: 'kimi-api', label: 'Kimi API' },
  { value: 'openai', label: 'OpenAI 兼容' },
  { value: 'arsitect-agent', label: 'Arsitect Agent' },
]

const DEFAULT_PROVIDER_CONFIG: Record<string, Record<string, unknown>> = {
  'kimi-cli': { provider: 'kimi-cli', kimi_cli_path: 'kimi' },
  'kimi-api': { provider: 'kimi-api', api_base: '', api_key: '', model: 'kimi' },
  openai: {
    provider: 'openai',
    api_base: 'https://api.openai.com/v1',
    api_key: '',
    model: 'gpt-4o-mini',
  },
  'arsitect-agent': { provider: 'arsitect-agent' },
}

interface ProviderFormData {
  scope: 'global' | 'project' | 'user'
  scope_target: string
  key: string
  name: string
  description: string
  provider: string
  api_base: string
  api_key: string
  model: string
  kimi_cli_path: string
  timeout: number
  is_default: boolean
  priority: number
}

function buildCreatePayload(data: ProviderFormData): ConfigNodeCreate {
  const config: Record<string, unknown> = {
    provider: data.provider,
    timeout: data.timeout,
  }
  if (data.provider === 'kimi-cli') {
    config.kimi_cli_path = data.kimi_cli_path
  }
  if (data.provider === 'openai' || data.provider === 'kimi-api') {
    config.api_base = data.api_base
    config.model = data.model
  }
  const secret: Record<string, unknown> | null =
    data.provider === 'openai' || data.provider === 'kimi-api'
      ? { api_key: data.api_key }
      : null

  return {
    node_type: 'llm_provider',
    scope: data.scope,
    scope_target: data.scope_target || null,
    key: data.key,
    name: data.name,
    description: data.description || undefined,
    is_default: data.is_default,
    priority: data.priority,
    config_json: config,
    secret_json: secret,
  }
}

function buildUpdatePayload(data: ProviderFormData): ConfigNodeUpdate {
  const payload: ConfigNodeUpdate = {
    name: data.name,
    description: data.description || undefined,
    is_default: data.is_default,
    priority: data.priority,
    config_json: buildCreatePayload(data).config_json,
  }
  if (data.api_key && data.api_key !== '••••••' && !data.api_key.startsWith('•')) {
    payload.secret_json = { api_key: data.api_key }
  }
  return payload
}

function initialFormData(node?: ConfigNode): ProviderFormData {
  const config = node?.config_json || { provider: 'kimi-cli' }
  const secret = node?.secret_json || {}
  return {
    scope: (node?.scope as 'global' | 'project' | 'user') || 'global',
    scope_target: node?.scope_target || '',
    key: node?.key || '',
    name: node?.name || '',
    description: node?.description || '',
    provider: (config.provider as string) || 'kimi-cli',
    api_base: (config.api_base as string) || '',
    api_key: (secret.api_key as string) || '',
    model: (config.model as string) || '',
    kimi_cli_path: (config.kimi_cli_path as string) || 'kimi',
    timeout: (config.timeout as number) || 120,
    is_default: node?.is_default || false,
    priority: node?.priority || 0,
  }
}

interface ProviderNodePanelProps {
  projectId?: string
}

export default function ProviderNodePanel({ projectId }: ProviderNodePanelProps) {
  const [nodes, setNodes] = useState<ConfigNode[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editingNode, setEditingNode] = useState<ConfigNode | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [testResults, setTestResults] = useState<Record<string, ProviderTestResult>>({})
  const [testingId, setTestingId] = useState<string | null>(null)

  const [form, setForm] = useState<ProviderFormData>(initialFormData())

  const fetchNodes = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await configNodeApi.list({ node_type: 'llm_provider' })
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
      setForm(initialFormData())
      if (projectId) {
        setForm((f) => ({ ...f, scope: 'project', scope_target: projectId }))
      }
    }
  }, [editingNode, showForm, projectId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      if (editingNode) {
        await configNodeApi.update(editingNode.id, buildUpdatePayload(form))
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
    if (!window.confirm(`确定删除 Provider 节点「${node.name}」？`)) return
    try {
      await configNodeApi.remove(node.id)
      await fetchNodes()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  const handleClone = async (node: ConfigNode) => {
    try {
      await configNodeApi.clone(node.id)
      await fetchNodes()
    } catch (err) {
      setError(err instanceof Error ? err.message : '克隆失败')
    }
  }

  const handleTest = async (node: ConfigNode) => {
    setTestingId(node.id)
    try {
      const result = await configNodeApi.testProvider(node.id)
      setTestResults((prev) => ({ ...prev, [node.id]: result }))
    } catch (err) {
      setTestResults((prev) => ({
        ...prev,
        [node.id]: { success: false, message: err instanceof Error ? err.message : '测试失败' },
      }))
    } finally {
      setTestingId(null)
    }
  }

  const providerLabel = useMemo(() => {
    const map = Object.fromEntries(PROVIDER_TYPES.map((p) => [p.value, p.label]))
    return (v: string) => map[v] || v
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">LLM Provider 节点</h3>
          <p className="text-sm text-gray-500">管理全局或项目级的 LLM 接入配置</p>
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
          新增 Provider
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
                    scope_target: e.target.value === 'project' && projectId ? projectId : '',
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
                placeholder={form.scope === 'project' ? '项目 ID' : '用户 ID'}
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

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Provider 类型</label>
              <select
                value={form.provider}
                onChange={(e) => {
                  const p = e.target.value
                  setForm((f) => ({
                    ...f,
                    provider: p,
                    ...DEFAULT_PROVIDER_CONFIG[p],
                  }))
                }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              >
                {PROVIDER_TYPES.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-4 pt-6">
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={form.is_default}
                  onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
                  className="rounded border-gray-300"
                />
                设为默认
              </label>
            </div>
          </div>

          {form.provider === 'kimi-cli' && (
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Kimi CLI 路径
              </label>
              <input
                type="text"
                value={form.kimi_cli_path}
                onChange={(e) => setForm({ ...form, kimi_cli_path: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
          )}

          {(form.provider === 'openai' || form.provider === 'kimi-api') && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">API Base</label>
                  <input
                    type="text"
                    value={form.api_base}
                    onChange={(e) => setForm({ ...form, api_base: e.target.value })}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">模型</label>
                  <input
                    type="text"
                    value={form.model}
                    onChange={(e) => setForm({ ...form, model: e.target.value })}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">API Key</label>
                <input
                  type="password"
                  value={form.api_key}
                  placeholder={editingNode ? '不修改请留空' : ''}
                  onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </>
          )}

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
        <div className="text-sm text-gray-500 py-8 text-center">暂无 Provider 节点</div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-3 text-left font-medium">名称</th>
                <th className="px-4 py-3 text-left font-medium">类型</th>
                <th className="px-4 py-3 text-left font-medium">作用域</th>
                <th className="px-4 py-3 text-left font-medium">默认</th>
                <th className="px-4 py-3 text-left font-medium">状态</th>
                <th className="px-4 py-3 text-right font-medium">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {nodes.map((node) => (
                <tr key={node.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{node.name}</div>
                    <div className="text-xs text-gray-400">{node.key}</div>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {providerLabel((node.config_json.provider as string) || '')}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {node.scope}
                    {node.scope_target ? ` / ${node.scope_target}` : ''}
                  </td>
                  <td className="px-4 py-3">
                    {node.is_default ? (
                      <span className="inline-flex items-center gap-1 text-xs text-amber-600">
                        <Star size={12} /> 默认
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {testResults[node.id] && (
                      <span
                        className={`text-xs ${
                          testResults[node.id].success ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {testResults[node.id].success ? '连通' : '失败'}
                        {testResults[node.id].latency_ms
                          ? ` (${testResults[node.id].latency_ms}ms)`
                          : ''}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => handleTest(node)}
                        disabled={testingId === node.id}
                        className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                        title="测试连接"
                      >
                        <TestTube size={14} />
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setEditingNode(node)
                          setShowForm(true)
                        }}
                        className="p-1.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded"
                        title="编辑"
                      >
                        <Edit2 size={14} />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleClone(node)}
                        className="p-1.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded"
                        title="克隆"
                      >
                        <Copy size={14} />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(node)}
                        className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded"
                        title="删除"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
