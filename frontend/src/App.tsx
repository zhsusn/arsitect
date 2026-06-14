import { useState } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router'
import { GlobalToast } from './components/GlobalToast'
import ProjectSelector from './components/ProjectSelector'
import AppDashboard from './pages/AppDashboard'
import SkillRegistry from './pages/SkillRegistry'
import ProjectCreate from './pages/ProjectCreate'
import ProjectDashboard from './pages/ProjectDashboard'

import ExecutionMonitor from './pages/ExecutionMonitor'
import GateCenter from './pages/GateCenter'
import GateDetailPage from './pages/GateCenter/components/GateDetailPage'
import GateHistoryPage from './pages/GateCenter/components/GateHistoryPage'
import ArtifactViewer from './pages/ArtifactViewer'
import C4Navigator from './pages/C4Navigator'
import MonitoringDashboard from './pages/MonitoringDashboard'
import HistoryViewer from './pages/HistoryViewer'
import ArchValidation from './pages/ArchValidation'
import BypassManager from './pages/BypassManager'
import OpenUIPreview from './pages/OpenUIPreview'
import WireframeCanvas from './pages/WireframeCanvas'
import BindingPanel from './pages/BindingPanel'
import SketchGallery from './pages/SketchGallery'
import CanvasPage from './pages/Canvas'
import AiCliPage from './pages/AiCli'
import TemplateStageConfig from './pages/TemplateStageConfig'
import ComplexityRouter from './pages/ComplexityRouter'
import DocForgeAdmin from './pages/DocForgeAdmin'
import ArchGovernancePage from './pages/ArchGovernance'
import LlmConfig from './pages/LlmConfig'

interface NavItem {
  label: string
  path: string
}

interface NavGroup {
  icon: string
  label: string
  items: NavItem[]
}

const navGroups: NavGroup[] = [
  {
    icon: '📊',
    label: '项目中心',
    items: [
      { label: '项目工作台', path: '/projects' },
      { label: '项目画布', path: '/canvas/default' },
      { label: '复杂度评估', path: '/complexity-router' },
    ],
  },
  {
    icon: '▶',
    label: '执行中心',
    items: [
      { label: '执行监控', path: '/executions' },
      { label: 'AI CLI', path: '/cli' },
      { label: '监控看板', path: '/monitoring' },
    ],
  },
  {
    icon: '🏗️',
    label: '架构设计',
    items: [
      { label: 'C4 架构', path: '/c4' },
      { label: '线框图', path: '/wireframe' },
      { label: '草图', path: '/sketches' },
      { label: 'OpenUI', path: '/open-ui' },
      { label: '数据绑定', path: '/binding' },
    ],
  },
  {
    icon: '📦',
    label: '产物验证',
    items: [
      { label: '产物浏览器', path: '/artifacts' },
      { label: '架构验证', path: '/arch-validation' },
      { label: '架构治理', path: '/arch-governance' },
      { label: '历史回溯', path: '/history' },
    ],
  },
  {
    icon: '🛡️',
    label: '治理审批',
    items: [
      { label: '审批中心', path: '/gates' },
      { label: '旁路审批', path: '/bypass' },
    ],
  },
  {
    icon: '⚙️',
    label: '平台管理',
    items: [
      { label: 'Application', path: '/applications' },
      { label: 'Skill 治理', path: '/skills' },
      { label: 'LLM 配置', path: '/settings/llm' },
      { label: '模板配置', path: '/template-config' },
      { label: '文档标准化', path: '/docforge' },
    ],
  },
]

function Sidebar() {
  const location = useLocation()
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    '项目中心': true,
    '执行中心': false,
    '架构设计': false,
    '产物验证': false,
    '治理审批': false,
    '平台管理': false,
  })

  const toggleGroup = (label: string) => {
    setExpanded((prev) => ({ ...prev, [label]: !prev[label] }))
  }

  const isActive = (path: string) => {
    if (path === '/canvas/default') {
      return location.pathname.startsWith('/canvas')
    }
    return (
      location.pathname === path || location.pathname.startsWith(path + '/')
    )
  }

  return (
    <aside
      style={{
        width: 220,
        minWidth: 220,
        borderRight: '1px solid #e5e7eb',
        display: 'flex',
        flexDirection: 'column',
        background: '#fff',
        height: '100vh',
        overflowY: 'auto',
      }}
    >
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid #e5e7eb',
          fontWeight: 700,
          fontSize: 18,
          color: '#111827',
        }}
      >
        Arsitect
      </div>
      <nav style={{ padding: '12px 0', flex: 1 }}>
        {navGroups.map((group) => {
          const groupHasActive = group.items.some((item) => isActive(item.path))
          const isExpanded = expanded[group.label] || groupHasActive

          return (
            <div key={group.label} style={{ marginBottom: 4 }}>
              <button
                onClick={() => toggleGroup(group.label)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 20px',
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 14,
                  fontWeight: 600,
                  color: groupHasActive ? '#2563eb' : '#374151',
                  textAlign: 'left',
                }}
              >
                <span>
                  {group.icon} {group.label}
                </span>
                <span
                  style={{
                    display: 'inline-block',
                    transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                    transition: 'transform 0.2s',
                    fontSize: 12,
                  }}
                >
                  ▶
                </span>
              </button>
              {isExpanded && (
                <div style={{ paddingLeft: 20 }}>
                  {group.items.map((item) => {
                    const active = isActive(item.path)
                    return (
                      <Link
                        key={item.path}
                        to={item.path}
                        style={{
                          display: 'block',
                          padding: '8px 20px',
                          fontSize: 13,
                          color: active ? '#2563eb' : '#4b5563',
                          textDecoration: 'none',
                          background: active ? '#eff6ff' : 'transparent',
                          borderLeft: active ? '3px solid #2563eb' : '3px solid transparent',
                        }}
                      >
                        {item.label}
                      </Link>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </nav>
    </aside>
  )
}

const LS_PROJECT_KEY = 'arsitect:lastProjectId'

function TopBar({
  currentProjectId,
  onProjectChange,
}: {
  currentProjectId: string
  onProjectChange: (projectId: string) => void
}) {
  return (
    <header
      style={{
        height: 56,
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        background: '#fff',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, maxWidth: 480 }}>
        <span style={{ color: '#111827', fontWeight: 600, fontSize: 14, whiteSpace: 'nowrap' }}>
          当前项目
        </span>
        <ProjectSelector value={currentProjectId} onChange={onProjectChange} />
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <Link
          to="/projects/create"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            padding: '6px 14px',
            background: '#2563eb',
            color: '#fff',
            borderRadius: 6,
            textDecoration: 'none',
            fontSize: 13,
            fontWeight: 500,
          }}
        >
          <span style={{ fontSize: 16 }}>+</span> 创建项目
        </Link>
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            background: '#e5e7eb',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 12,
            color: '#374151',
          }}
        >
          👤
        </div>
      </div>
    </header>
  )
}

function AppLayout() {
  const [currentProjectId, setCurrentProjectId] = useState(() => {
    try {
      return localStorage.getItem(LS_PROJECT_KEY) || ''
    } catch {
      return ''
    }
  })

  const handleProjectChange = (projectId: string) => {
    setCurrentProjectId(projectId)
    try {
      if (projectId) {
        localStorage.setItem(LS_PROJECT_KEY, projectId)
      } else {
        localStorage.removeItem(LS_PROJECT_KEY)
      }
    } catch {
      // ignore
    }
  }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <TopBar currentProjectId={currentProjectId} onProjectChange={handleProjectChange} />
        <main style={{ flex: 1, padding: 24, overflowY: 'auto', background: '#f9fafb' }}>
          <Routes>
            <Route path="/applications" element={<AppDashboard />} />
            <Route path="/skills" element={<SkillRegistry />} />
            <Route path="/projects" element={<ProjectDashboard />} />
            <Route path="/projects/create" element={<ProjectCreate />} />
            <Route path="/projects/:projectId" element={<ProjectDashboard />} />

            <Route path="/executions" element={<ExecutionMonitor />} />
            <Route path="/executions/:executionId" element={<ExecutionMonitor />} />
            <Route path="/cli" element={<AiCliPage />} />
            <Route path="/gates" element={<GateCenter />} />
            <Route path="/gates/history" element={<GateHistoryPage />} />
            <Route path="/gates/:gateId" element={<GateDetailPage />} />
            <Route path="/artifacts" element={<ArtifactViewer />} />
            <Route path="/c4" element={<C4Navigator />} />
            <Route path="/c4/:projectId" element={<C4Navigator />} />
            <Route path="/monitoring" element={<MonitoringDashboard />} />
            <Route path="/history" element={<HistoryViewer />} />
            <Route path="/arch-validation" element={<ArchValidation />} />
            <Route path="/bypass" element={<BypassManager />} />
            <Route path="/open-ui" element={<OpenUIPreview />} />
            <Route path="/wireframe" element={<WireframeCanvas />} />
            <Route path="/binding" element={<BindingPanel />} />
            <Route path="/sketches" element={<SketchGallery />} />
            <Route path="/canvas/:projectId" element={<CanvasPage />} />
            <Route path="/template-config" element={<TemplateStageConfig />} />
            <Route path="/complexity-router" element={<ComplexityRouter />} />
            <Route path="/docforge" element={<DocForgeAdmin />} />
            <Route path="/settings/llm" element={<LlmConfig />} />
            <Route path="/arch-governance" element={<ArchGovernancePage />} />
            <Route path="/arch-governance/:projectId" element={<ArchGovernancePage />} />
            <Route path="/" element={<AppDashboard />} />
          </Routes>
        </main>
      </div>
      <GlobalToast />
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  )
}

export default App
