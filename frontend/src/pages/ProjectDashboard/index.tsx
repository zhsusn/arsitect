import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import { useProjectDashboardStore } from '../../stores/projectDashboardStore'
import { fetchApplications } from '../../services/project'
import type { ApplicationItem, Project } from '../../services/project'
import ProjectCard from './components/ProjectCard'
import ProjectListView from './components/ProjectListView'
import RiskAlertPanel from './components/RiskAlertPanel'
import ProjectDetailDrawer from './components/ProjectDetailDrawer'
import DeleteConfirmDialog from './components/DeleteConfirmDialog'
import SizeEstimateWizard from './components/SizeEstimateWizard'
import ScaleMismatchBanner from './components/ScaleMismatchBanner'

export default function ProjectDashboard() {
  const {
    loading,
    error,
    searchQuery,
    statusFilter,
    riskFilter,
    sortField,
    sortOrder,
    viewMode,
    fetchProjects,
    activateProject,
    archiveProject,
    cancelProject,
    setSearchQuery,
    setStatusFilter,
    setRiskFilter,
    setSortField,
    setSortOrder,
    setViewMode,
    filteredProjects,
  } = useProjectDashboardStore()

  const [apps, setApps] = useState<ApplicationItem[]>([])
  const [selectedAppId, setSelectedAppId] = useState('')
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [detailProject, setDetailProject] = useState<Project | null>(null)
  const [deleteProject, setDeleteProject] = useState<Project | null>(null)
  const [sizeEstimateProject, setSizeEstimateProject] = useState<Project | null>(null)
  const [dismissMismatchId, setDismissMismatchId] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetchApplications()
      .then((res) => {
        setApps(res.data)
        if (res.data.length > 0) {
          setSelectedAppId(res.data[0].application_id)
        }
      })
      .catch(() => setApps([]))
  }, [])

  useEffect(() => {
    if (selectedAppId) {
      fetchProjects(selectedAppId)
    }
  }, [selectedAppId, fetchProjects])

  const filtered = filteredProjects()

  if (loading && apps.length === 0) return <div style={{ padding: 24 }}>加载中...</div>
  if (error) return <div style={{ padding: 24, color: '#ef4444' }}>错误: {error}</div>

  const selectedProject = filtered.find((p) => p.project_id === selectedProjectId) || null

  return (
    <div style={{ maxWidth: 900 }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
          flexWrap: 'wrap',
          gap: 8,
        }}
      >
        <h1 style={{ margin: 0 }}>项目工作台</h1>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {apps.length > 0 && (
            <select
              value={selectedAppId}
              onChange={(e) => setSelectedAppId(e.target.value)}
              style={{ padding: 8, border: '1px solid #e5e7eb', borderRadius: 6 }}
            >
              {apps.map((app) => (
                <option key={app.application_id} value={app.application_id}>
                  {app.application_name}
                </option>
              ))}
            </select>
          )}
          <button onClick={() => navigate('/projects/create')}>+ 新建项目</button>
        </div>
      </div>

      {/* Filters & View Toggle */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          marginBottom: 16,
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        <input
          type="text"
          placeholder="搜索项目名称..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ flex: 1, minWidth: 180, padding: 8 }}
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{ padding: 8 }}
        >
          <option value="">全部状态</option>
          <option value="Draft">Draft</option>
          <option value="Active">Active</option>
          <option value="Archived">Archived</option>
          <option value="Cancelled">Cancelled</option>
        </select>
        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          style={{ padding: 8 }}
        >
          <option value="">全部风险</option>
          <option value="None">None</option>
          <option value="Low">Low</option>
          <option value="Medium">Medium</option>
          <option value="High">High</option>
        </select>
        <select
          value={sortField}
          onChange={(e) =>
            setSortField(e.target.value as 'created_at' | 'updated_at' | 'project_name')
          }
          style={{ padding: 8 }}
        >
          <option value="created_at">创建时间</option>
          <option value="updated_at">更新时间</option>
          <option value="project_name">名称</option>
        </select>
        <button
          onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
          style={{ padding: '8px 12px' }}
        >
          {sortOrder === 'asc' ? '↑ 升序' : '↓ 降序'}
        </button>

        {/* View Toggle */}
        <div style={{ display: 'flex', border: '1px solid #e5e7eb', borderRadius: 6, overflow: 'hidden' }}>
          <button
            onClick={() => setViewMode('grid')}
            style={{
              padding: '8px 12px',
              border: 'none',
              background: viewMode === 'grid' ? '#3b82f6' : '#fff',
              color: viewMode === 'grid' ? '#fff' : '#374151',
              cursor: 'pointer',
              fontSize: 13,
            }}
            title="网格视图"
          >
            ⊞
          </button>
          <button
            onClick={() => setViewMode('list')}
            style={{
              padding: '8px 12px',
              border: 'none',
              background: viewMode === 'list' ? '#3b82f6' : '#fff',
              color: viewMode === 'list' ? '#fff' : '#374151',
              cursor: 'pointer',
              fontSize: 13,
            }}
            title="列表视图"
          >
            ☰
          </button>
        </div>
      </div>

      {/* Scale mismatch warning */}
      {selectedProjectId && selectedProject && selectedProject.project_status === 'Draft' && selectedProject.size_estimate_id && dismissMismatchId !== selectedProjectId && (
        <ScaleMismatchBanner
          projectId={selectedProjectId}
          onDismiss={() => setDismissMismatchId(selectedProjectId)}
        />
      )}

      {/* Risk alert banner for selected project */}
      {selectedProjectId && selectedProject && (
        <div style={{ marginBottom: 16 }}>
          <RiskAlertPanel projectId={selectedProjectId} />
        </div>
      )}

      {/* Project list */}
      {filtered.length === 0 ? (
        <div
          style={{
            padding: 40,
            textAlign: 'center',
            color: '#6b7280',
            border: '2px dashed #e5e7eb',
            borderRadius: 8,
          }}
        >
          {searchQuery || statusFilter || riskFilter
            ? '无匹配结果'
            : '暂无项目，点击右上角新建'}
        </div>
      ) : viewMode === 'grid' ? (
        filtered.map((project) => (
          <ProjectCard
            key={project.project_id}
            project={project}
            onSelect={(id) => setSelectedProjectId(id)}
            onActivate={async (id) => {
              await activateProject(id)
            }}
            onArchive={async (id) => {
              const p = filtered.find((x) => x.project_id === id)
              if (p) setDeleteProject(p)
            }}
            onCancel={async (id) => {
              await cancelProject(id)
            }}
            onEnter={(id) => {
              navigate(`/canvas/${id}`)
            }}
            onViewDetail={(id) => {
              const p = filtered.find((x) => x.project_id === id)
              if (p) setDetailProject(p)
            }}
            onEdit={(id) => {
              alert(`编辑项目 ${id}（演示）`)
            }}
            onSizeEstimate={(id) => {
              const p = filtered.find((x) => x.project_id === id)
              if (p) setSizeEstimateProject(p)
            }}
          />
        ))
      ) : (
        <ProjectListView
          projects={filtered}
          onViewDetail={(p) => setDetailProject(p)}
          onEdit={(p) => alert(`编辑项目 ${p.project_name}（演示）`)}
          onArchive={(p) => setDeleteProject(p)}
          onActivate={async (p) => {
            await activateProject(p.project_id)
          }}
          onCancel={async (p) => {
            await cancelProject(p.project_id)
          }}
          onEnter={(p) => {
            navigate(`/canvas/${p.project_id}`)
          }}
        />
      )}

      {/* Detail Drawer */}
      {detailProject && (
        <ProjectDetailDrawer
          project={detailProject}
          onClose={() => setDetailProject(null)}
        />
      )}

      {/* Delete Confirm Dialog */}
      {deleteProject && (
        <DeleteConfirmDialog
          projectName={deleteProject.project_name}
          onCancel={() => setDeleteProject(null)}
          onConfirm={async () => {
            await archiveProject(deleteProject.project_id)
            setDeleteProject(null)
          }}
        />
      )}

      {/* Size Estimate Wizard */}
      {sizeEstimateProject && (
        <SizeEstimateWizard
          projectId={sizeEstimateProject.project_id}
          onClose={() => setSizeEstimateProject(null)}
          onApplied={() => {
            if (selectedAppId) fetchProjects(selectedAppId)
          }}
        />
      )}
    </div>
  )
}
