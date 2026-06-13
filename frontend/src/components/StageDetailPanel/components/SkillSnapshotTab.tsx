import { useEffect, useState } from 'react'
import { useStageDetailStore } from '../../../stores/stageDetailStore'
import { api } from '../../../services/api'
import type { StageSkill } from '../../../types/stage-detail'

const PATTERN_COLORS: Record<string, string> = {
  generator: 'bg-blue-100 text-blue-700',
  pipeline: 'bg-purple-100 text-purple-700',
  reviewer: 'bg-amber-100 text-amber-700',
  analyzer: 'bg-emerald-100 text-emerald-700',
  inversion: 'bg-rose-100 text-rose-700',
  'tool-wrapper': 'bg-gray-100 text-gray-700',
}

const STATUS_COLORS: Record<string, string> = {
  PARSED: 'bg-green-100 text-green-700',
  PENDING: 'bg-yellow-100 text-yellow-700',
  FAILED: 'bg-red-100 text-red-700',
}

export default function SkillSnapshotTab() {
  const stageId = useStageDetailStore((s) => s.stageId)
  const [skills, setSkills] = useState<StageSkill[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!stageId) return
    let cancelled = false
    setLoading(true)
    setError(null)

    api
      .get<StageSkill[]>(`/v1/stages/${stageId}/skills`)
      .then((res) => {
        if (!cancelled) setSkills(res.data)
      })
      .catch((err) => {
        if (!cancelled) setError(err?.response?.data?.detail || '加载 Skill 列表失败')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [stageId])

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="animate-pulse rounded-lg border border-gray-200 p-4">
            <div className="mb-2 h-4 w-1/3 rounded bg-gray-200" />
            <div className="mb-2 h-3 w-1/2 rounded bg-gray-200" />
            <div className="h-2 w-full rounded bg-gray-200" />
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {error}
      </div>
    )
  }

  if (skills.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-400">
        暂无绑定的 Skill
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {skills.map((skill) => (
        <div
          key={skill.skill_id || skill.skill_name}
          className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
        >
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-sm font-semibold text-gray-800">{skill.skill_name}</h3>
              <p className="mt-0.5 text-xs text-gray-500">{skill.description || '无描述'}</p>
            </div>
            <span
              className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                PATTERN_COLORS[skill.pattern] || PATTERN_COLORS['tool-wrapper']
              }`}
            >
              {skill.pattern}
            </span>
          </div>

          <div className="mt-3 flex items-center gap-4">
            <div className="text-xs text-gray-500">版本: {skill.version}</div>
            <span
              className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                STATUS_COLORS[skill.parse_status] || STATUS_COLORS.PENDING
              }`}
            >
              {skill.parse_status}
            </span>
          </div>

          {skill.tags && skill.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {skill.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-600"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* 置信度进度条（MVP 用 parse_status 模拟） */}
          <div className="mt-3">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>置信度</span>
              <span>{skill.parse_status === 'PARSED' ? '95%' : '60%'}</span>
            </div>
            <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-gray-100">
              <div
                className="h-full rounded-full bg-blue-500 transition-all"
                style={{
                  width: skill.parse_status === 'PARSED' ? '95%' : '60%',
                }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
