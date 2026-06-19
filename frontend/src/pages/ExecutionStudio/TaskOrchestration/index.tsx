import { useEffect, useMemo, useState, useCallback } from 'react'
import { useProjectContext } from '../../../App'
import { useExecutionStore } from '../../../stores/executionStore'
import {
  fetchTasks,
  createTask,
  executeTask,
  retryTask,
  markBug,
  type ExecutionTask,
} from '../../../services/execution'
import TaskTree, { type TaskItem } from '../../../components/TaskTree'
import ExecutionPanel from '../../../components/ExecutionPanel'
import StatusBar from '../../../components/StatusBar'

const TABS = [
  { id: '拆解', label: '任务拆解' },
  { id: '执行', label: '任务执行' },
  { id: 'Bug', label: 'Bug 修复' },
]

export default function TaskOrchestrationPage() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId

  const {
    tasks,
    selectedTaskId,
    setTasks,
    selectTask,
    setLoading,
    setError,
    connectSSE,
    disconnectSSE,
  } = useExecutionStore()

  const [activeTab, setActiveTab] = useState('执行')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createForm, setCreateForm] = useState({
    name: '',
    type: 'coding' as 'coding' | 'test' | 'bugfix',
    parentModule: '',
    assignedSkill: '',
  })
  const [filterType, setFilterType] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterModule, setFilterModule] = useState('')
  const [showBatchExec, setShowBatchExec] = useState(false)
  const [_selectedTaskIds, _setSelectedTaskIds] = useState<Set<string>>(new Set())
  const [execStatus, setExecStatus] = useState('idle')
  const [execLogs, setExecLogs] = useState<string[]>([])
  const [showExecPanel, setShowExecPanel] = useState(false)
  const [activeExecutionId, setActiveExecutionId] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    fetchTasks(projectId)
      .then((data) => {
        setTasks(data)
        setError(null)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : '加载任务失败')
      })
      .finally(() => setLoading(false))
    // 连接 SSE
    connectSSE(projectId)
    return () => { disconnectSSE() }
  }, [projectId, setTasks, setLoading, setError, connectSSE, disconnectSSE])

  const taskItems = useMemo((): TaskItem[] => {
    return tasks.map((t: any) => ({
      taskId: t.task_id || t.taskId,
      name: t.name,
      status: (t.status || 'NOT_STARTED').toUpperCase(),
      type: t.type || 'coding',
      module: t.parent_module || t.parentModule || '默认模块',
    }))
  }, [tasks])

  const filteredTaskItems = useMemo(() => {
    return taskItems.filter((t) => {
      const matchType = !filterType || t.type === filterType
      const matchStatus = !filterStatus || t.status === filterStatus
      const matchModule = !filterModule || (t.module || '').includes(filterModule)
      return matchType && matchStatus && matchModule
    })
  }, [taskItems, filterType, filterStatus, filterModule])

  const moduleOptions = useMemo(() => {
    const set = new Set(taskItems.map((t) => t.module || '默认模块'))
    return Array.from(set)
  }, [taskItems])

  const stats = useMemo(() => {
    const total = taskItems.length
    const completed = taskItems.filter((t) => t.status === 'PASSED').length
    const failed = taskItems.filter((t) => t.status === 'FAILED').length
    const inProgress = taskItems.filter((t) => t.status === 'IN_PROGRESS').length
    return { total, completed, failed, inProgress }
  }, [taskItems])

  const selectedTask = useMemo(() => {
    return tasks.find((t: any) => (t.task_id || t.taskId) === selectedTaskId) as ExecutionTask | undefined
  }, [tasks, selectedTaskId])

  const handleCreateTask = useCallback(async () => {
    if (!projectId || !createForm.name) return
    try {
      setLoading(true)
      await createTask(projectId, {
        name: createForm.name,
        type: createForm.type,
        parent_module: createForm.parentModule,
        assigned_skill_id: createForm.assignedSkill,
      })
      const data = await fetchTasks(projectId)
      setTasks(data)
      setShowCreateForm(false)
      setCreateForm({ name: '', type: 'coding', parentModule: '', assignedSkill: '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建任务失败')
    } finally {
      setLoading(false)
    }
  }, [projectId, createForm, setTasks, setLoading, setError])

  const handleExecute = useCallback(async () => {
    if (!projectId || !selectedTaskId) return
    setExecStatus('prep')
    setExecLogs(['> prep: 加载上下文...'])
    setShowExecPanel(true)
    try {
      await executeTask(projectId, selectedTaskId)
      setExecStatus('exec')
      setExecLogs((prev) => [...prev, '> exec: 执行中...'])
      // 模拟执行完成后更新状态
      setTimeout(() => {
        setExecStatus('post')
        setExecLogs((prev) => [...prev, '> post: 产物写入...'])
      }, 1500)
      setTimeout(() => {
        setExecStatus('success')
        setExecLogs((prev) => [...prev, '> 执行完成'])
        fetchTasks(projectId).then(setTasks)
      }, 3000)
    } catch (err) {
      setExecStatus('failed')
      setExecLogs((prev) => [...prev, `> 执行失败: ${err instanceof Error ? err.message : '未知错误'}`])
    }
  }, [projectId, selectedTaskId, setTasks])

  const handleRetry = useCallback(async () => {
    if (!projectId || !selectedTaskId) return
    try {
      await retryTask(projectId, selectedTaskId)
      const data = await fetchTasks(projectId)
      setTasks(data)
      setExecStatus('idle')
      setExecLogs([])
    } catch (err) {
      setError(err instanceof Error ? err.message : '重试失败')
    }
  }, [projectId, selectedTaskId, setTasks, setError])

  const handleMarkBug = useCallback(async () => {
    if (!projectId || !selectedTaskId) return
    try {
      await markBug(projectId, selectedTaskId, {
        errorLog: execLogs.join('\n'),
        issueType: 'other',
      })
      const data = await fetchTasks(projectId)
      setTasks(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '标记 Bug 失败')
    }
  }, [projectId, selectedTaskId, execLogs, setTasks, setError])

  if (!projectId) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' }}>
        请先在顶部选择项目
      </div>
    )
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#fff',
        borderRadius: 8,
        border: '1px solid #e5e7eb',
        overflow: 'hidden',
      }}
    >
      {/* 顶部 Tab 切换 */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '10px 20px',
              fontSize: 13,
              border: 'none',
              background: activeTab === tab.id ? '#fff' : 'transparent',
              color: activeTab === tab.id ? '#2563eb' : '#6b7280',
              borderBottom: activeTab === tab.id ? '2px solid #2563eb' : '2px solid transparent',
              cursor: 'pointer',
              fontWeight: activeTab === tab.id ? 600 : 400,
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左侧：任务树 + 筛选 + 统计 */}
        <div style={{ width: showExecPanel ? 280 : 'auto', minWidth: 280, flex: showExecPanel ? 'none' : 1, borderRight: '1px solid #e5e7eb', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {/* 统计面板 */}
          <div style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb', background: '#f9fafb', display: 'flex', gap: 8, justifyContent: 'space-around' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#374151' }}>{stats.total}</div>
              <div style={{ fontSize: 10, color: '#6b7280' }}>总任务</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#16a34a' }}>{stats.completed}</div>
              <div style={{ fontSize: 10, color: '#6b7280' }}>已完成</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#dc2626' }}>{stats.failed}</div>
              <div style={{ fontSize: 10, color: '#6b7280' }}>失败</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#2563eb' }}>{stats.inProgress}</div>
              <div style={{ fontSize: 10, color: '#6b7280' }}>执行中</div>
            </div>
          </div>
          {/* 筛选栏 */}
          <div style={{ padding: '8px 12px', borderBottom: '1px solid #e5e7eb', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <select value={filterType} onChange={(e) => setFilterType(e.target.value)} style={{ padding: '4px 8px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 4, background: '#fff' }}>
              <option value="">全部类型</option>
              <option value="coding">编码</option>
              <option value="test">测试</option>
              <option value="bugfix">Bug修复</option>
            </select>
            <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} style={{ padding: '4px 8px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 4, background: '#fff' }}>
              <option value="">全部状态</option>
              <option value="NOT_STARTED">未开始</option>
              <option value="IN_PROGRESS">执行中</option>
              <option value="COMPLETED">已完成</option>
              <option value="FAILED">失败</option>
              <option value="BLOCKED">阻塞</option>
            </select>
            <select value={filterModule} onChange={(e) => setFilterModule(e.target.value)} style={{ padding: '4px 8px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 4, background: '#fff' }}>
              <option value="">全部模块</option>
              {moduleOptions.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
          {/* 批量操作 */}
          <div style={{ padding: '6px 12px', borderBottom: '1px solid #e5e7eb', display: 'flex', gap: 6, alignItems: 'center' }}>
            <button onClick={() => setShowBatchExec(!showBatchExec)} style={{ fontSize: 11, padding: '3px 8px', border: '1px solid #e5e7eb', borderRadius: 4, background: showBatchExec ? '#eff6ff' : '#fff', color: showBatchExec ? '#2563eb' : '#374151', cursor: 'pointer' }}>
              {showBatchExec ? '取消批量' : '批量操作'}
            </button>
            {showBatchExec && (
              <>
                <button onClick={() => { /* 批量执行 */ }} style={{ fontSize: 11, padding: '3px 8px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>批量执行</button>
                <button onClick={() => { /* 批量重试 */ }} style={{ fontSize: 11, padding: '3px 8px', background: '#f59e0b', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>批量重试</button>
              </>
            )}
            <span style={{ fontSize: 11, color: '#9ca3af', marginLeft: 'auto' }}>{filteredTaskItems.length} 个</span>
          </div>
          <TaskTree
            tasks={filteredTaskItems}
            selectedTaskId={selectedTaskId}
            onTaskSelect={(taskId) => {
              selectTask(taskId)
              if (showExecPanel) setActiveExecutionId(taskId)
            }}
            onTaskExecute={(taskId) => {
              selectTask(taskId)
              setShowExecPanel(true)
              handleExecute()
            }}
          />
        </div>

        {/* 中间：任务详情 */}
        {!showExecPanel && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderRight: '1px solid #e5e7eb' }}>
            {activeTab === '拆解' && (
              <div style={{ padding: 24, overflow: 'auto' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <h3 style={{ margin: 0, fontSize: 16 }}>任务拆解</h3>
                  <button
                    onClick={() => setShowCreateForm(true)}
                    style={{
                      padding: '6px 14px',
                      fontSize: 13,
                      background: '#2563eb',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 4,
                      cursor: 'pointer',
                    }}
                  >
                    + 新建任务
                  </button>
                </div>

                {showCreateForm && (
                  <div
                    style={{
                      padding: 16,
                      background: '#f9fafb',
                      borderRadius: 8,
                      marginBottom: 16,
                      border: '1px solid #e5e7eb',
                    }}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      <div>
                        <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>任务名称</label>
                        <input
                          value={createForm.name}
                          onChange={(e) => setCreateForm((p) => ({ ...p, name: e.target.value }))}
                          style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13 }}
                          placeholder="例如: 订单创建接口编码"
                        />
                      </div>
                      <div style={{ display: 'flex', gap: 12 }}>
                        <div style={{ flex: 1 }}>
                          <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>任务类型</label>
                          <select
                            value={createForm.type}
                            onChange={(e) => setCreateForm((p) => ({ ...p, type: e.target.value as any }))}
                            style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13 }}
                          >
                            <option value="coding">编码</option>
                            <option value="test">测试</option>
                            <option value="bugfix">Bug 修复</option>
                          </select>
                        </div>
                        <div style={{ flex: 1 }}>
                          <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>所属模块</label>
                          <input
                            value={createForm.parentModule}
                            onChange={(e) => setCreateForm((p) => ({ ...p, parentModule: e.target.value }))}
                            style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13 }}
                            placeholder="例如: 订单模块"
                          />
                        </div>
                      </div>
                      <div>
                        <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>分配 Skill</label>
                        <input
                          value={createForm.assignedSkill}
                          onChange={(e) => setCreateForm((p) => ({ ...p, assignedSkill: e.target.value }))}
                          style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13 }}
                          placeholder="例如: skill-code-generation"
                        />
                      </div>
                      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                        <button
                          onClick={() => setShowCreateForm(false)}
                          style={{ padding: '6px 12px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 4, background: '#fff', cursor: 'pointer' }}
                        >
                          取消
                        </button>
                        <button
                          onClick={handleCreateTask}
                          disabled={!createForm.name}
                          style={{
                            padding: '6px 12px',
                            fontSize: 12,
                            background: createForm.name ? '#2563eb' : '#e5e7eb',
                            color: createForm.name ? '#fff' : '#9ca3af',
                            border: 'none',
                            borderRadius: 4,
                            cursor: createForm.name ? 'pointer' : 'not-allowed',
                          }}
                        >
                          创建
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                <div style={{ fontSize: 13, color: '#6b7280' }}>
                  共 {taskItems.length} 个任务，按模块分组展示
                </div>
              </div>
            )}

            {activeTab === '执行' && selectedTask && (
              <div style={{ padding: 24, overflow: 'auto' }}>
                <h3 style={{ margin: '0 0 12px', fontSize: 16 }}>{selectedTask.name}</h3>
                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                  <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                    类型: {selectedTask.type}
                  </span>
                  <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                    状态: {selectedTask.status}
                  </span>
                  <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                    重试: {selectedTask.retry_count}/3
                  </span>
                </div>
                <div style={{ marginBottom: 12, fontSize: 13, color: '#374151' }}>
                  <strong>输入产物:</strong> {Array.isArray(selectedTask.input_artifacts) ? selectedTask.input_artifacts.join(', ') : (selectedTask.input_artifacts || '无')}
                </div>
                <div style={{ marginBottom: 12, fontSize: 13, color: '#374151' }}>
                  <strong>输出产物:</strong> {selectedTask.output_artifact_path || '无'}
                </div>
                <div style={{ marginBottom: 12, fontSize: 13, color: '#374151' }}>
                  <strong>分配 Skill:</strong> {selectedTask.assigned_skill_id || '未分配'}
                </div>

                <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                  <button
                    onClick={() => {
                      setShowExecPanel(true)
                      handleExecute()
                    }}
                    style={{
                      padding: '6px 14px',
                      fontSize: 13,
                      background: '#2563eb',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 4,
                      cursor: 'pointer',
                    }}
                  >
                    ▶ 执行
                  </button>
                  {selectedTask.status === 'failed' && (
                    <>
                      <button
                        onClick={handleMarkBug}
                        style={{
                          padding: '6px 12px',
                          fontSize: 12,
                          background: '#dc2626',
                          color: '#fff',
                          border: 'none',
                          borderRadius: 4,
                          cursor: 'pointer',
                        }}
                      >
                        标记为 Bug
                      </button>
                      <button
                        onClick={handleRetry}
                        style={{
                          padding: '6px 12px',
                          fontSize: 12,
                          background: '#fff',
                          color: '#2563eb',
                          border: '1px solid #2563eb',
                          borderRadius: 4,
                          cursor: 'pointer',
                        }}
                      >
                        重试
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}

            {activeTab === '执行' && !selectedTask && (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280', fontSize: 14 }}>
                请从左侧选择一个任务
              </div>
            )}

            {activeTab === 'Bug' && (
              <div style={{ padding: 24, overflow: 'auto' }}>
                <h3 style={{ margin: '0 0 12px', fontSize: 16 }}>Bug 修复</h3>
                <div style={{ fontSize: 13, color: '#6b7280' }}>
                  选择左侧标记为 BLOCKED 的任务进行修复
                </div>
              </div>
            )}
          </div>
        )}

        {/* 右侧：执行面板（可收起） */}
        {showExecPanel && (
          <div style={{ width: 360, minWidth: 360, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderLeft: '1px solid #e5e7eb' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>执行面板</span>
              <button
                onClick={() => setShowExecPanel(false)}
                style={{ fontSize: 12, color: '#6b7280', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                收起 ▶
              </button>
            </div>
            <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <ExecutionPanel
                status={execStatus}
                logs={execLogs}
                skillName={selectedTask?.assigned_skill_id || '未选择'}
                onExecute={handleExecute}
                onRetry={handleRetry}
                onAbort={() => {
                  setExecStatus('idle')
                  setExecLogs((prev) => [...prev, '> 已中断'])
                }}
              />
              {activeExecutionId && (
                <div style={{ flex: 1, overflow: 'hidden', borderTop: '1px solid #e5e7eb' }}>
                  <div style={{ padding: '8px 12px', fontSize: 12, fontWeight: 600, borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
                    实时日志
                  </div>
                  <div style={{ flex: 1, overflow: 'auto', padding: 8, fontSize: 11, fontFamily: 'monospace', lineHeight: 1.5, background: '#1f2937', color: '#e5e7eb' }}>
                    {execLogs.map((log, i) => (
                      <div key={i}>{log}</div>
                    ))}
                    <div style={{ color: '#6b7280', marginTop: 8 }}>
                      Token: 1,234 | 耗时: 45s
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <StatusBar
        projectName={projectId}
        stageName="任务编排"
        artifactName={selectedTask?.name || '-'}
        version="-"
      />
    </div>
  )
}
