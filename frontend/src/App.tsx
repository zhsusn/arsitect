import { useState, createContext, useContext } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from 'react-router'
import { GlobalToast } from './components/GlobalToast'
import ProjectSelector from './components/ProjectSelector'

// Project Center
import AppDashboard from './pages/AppDashboard'
import ProjectCreate from './pages/ProjectCreate'
import ProjectDashboard from './pages/ProjectDashboard'
import ArtifactViewer from './pages/ArtifactViewer'
import GateCenter from './pages/GateCenter'
import GateDetailPage from './pages/GateCenter/components/GateDetailPage'
import GateHistoryPage from './pages/GateCenter/components/GateHistoryPage'

// Requirement Studio
import BrainstormPage from './pages/RequirementStudio/Brainstorm'
import RequirementPlanPage from './pages/RequirementStudio/RequirementPlan'
import RequirementGatePage from './pages/RequirementStudio/RequirementGate'
import SketchGallery from './pages/SketchGallery'

// Solution Studio
import DesignPlanPage from './pages/SolutionStudio/DesignPlan'
import DesignFinalizationPage from './pages/SolutionStudio/DesignFinalization'
import C4Navigator from './pages/C4Navigator'
import WireframeCanvas from './pages/WireframeCanvas'
import OpenUIPreview from './pages/OpenUIPreview'
import BindingPanel from './pages/BindingPanel'

// Execution Studio
import TaskOrchestrationPage from './pages/ExecutionStudio/TaskOrchestration'
import CodeDevPage from './pages/ExecutionStudio/CodeDev'
import TestingPage from './pages/ExecutionStudio/Testing'
import UATPage from './pages/ExecutionStudio/UAT'
import CodeReviewPage from './pages/ExecutionStudio/CodeReview'
import ReleasePage from './pages/ExecutionStudio/Release'
import AiCliPage from './pages/AiCli'

// Platform
import SkillRegistry from './pages/SkillRegistry'
import LlmConfig from './pages/LlmConfig'
import TemplateStageConfig from './pages/TemplateStageConfig'
import DocForgeAdmin from './pages/DocForgeAdmin'

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
    icon: '🏢',
    label: '项目工作台',
    items: [
      { label: '应用管理', path: '/project-center/application' },
      { label: '项目管理', path: '/project-center/project' },
      { label: '产物浏览器', path: '/project-center/artifact-browser' },
      { label: '审批中心', path: '/project-center/approval' },
    ],
  },
  {
    icon: '🎨',
    label: '需求设计室',
    items: [
      { label: '脑暴室', path: '/requirement-studio/brainstorm' },
      { label: '需求方案', path: '/requirement-studio/requirement-plan' },
      { label: '需求草图', path: '/requirement-studio/sketch' },
      { label: '需求确认', path: '/requirement-studio/requirement-gate' },
    ],
  },
  {
    icon: '🏗️',
    label: '方案设计室',
    items: [
      { label: '设计方案', path: '/solution-studio/design-plan' },
      { label: '系统结构', path: '/solution-studio/system-structure' },
      { label: '页面布局', path: '/solution-studio/page-layout' },
      { label: '交互原型', path: '/solution-studio/interaction-prototype' },
      { label: '接口对照', path: '/solution-studio/interface-check' },
      { label: '设计定稿', path: '/solution-studio/design-finalization' },
    ],
  },
  {
    icon: '▶️',
    label: '开发执行室',
    items: [
      { label: '任务编排', path: '/execution-studio/task-orchestration' },
      { label: '代码开发', path: '/execution-studio/coding' },
      { label: '测试调试', path: '/execution-studio/testing' },
      { label: 'UAT 验收', path: '/execution-studio/uat' },
      { label: '代码审查', path: '/execution-studio/code-review' },
      { label: '发布管理', path: '/execution-studio/release' },
      { label: 'AI CLI', path: '/execution-studio/cli' },
    ],
  },
  {
    icon: '⚙️',
    label: '平台管理',
    items: [
      { label: 'Skill 治理', path: '/platform/skill-management' },
      { label: 'LLM 配置', path: '/platform/llm-config' },
      { label: '模板配置', path: '/platform/template-config' },
      { label: '文档标准化', path: '/platform/doc-standard' },
    ],
  },
]

function Sidebar() {
  const location = useLocation()
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    '项目工作台': true,
    '需求设计室': false,
    '方案设计室': false,
    '开发执行室': false,
    '平台管理': false,
  })

  const toggleGroup = (label: string) => {
    setExpanded((prev) => ({ ...prev, [label]: !prev[label] }))
  }

  const isActive = (path: string) => {
    if (path.endsWith('/*')) {
      const prefix = path.slice(0, -2)
      return location.pathname === prefix || location.pathname.startsWith(prefix + '/')
    }
    return location.pathname === path || location.pathname.startsWith(path + '/')
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

// Project Context for global projectId access
export const ProjectContext = createContext<{
  currentProjectId: string
  setCurrentProjectId: (id: string) => void
}>({ currentProjectId: '', setCurrentProjectId: () => {} })

export function useProjectContext() {
  return useContext(ProjectContext)
}

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
          to="/project-center/project/create"
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

// Route guard: requires projectId for design studio pages
function ProjectRequiredGuard({ children }: { children: React.ReactNode }) {
  const { currentProjectId } = useProjectContext()
  const location = useLocation()

  if (!currentProjectId) {
    return (
      <Navigate
        to="/project-center/project"
        state={{ from: location.pathname, message: '请先选择或创建一个项目' }}
        replace
      />
    )
  }
  return <>{children}</>
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
    <ProjectContext.Provider value={{ currentProjectId, setCurrentProjectId: handleProjectChange }}>
      <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
        <Sidebar />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <TopBar currentProjectId={currentProjectId} onProjectChange={handleProjectChange} />
          <main style={{ flex: 1, padding: 24, overflowY: 'auto', background: '#f9fafb' }}>
            <Routes>
              {/* ═══════════════════════════════════════════════════════════
                 项目工作台
                 ═══════════════════════════════════════════════════════════ */}
              <Route path="/project-center/application" element={<AppDashboard />} />
              <Route path="/project-center/project" element={<ProjectDashboard />} />
              <Route path="/project-center/project/create" element={<ProjectCreate />} />
              <Route path="/project-center/project/:projectId" element={<ProjectDashboard />} />
              <Route path="/project-center/artifact-browser" element={<ArtifactViewer />} />
              <Route path="/project-center/approval" element={<GateCenter />} />
              <Route path="/project-center/approval/history" element={<GateHistoryPage />} />
              <Route path="/project-center/approval/:gateId" element={<GateDetailPage />} />

              {/* ═══════════════════════════════════════════════════════════
                 需求设计室 — 需要项目ID
                 ═══════════════════════════════════════════════════════════ */}
              <Route path="/requirement-studio/brainstorm" element={<ProjectRequiredGuard><BrainstormPage /></ProjectRequiredGuard>} />
              <Route path="/requirement-studio/requirement-plan" element={<ProjectRequiredGuard><RequirementPlanPage /></ProjectRequiredGuard>} />
              <Route path="/requirement-studio/sketch" element={<ProjectRequiredGuard><SketchGallery /></ProjectRequiredGuard>} />
              <Route path="/requirement-studio/requirement-gate" element={<ProjectRequiredGuard><RequirementGatePage /></ProjectRequiredGuard>} />

              {/* ═══════════════════════════════════════════════════════════
                 方案设计室 — 需要项目ID
                 ═══════════════════════════════════════════════════════════ */}
              <Route path="/solution-studio/design-plan" element={<ProjectRequiredGuard><DesignPlanPage /></ProjectRequiredGuard>} />
              <Route path="/solution-studio/system-structure" element={<ProjectRequiredGuard><C4Navigator /></ProjectRequiredGuard>} />
              <Route path="/solution-studio/page-layout" element={<ProjectRequiredGuard><WireframeCanvas /></ProjectRequiredGuard>} />
              <Route path="/solution-studio/interaction-prototype" element={<ProjectRequiredGuard><OpenUIPreview /></ProjectRequiredGuard>} />
              <Route path="/solution-studio/interface-check" element={<ProjectRequiredGuard><BindingPanel /></ProjectRequiredGuard>} />
              <Route path="/solution-studio/design-finalization" element={<ProjectRequiredGuard><DesignFinalizationPage /></ProjectRequiredGuard>} />

              {/* ═══════════════════════════════════════════════════════════
                 开发执行室
                 ═══════════════════════════════════════════════════════════ */}
              <Route path="/execution-studio/task-orchestration" element={<ProjectRequiredGuard><TaskOrchestrationPage /></ProjectRequiredGuard>} />
              <Route path="/execution-studio/coding" element={<ProjectRequiredGuard><CodeDevPage /></ProjectRequiredGuard>} />
              <Route path="/execution-studio/coding/:projectId" element={<ProjectRequiredGuard><CodeDevPage /></ProjectRequiredGuard>} />
              <Route path="/execution-studio/testing" element={<ProjectRequiredGuard><TestingPage /></ProjectRequiredGuard>} />
              <Route path="/execution-studio/uat" element={<ProjectRequiredGuard><UATPage /></ProjectRequiredGuard>} />
              <Route path="/execution-studio/code-review" element={<ProjectRequiredGuard><CodeReviewPage /></ProjectRequiredGuard>} />
              <Route path="/execution-studio/release" element={<ProjectRequiredGuard><ReleasePage /></ProjectRequiredGuard>} />
              <Route path="/execution-studio/cli" element={<AiCliPage />} />

              {/* ═══════════════════════════════════════════════════════════
                 平台管理
                 ═══════════════════════════════════════════════════════════ */}
              <Route path="/platform/skill-management" element={<SkillRegistry />} />
              <Route path="/platform/llm-config" element={<LlmConfig />} />
              <Route path="/platform/template-config" element={<TemplateStageConfig />} />
              <Route path="/platform/doc-standard" element={<DocForgeAdmin />} />

              {/* ═══════════════════════════════════════════════════════════
                 旧路由重定向（兼容性）
                 ═══════════════════════════════════════════════════════════ */}

              {/* 项目工作台旧路由 */}
              <Route path="/project-center/workbench" element={<Navigate to="/project-center/project" replace />} />
              <Route path="/project-center/workbench/*" element={<Navigate to="/project-center/project" replace />} />

              {/* 需求设计室拆分重定向 */}
              <Route path="/requirement-studio/*" element={<Navigate to="/requirement-studio/brainstorm" replace />} />
              <Route path="/requirement-studio/requirement-outline" element={<Navigate to="/requirement-studio/requirement-plan" replace />} />
              <Route path="/requirement-studio/requirement-detailed" element={<Navigate to="/requirement-studio/requirement-plan" replace />} />
              <Route path="/requirement-studio/design-outline" element={<Navigate to="/solution-studio/design-plan" replace />} />
              <Route path="/requirement-studio/design-detailed" element={<Navigate to="/solution-studio/design-plan" replace />} />
              <Route path="/requirement-studio/artifacts" element={<Navigate to="/solution-studio/design-plan" replace />} />
              <Route path="/requirement-studio/governance" element={<Navigate to="/solution-studio/design-finalization" replace />} />

              {/* 方案设计室改名重定向 */}
              <Route path="/c4" element={<Navigate to="/solution-studio/system-structure" replace />} />
              <Route path="/c4/*" element={<Navigate to="/solution-studio/system-structure" replace />} />
              <Route path="/wireframe" element={<Navigate to="/solution-studio/page-layout" replace />} />
              <Route path="/wireframe/*" element={<Navigate to="/solution-studio/page-layout" replace />} />
              <Route path="/open-ui" element={<Navigate to="/solution-studio/interaction-prototype" replace />} />
              <Route path="/open-ui/*" element={<Navigate to="/solution-studio/interaction-prototype" replace />} />
              <Route path="/binding" element={<Navigate to="/solution-studio/interface-check" replace />} />
              <Route path="/binding/*" element={<Navigate to="/solution-studio/interface-check" replace />} />
              <Route path="/arch-governance" element={<Navigate to="/solution-studio/design-finalization" replace />} />
              <Route path="/arch-governance/*" element={<Navigate to="/solution-studio/design-finalization" replace />} />
              <Route path="/sketches" element={<Navigate to="/requirement-studio/sketch" replace />} />
              <Route path="/sketches/*" element={<Navigate to="/requirement-studio/sketch" replace />} />

              {/* 开发执行室改名+合并重定向 */}
              <Route path="/execution/task-center" element={<Navigate to="/execution-studio/task-orchestration" replace />} />
              <Route path="/execution/canvas" element={<Navigate to="/execution-studio/coding" replace />} />
              <Route path="/execution/canvas/:projectId" element={<Navigate to="/execution-studio/coding" replace />} />
              <Route path="/execution/issues" element={<Navigate to="/execution-studio/testing" replace />} />
              <Route path="/execution/monitor" element={<Navigate to="/execution-studio/task-orchestration" replace />} />
              <Route path="/execution/monitor/:executionId" element={<Navigate to="/execution-studio/task-orchestration" replace />} />
              <Route path="/execution/cli" element={<Navigate to="/execution-studio/cli" replace />} />
              <Route path="/execution/dashboard" element={<Navigate to="/project-center/project" replace />} />

              {/* 产物验证合并到项目工作台 */}
              <Route path="/artifact-verification/browser" element={<Navigate to="/project-center/artifact-browser" replace />} />
              <Route path="/artifact-verification/validation" element={<Navigate to="/solution-studio/design-finalization" replace />} />
              <Route path="/artifact-verification/history" element={<Navigate to="/project-center/artifact-browser" replace />} />

              {/* 治理审批合并到项目工作台 */}
              <Route path="/governance/approval-center" element={<Navigate to="/project-center/approval" replace />} />
              <Route path="/governance/approval-center/*" element={<Navigate to="/project-center/approval" replace />} />
              <Route path="/governance/bypass" element={<Navigate to="/project-center/approval" replace />} />
              <Route path="/gates" element={<Navigate to="/project-center/approval" replace />} />
              <Route path="/gates/*" element={<Navigate to="/project-center/approval" replace />} />

              {/* 历史遗留重定向 */}
              <Route path="/projects" element={<Navigate to="/project-center/project" replace />} />
              <Route path="/projects/create" element={<Navigate to="/project-center/project/create" replace />} />
              <Route path="/projects/:projectId" element={<Navigate to="/project-center/project" replace />} />
              <Route path="/applications" element={<Navigate to="/project-center/application" replace />} />
              <Route path="/executions" element={<Navigate to="/execution-studio/task-orchestration" replace />} />
              <Route path="/executions/:executionId" element={<Navigate to="/execution-studio/task-orchestration" replace />} />
              <Route path="/cli" element={<Navigate to="/execution-studio/cli" replace />} />
              <Route path="/monitoring" element={<Navigate to="/project-center/project" replace />} />
              <Route path="/artifacts" element={<Navigate to="/project-center/artifact-browser" replace />} />
              <Route path="/arch-validation" element={<Navigate to="/solution-studio/design-finalization" replace />} />
              <Route path="/history" element={<Navigate to="/project-center/artifact-browser" replace />} />
              <Route path="/bypass" element={<Navigate to="/project-center/approval" replace />} />
              <Route path="/skills" element={<Navigate to="/platform/skill-management" replace />} />
              <Route path="/settings/llm" element={<Navigate to="/platform/llm-config" replace />} />
              <Route path="/template-config" element={<Navigate to="/platform/template-config" replace />} />
              <Route path="/docforge" element={<Navigate to="/platform/doc-standard" replace />} />

              <Route path="/" element={<AppDashboard />} />
            </Routes>
          </main>
        </div>
        <GlobalToast />
      </div>
    </ProjectContext.Provider>
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
