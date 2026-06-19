import { useEffect, useMemo, useState, useCallback } from 'react'
import { useSearchParams } from 'react-router'
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

export default function TaskCenter() {
  const [searchParams] = useSearchParams()
  const projectId = searchParams.get('projectId') || ''

  const {
    tasks,
    selectedTaskId,
    setTasks,
    selectTask,
    setLoading,
    setError,
  } = useExecutionStore()

  const [activeTab, setActiveTab] = useState('执行')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createForm, setCreateForm] = useState({
    name: '',
    type: 'coding' as 'coding' | 'test' | 'bugfix',
    parentModule: '',
    assignedSkill: '',
  })
  const [execStatus, setExecStatus] = useState('idle')
  const [execLogs, setExecLogs] = useState<string[]>([])

  // 加载任务列表
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
  }, [projectId, setTasks, setLoading, setError])

  const taskItems = useMemo((): TaskItem[] => {
    return tasks.map((t: any) => ({
      taskId: t.task_id || t.taskId,
      name: t.name,
      status: (t.status || 'NOT_STARTED').toUpperCase(),
      type: t.type || 'coding',
      module: t.parent_module || t.parentModule || '默认模块',
    }))
  }, [tasks])

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
    try {
      await executeTask(projectId, selectedTaskId)
      setExecStatus('exec')
      setExecLogs((prev) => [...prev, '> exec: 执行中...'])
      // 模拟完成后更新状态
      setTimeout(() => {
        setExecStatus('post')
        setExecLogs((prev) => [...prev, '> post: 产物写入...'])
      }, 1500)
      setTimeout(() => {
        setExecStatus('success')
        setExecLogs((prev) => [...prev, '> 执行完成'])
        // 刷新任务列表
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
        {/* 左侧：任务树 */}
        <TaskTree
          tasks={taskItems}
          selectedTaskId={selectedTaskId}
          onTaskSelect={selectTask}
          onTaskExecute={(taskId) => {
            selectTask(taskId)
            handleExecute()
          }}
        />

        {/* 中间：任务详情 */}
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
                <span
                  style={{
                    fontSize: 12,
                    padding: '4px 10px',
                    borderRadius: 4,
                    background: '#f3f4f6',
                    color: '#374151',
                  }}
                >
                  类型: {selectedTask.type}
                </span>
                <span
                  style={{
                    fontSize: 12,
                    padding: '4px 10px',
                    borderRadius: 4,
                    background: '#f3f4f6',
                    color: '#374151',
                  }}
                >
                  状态: {selectedTask.status}
                </span>
                <span
                  style={{
                    fontSize: 12,
                    padding: '4px 10px',
                    borderRadius: 4,
                    background: '#f3f4f6',
                    color: '#374151',
                  }}
                >
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

              {selectedTask.status === 'failed' && (
                <div style={{ marginTop: 16 }}>
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
                      marginRight: 8,
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
                </div>
              )}
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

        {/* 右侧：执行面板 */}
        <div style={{ width: 300, minWidth: 300, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
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
        </div>
      </div>

      <StatusBar
        projectName={projectId}
        stageName="任务中心"
        artifactName={selectedTask?.name || '-'}
        version="-"
      />
    </div>
  )
}
