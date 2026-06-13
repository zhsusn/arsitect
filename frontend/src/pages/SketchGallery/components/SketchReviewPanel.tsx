import { useState } from 'react'
import type { SketchPage } from '../../../services/sketchPage'

interface SketchReviewPanelProps {
  pages: SketchPage[]
  onApprove: (pageId: string) => void
  onReject: (pageId: string, reason: string) => void
  onAddAnnotation: (pageId: string, content: string) => void
}

const STATUS_LABELS: Record<string, string> = {
  DRAFT: '草稿',
  GENERATED: '已生成',
  REVIEW_PENDING: '待审查',
  APPROVED: '已通过',
  REJECTED: '已驳回',
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-600',
  GENERATED: 'bg-blue-100 text-blue-700',
  REVIEW_PENDING: 'bg-yellow-100 text-yellow-700',
  APPROVED: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-700',
}

export default function SketchReviewPanel({ pages, onApprove, onReject, onAddAnnotation }: SketchReviewPanelProps) {
  const [statusFilter, setStatusFilter] = useState<string>('ALL')
  const [selectedPage, setSelectedPage] = useState<string | null>(null)
  const [annotation, setAnnotation] = useState('')
  const [rejectReason, setRejectReason] = useState('')
  const [showRejectModal, setShowRejectModal] = useState(false)

  const filtered = statusFilter === 'ALL' ? pages : pages.filter((p) => (p.status || 'DRAFT') === statusFilter)

  const selected = pages.find((p) => p.page_id === selectedPage)

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="px-4 py-2 border-b flex items-center gap-2 flex-wrap">
        <span className="text-xs font-semibold text-gray-500">状态筛选:</span>
        {(['ALL', 'DRAFT', 'GENERATED', 'REVIEW_PENDING', 'APPROVED', 'REJECTED'] as const).map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-2 py-0.5 text-xs rounded border ${
              statusFilter === s ? 'bg-gray-800 text-white border-gray-800' : 'border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            {s === 'ALL' ? '全部' : STATUS_LABELS[s]}
          </button>
        ))}
        <span className="ml-auto text-xs text-gray-400">{filtered.length} 页</span>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-64 border-r overflow-auto">
          {filtered.map((p) => (
            <button
              key={p.page_id}
              onClick={() => setSelectedPage(p.page_id)}
              className={`w-full text-left px-3 py-2 border-b text-sm transition ${
                selectedPage === p.page_id ? 'bg-blue-50 border-blue-200' : 'hover:bg-gray-50'
              }`}
            >
              <div className="font-medium truncate">{p.page_name}</div>
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${STATUS_COLORS[p.status || 'DRAFT']}`}>
                  {STATUS_LABELS[p.status || 'DRAFT']}
                </span>
              </div>
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-auto p-4">
          {selected ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">{selected.page_name}</h3>
                <div className="flex gap-2">
                  <button
                    onClick={() => onApprove(selected.page_id)}
                    className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    批准
                  </button>
                  <button
                    onClick={() => setShowRejectModal(true)}
                    className="px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    驳回
                  </button>
                </div>
              </div>

              {selected.svg_content ? (
                <div className="border rounded-lg p-4 bg-gray-50" dangerouslySetInnerHTML={{ __html: selected.svg_content }} />
              ) : (
                <div className="border rounded-lg p-8 text-center text-gray-400">无预览内容</div>
              )}

              <div className="border rounded-lg p-3">
                <div className="text-sm font-medium mb-2">添加批注</div>
                <textarea
                  value={annotation}
                  onChange={(e) => setAnnotation(e.target.value)}
                  placeholder="输入批注内容..."
                  className="w-full rounded border border-gray-300 p-2 text-sm min-h-[80px]"
                />
                <button
                  onClick={() => {
                    if (annotation.trim()) {
                      onAddAnnotation(selected.page_id, annotation)
                      setAnnotation('')
                    }
                  }}
                  className="mt-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  提交批注
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-400 mt-20">选择一个页面开始审查</div>
          )}
        </div>
      </div>

      {showRejectModal && selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
            <h4 className="text-base font-semibold mb-3">驳回草图</h4>
            <p className="text-sm text-gray-500 mb-3">页面: {selected.page_name}</p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="请输入驳回原因..."
              className="w-full rounded border border-gray-300 p-2 text-sm min-h-[100px]"
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setShowRejectModal(false)}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={() => {
                  onReject(selected.page_id, rejectReason)
                  setShowRejectModal(false)
                  setRejectReason('')
                }}
                className="px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700"
              >
                确认驳回
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
