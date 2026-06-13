import { useEffect, useState } from 'react'
import { fetchApplications, fetchProjects } from '../services/project'
import type { ApplicationItem, Project } from '../services/project'

interface ProjectSelectorProps {
  value: string
  onChange: (projectId: string) => void
}

const LS_APP_KEY = 'arsitect:lastApplicationId'

export default function ProjectSelector({ value, onChange }: ProjectSelectorProps) {
  const [apps, setApps] = useState<ApplicationItem[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedApp, setSelectedApp] = useState(() => {
    try {
      return localStorage.getItem(LS_APP_KEY) || ''
    } catch {
      return ''
    }
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetchApplications()
      .then((res) => setApps(res.data))
      .catch(() => setApps([]))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selectedApp) {
      setProjects([])
      return
    }
    setLoading(true)
    fetchProjects(selectedApp)
      .then((data) => setProjects(data))
      .catch(() => setProjects([]))
      .finally(() => setLoading(false))
  }, [selectedApp])

  const handleAppChange = (appId: string) => {
    setSelectedApp(appId)
    try {
      localStorage.setItem(LS_APP_KEY, appId)
    } catch {
      // ignore
    }
    onChange('')
  }

  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', flex: 1, flexWrap: 'wrap' }}>
      <select
        value={selectedApp}
        onChange={(e) => handleAppChange(e.target.value)}
        style={{ padding: 8, border: '1px solid #e5e7eb', minWidth: 140 }}
      >
        <option value="">选择应用</option>
        {apps.map((app) => (
          <option key={app.application_id} value={app.application_id}>
            {app.application_name}
          </option>
        ))}
      </select>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={!selectedApp}
        style={{ padding: 8, border: '1px solid #e5e7eb', flex: 1, minWidth: 140 }}
      >
        <option value="">选择项目</option>
        {projects.map((proj) => (
          <option key={proj.project_id} value={proj.project_id}>
            {proj.project_name}
          </option>
        ))}
      </select>
      {loading && (
        <span style={{ fontSize: 12, color: '#6b7280' }}>加载中…</span>
      )}
    </div>
  )
}
