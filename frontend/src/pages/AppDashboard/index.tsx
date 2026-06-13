import { useEffect, useState } from 'react'
import { useAppDashboardStore } from '../../stores/appDashboardStore'
import { AppCard } from './components/AppCard'
import { AppCreateModal } from './components/AppCreateModal'
import { AppDeleteConfirm } from './components/AppDeleteConfirm'

export default function AppDashboard() {
  const {
    applications,
    loading,
    error,
    searchQuery,
    fetchApplications,
    setSearchQuery,
  } = useAppDashboardStore()

  const [showCreate, setShowCreate] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<{
    id: string
    name: string
  } | null>(null)

  useEffect(() => {
    fetchApplications()
  }, [fetchApplications])

  const filtered = searchQuery
    ? applications.filter(
        (a) =>
          a.application_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          a.local_path.toLowerCase().includes(searchQuery.toLowerCase()),
      )
    : applications

  if (loading) return <div style={{ padding: 24 }}>加载中...</div>
  if (error) return <div style={{ padding: 24, color: '#ef4444' }}>错误: {error}</div>

  return (
    <div style={{ padding: 24, maxWidth: 800 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <h1 style={{ margin: 0 }}>Application 治理</h1>
        <button onClick={() => setShowCreate(true)}>+ 新建</button>
      </div>

      <input
        type="text"
        placeholder="按名称或路径搜索..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        style={{
          width: '100%',
          padding: 8,
          marginBottom: 16,
          boxSizing: 'border-box',
        }}
      />

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
          {searchQuery ? '无匹配结果' : '暂无 Application，点击右上角新建'}
        </div>
      ) : (
        filtered.map((app) => (
          <div key={app.application_id} style={{ position: 'relative' }}>
            <AppCard
              application_name={app.application_name}
              local_path={app.local_path}
              path_accessible={app.path_accessible}
              description={app.description}
            />
            <button
              onClick={() =>
                setDeleteTarget({
                  id: app.application_id,
                  name: app.application_name,
                })
              }
              style={{
                position: 'absolute',
                top: 16,
                right: 16,
                background: 'none',
                border: 'none',
                color: '#ef4444',
                cursor: 'pointer',
                fontSize: 14,
              }}
            >
              删除
            </button>
          </div>
        ))
      )}

      {showCreate && <AppCreateModal onClose={() => setShowCreate(false)} />}
      {deleteTarget && (
        <AppDeleteConfirm
          appId={deleteTarget.id}
          appName={deleteTarget.name}
          onClose={() => setDeleteTarget(null)}
        />
      )}
    </div>
  )
}
