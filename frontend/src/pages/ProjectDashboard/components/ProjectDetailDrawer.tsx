import { useEffect, useState, useCallback } from 'react'
import { useProjectDashboardStore } from '../../../stores/projectDashboardStore'
import type { Project, StageProgress, ArtifactSummary, OperationLogItem, SizeEstimateResult } from '../../../services/project'

interface ProjectDetailDrawerProps {
  project: Project
  onClose: () => void
}

type TabKey = 'overview' | 'stages' | 'artifacts' | 'logs'

const TAB_LABELS: Record<TabKey, string> = {
  overview: '概览',
  stages: '阶段进度',
  artifacts: '产物',
  logs: '操作日志',
}

const complexityBadgeStyles: Record<string, { bg: string; color: string }> = {
  Trivial: { bg: '#f3f4f6', color: '#6b7280' },
  Light: { bg: '#eff6ff', color: '#3b82f6' },
  Standard: { bg: '#fff7ed', color: '#f97316' },
  Deep: { bg: '#fef2f2', color: '#ef4444' },
}

const complexityLabels: Record<string, string> = {
  Trivial: '轻量',
  Light: '轻量',
  Standard: '标准',
  Deep: '深度',
}

export default function ProjectDetailDrawer({ project, onClose }: ProjectDetailDrawerProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('overview')
  const { projectOverview, overviewLoading, fetchProjectOverview, clearProjectOverview } =
    useProjectDashboardStore()

  useEffect(() => {
    fetchProjectOverview(project.project_id)
    return () => {
      clearProjectOverview()
    }
  }, [project.project_id, fetchProjectOverview, clearProjectOverview])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    },
    [onClose],
  )

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  const overview = projectOverview

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1100,
        display: 'flex',
        justifyContent: 'flex-end',
      }}
    >
      {/* Backdrop */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(0,0,0,0.4)',
        }}
        onClick={onClose}
      />
      {/* Drawer */}
      <div
        style={{
          position: 'relative',
          width: 500,
          maxWidth: '100%',
          height: '100%',
          background: '#fff',
          boxShadow: '-4px 0 24px rgba(0,0,0,0.1)',
          display: 'flex',
          flexDirection: 'column',
          animation: 'slideIn 0.2s ease-out',
        }}
      >
        <style>{`
          @keyframes slideIn {
            from { transform: translateX(100%); }
            to { transform: translateX(0); }
          }
        `}</style>
        {/* Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid #e5e7eb',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>{project.project_name}</h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: 20,
              cursor: 'pointer',
              color: '#6b7280',
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb' }}>
          {(Object.keys(TAB_LABELS) as TabKey[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                flex: 1,
                padding: '10px 0',
                background: activeTab === tab ? '#fff' : '#f9fafb',
                border: 'none',
                borderBottom: activeTab === tab ? '2px solid #3b82f6' : '2px solid transparent',
                color: activeTab === tab ? '#3b82f6' : '#6b7280',
                fontWeight: activeTab === tab ? 600 : 400,
                fontSize: 13,
                cursor: 'pointer',
              }}
            >
              {TAB_LABELS[tab]}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
          {overviewLoading && <div style={{ color: '#6b7280', textAlign: 'center', padding: 40 }}>加载中...</div>}
          {!overviewLoading && overview && (
            <>
              {activeTab === 'overview' && <OverviewTab project={project} sizeEstimate={overview.size_estimate} />}
              {activeTab === 'stages' && <StagesTab stages={overview.stages} />}
              {activeTab === 'artifacts' && <ArtifactsTab artifacts={overview.artifacts} />}
              {activeTab === 'logs' && <LogsTab logs={overview.operation_logs} />}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function OverviewTab({
  project,
  sizeEstimate,
}: {
  project: Project
  sizeEstimate: SizeEstimateResult | null
}) {
  const badge = sizeEstimate?.complexity_level
    ? complexityBadgeStyles[sizeEstimate.complexity_level] || complexityBadgeStyles.Standard
    : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Basic Info */}
      <section>
        <h3 style={{ margin: '0 0 12px 0', fontSize: 14, fontWeight: 600, color: '#374151' }}>基本信息</h3>
        <div
          style={{
            background: '#f9fafb',
            borderRadius: 8,
            padding: 16,
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
            fontSize: 13,
          }}
        >
          <InfoRow label="项目名称" value={project.project_name} />
          <InfoRow label="描述" value={project.project_description || '无描述'} />
          <InfoRow label="应用ID" value={project.application_id} />
          <InfoRow label="模板类型" value={project.template_level} />
          <InfoRow label="状态" value={project.project_status} />
          <InfoRow
            label="创建时间"
            value={new Date(project.created_at).toLocaleString('zh-CN')}
          />
        </div>
      </section>

      {/* Size Estimate */}
      {sizeEstimate && (
        <section>
          <h3 style={{ margin: '0 0 12px 0', fontSize: 14, fontWeight: 600, color: '#374151' }}>
            规模评估结果
          </h3>
          <div
            style={{
              background: '#f9fafb',
              borderRadius: 8,
              padding: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              {badge && (
                <span
                  style={{
                    display: 'inline-block',
                    padding: '4px 12px',
                    borderRadius: 999,
                    fontSize: 14,
                    fontWeight: 700,
                    backgroundColor: badge.bg,
                    color: badge.color,
                    border: `1px solid ${badge.color}`,
                  }}
                >
                  {sizeEstimate.complexity_level} — {complexityLabels[sizeEstimate.complexity_level ?? ''] || sizeEstimate.complexity_level}
                </span>
              )}
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: 12,
                marginBottom: 16,
              }}
            >
              <ScoreCard label="乐观" score={sizeEstimate.optimistic_score} color="#10b981" />
              <ScoreCard label="预期" score={sizeEstimate.expected_score} color="#3b82f6" />
              <ScoreCard label="保守" score={sizeEstimate.conservative_score} color="#f59e0b" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12, color: '#6b7280' }}>
              <InfoRow label="功能模块数" value={String(sizeEstimate.module_count ?? '-')} />
              <InfoRow label="接口数" value={String(sizeEstimate.interface_count ?? '-')} />
              <InfoRow label="页面数" value={String(sizeEstimate.page_count ?? '-')} />
              <InfoRow label="技术复杂度" value={sizeEstimate.tech_complexity ?? '-'} />
              <InfoRow label="风险等级" value={sizeEstimate.risk_level ?? '-'} />
            </div>
          </div>
        </section>
      )}

      {/* Current Progress */}
      <section>
        <h3 style={{ margin: '0 0 12px 0', fontSize: 14, fontWeight: 600, color: '#374151' }}>当前进度</h3>
        <div style={{ background: '#f9fafb', borderRadius: 8, padding: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 8 }}>
            <span>{project.current_stage || '未开始'}</span>
            <span style={{ fontWeight: 600 }}>{project.progress_percent}%</span>
          </div>
          <div
            style={{
              width: '100%',
              height: 8,
              background: '#e5e7eb',
              borderRadius: 4,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${project.progress_percent}%`,
                height: '100%',
                background: '#3b82f6',
                borderRadius: 4,
                transition: 'width 0.3s',
              }}
            />
          </div>
        </div>
      </section>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <span style={{ color: '#6b7280' }}>{label}</span>
      <span style={{ color: '#111827', fontWeight: 500, textAlign: 'right', maxWidth: '60%', wordBreak: 'break-all' }}>
        {value}
      </span>
    </div>
  )
}

function ScoreCard({ label, score, color }: { label: string; score: number | null; color: string }) {
  return (
    <div
      style={{
        background: '#fff',
        borderRadius: 6,
        padding: 12,
        textAlign: 'center',
        border: '1px solid #e5e7eb',
      }}
    >
      <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color }}>{score ?? '-'}</div>
    </div>
  )
}

function StagesTab({ stages }: { stages: StageProgress[] }) {
  const statusIcons: Record<string, string> = {
    NOT_STARTED: '○',
    IN_PROGRESS: '◐',
    COMPLETED: '●',
    BLOCKED: '◌',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {stages.length === 0 && (
        <div style={{ color: '#6b7280', textAlign: 'center', padding: 24 }}>暂无阶段数据</div>
      )}
      {stages.map((stage) => (
        <div
          key={stage.stage_id}
          style={{
            background: '#f9fafb',
            borderRadius: 8,
            padding: 14,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <span style={{ fontSize: 18, width: 24, textAlign: 'center' }}>
            {statusIcons[stage.execution_status] || '○'}
          </span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>
              {stage.stage_name}
            </div>
            <div style={{ fontSize: 12, color: '#6b7280' }}>
              状态: {stage.status} {stage.skippable && '· 可跳过'}
            </div>
          </div>
          <div style={{ textAlign: 'right', minWidth: 80 }}>
            <div style={{ fontSize: 13, fontWeight: 600 }}>{stage.progress_percent}%</div>
            {stage.planned_days !== null && (
              <div style={{ fontSize: 11, color: '#6b7280' }}>
                预计 {stage.planned_days} 天
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

function ArtifactsTab({ artifacts }: { artifacts: ArtifactSummary[] }) {
  const typeColors: Record<string, string> = {
    md: '#8b5cf6',
    yaml: '#10b981',
    json: '#f59e0b',
    mermaid: '#06b6d4',
    openapi: '#ef4444',
    txt: '#6b7280',
    other: '#9ca3af',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {artifacts.length === 0 && (
        <div style={{ color: '#6b7280', textAlign: 'center', padding: 24 }}>暂无产物</div>
      )}
      {artifacts.map((art) => (
        <div
          key={art.artifact_id}
          style={{
            background: '#f9fafb',
            borderRadius: 8,
            padding: 12,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: '2px 8px',
              borderRadius: 4,
              background: typeColors[art.file_type] || typeColors.other,
              color: '#fff',
              textTransform: 'uppercase',
            }}
          >
            {art.file_type}
          </span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div
              style={{
                fontSize: 13,
                fontWeight: 500,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {art.file_name}
            </div>
            {art.created_at && (
              <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>
                {new Date(art.created_at).toLocaleString('zh-CN')}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

function LogsTab({ logs }: { logs: OperationLogItem[] }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {logs.length === 0 && (
        <div style={{ color: '#6b7280', textAlign: 'center', padding: 24 }}>暂无操作日志</div>
      )}
      {logs.map((log) => (
        <div
          key={log.log_id}
          style={{
            background: '#f9fafb',
            borderRadius: 8,
            padding: 12,
            borderLeft: '3px solid #3b82f6',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>{log.action}</span>
            {log.created_at && (
              <span style={{ fontSize: 11, color: '#6b7280' }}>
                {new Date(log.created_at).toLocaleString('zh-CN')}
              </span>
            )}
          </div>
          {log.detail && (
            <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>{log.detail}</div>
          )}
          <div style={{ fontSize: 11, color: '#9ca3af' }}>
            操作人: {log.operator_id || '系统'}
            {log.target_type && ` · 目标: ${log.target_type}`}
          </div>
        </div>
      ))}
    </div>
  )
}
