import { useCallback, useEffect, useMemo, useState } from 'react'
import { useProjectContext } from '../../App'
import {
  type CoverageScan,
  type CoverageScanItem,
  listCoverageScans,
  createCoverageScan,
  getCoverageScan,
  toggleWriteback,
  applyWriteback,
  reviewItem,
} from '../../services/binding'

type TabKey = 'gap' | 'redundant' | 'matched' | 'diff'

export default function BindingPanel() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId
  const [scans, setScans] = useState<CoverageScan[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeScanId, setActiveScanId] = useState<string | null>(null)
  const [scanItems, setScanItems] = useState<CoverageScanItem[]>([])
  const [tab, setTab] = useState<TabKey>('gap')
  const [scanLoading, setScanLoading] = useState(false)
  const [writebackLoading, setWritebackLoading] = useState(false)
  const [showDiffModal, setShowDiffModal] = useState(false)
  const [selectedDiffItem, setSelectedDiffItem] = useState<CoverageScanItem | null>(null)

  const loadScans = useCallback(async () => {
    if (!projectId.trim()) return
    setLoading(true)
    setError(null)
    try {
      const data = await listCoverageScans(projectId)
      setScans(data)
      if (data.length > 0 && !activeScanId) {
        setActiveScanId(data[0].scan_id)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [projectId, activeScanId])

  useEffect(() => {
    loadScans()
  }, [loadScans])

  useEffect(() => {
    if (!activeScanId) return
    const loadItems = async () => {
      setScanLoading(true)
      try {
        const detail = await getCoverageScan(activeScanId)
        setScanItems(detail.items)
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : '加载扫描详情失败')
      } finally {
        setScanLoading(false)
      }
    }
    loadItems()
  }, [activeScanId])

  const handleRunScan = async () => {
    if (!projectId.trim()) return
    setLoading(true)
    setError(null)
    try {
      const scan = await createCoverageScan(projectId)
      setScans((prev) => [scan, ...prev])
      setActiveScanId(scan.scan_id)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '扫描失败')
    } finally {
      setLoading(false)
    }
  }

  const activeScan = useMemo(
    () => scans.find((s) => s.scan_id === activeScanId) || null,
    [scans, activeScanId]
  )

  const filteredItems = useMemo(
    () => scanItems.filter((i) => i.result_type === tab),
    [scanItems, tab]
  )

  const handleToggle = async (item: CoverageScanItem) => {
    try {
      const updated = await toggleWriteback(item.item_id, !item.is_selected_for_writeback)
      setScanItems((prev) =>
        prev.map((i) => (i.item_id === updated.item_id ? updated : i))
      )
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '操作失败')
    }
  }

  const handleReview = async (itemId: string, status: 'approved' | 'rejected') => {
    try {
      const updated = await reviewItem(itemId, status)
      setScanItems((prev) =>
        prev.map((i) => (i.item_id === updated.item_id ? updated : i))
      )
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '评审失败')
    }
  }

  const handleWriteback = async () => {
    if (!activeScanId) return
    setWritebackLoading(true)
    try {
      const res = await applyWriteback(activeScanId)
      alert(`回写完成: 新建 ${res.created_count} 个接口契约`)
      await loadScans()
      if (activeScanId) {
        const detail = await getCoverageScan(activeScanId)
        setScanItems(detail.items)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '回写失败')
    } finally {
      setWritebackLoading(false)
    }
  }

  const tabLabels: Record<TabKey, string> = {
    gap: '缺失 (Gap)',
    redundant: '冗余 (Redundant)',
    matched: '匹配 (Matched)',
    diff: '差异 (Diff)',
  }

  const coverageColor = (pct: number | null) => {
    if (pct === null) return '#6b7280'
    if (pct >= 90) return '#16a34a'
    if (pct >= 70) return '#ca8a04'
    return '#dc2626'
  }

  if (!projectId) {
    return <div style={{ padding: 40, color: '#6b7280' }}>请先在顶部选择项目</div>
  }

  return (
    <div style={{ maxWidth: 1120 }}>
      <h1 style={{ marginBottom: 16 }}>原型-架构双向绑定</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <button onClick={handleRunScan} disabled={!projectId.trim() || loading}>
          {loading ? '扫描中...' : '开始检测'}
        </button>
        {activeScan && (
          <button onClick={handleWriteback} disabled={writebackLoading || (activeScan.gap_count ?? 0) === 0}>
            {writebackLoading ? '回写中...' : '回写缺失接口'}
          </button>
        )}
      </div>

      {error && (
        <div style={{ color: '#ef4444', marginBottom: 16 }}>错误: {error}</div>
      )}

      {/* Scan list */}
      {scans.length > 0 && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
          {scans.map((s) => (
            <button
              key={s.scan_id}
              onClick={() => setActiveScanId(s.scan_id)}
              style={{
                padding: '6px 12px',
                borderRadius: 6,
                border: '1px solid #e5e7eb',
                background: activeScanId === s.scan_id ? '#eff6ff' : '#fff',
                cursor: 'pointer',
                fontSize: 13,
              }}
            >
              <span style={{ fontWeight: 600 }}>{s.scan_id.slice(0, 8)}</span>
              <span style={{ marginLeft: 8, color: coverageColor(s.coverage_percent) }}>
                {s.coverage_percent ?? 0}%
              </span>
            </button>
          ))}
        </div>
      )}

      {scans.length === 0 && !loading && (
        <div style={{ color: '#6b7280', padding: 24, textAlign: 'center' }}>
          暂无扫描记录，请选择项目后点击"开始检测"
        </div>
      )}

      {activeScan && (
        <div>
          {/* Stats cards */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
            <StatCard label="覆盖率" value={`${activeScan.coverage_percent ?? 0}%`} color={coverageColor(activeScan.coverage_percent)} />
            <StatCard label="缺失" value={String(activeScan.gap_count ?? 0)} color="#dc2626" />
            <StatCard label="冗余" value={String(activeScan.redundant_count ?? 0)} color="#2563eb" />
            <StatCard label="差异" value={String(activeScan.diff_count ?? 0)} color="#ca8a04" />
            <StatCard label="Wireframe 页" value={String(activeScan.wireframe_page_count ?? 0)} color="#6b7280" />
            <StatCard label="OpenUI 页" value={String(activeScan.openui_page_count ?? 0)} color="#6b7280" />
            <StatCard label="C4 接口" value={String(activeScan.c4_interface_count ?? 0)} color="#6b7280" />
          </div>

          {/* Tabs */}
          <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #e5e7eb', marginBottom: 12 }}>
            {(Object.keys(tabLabels) as TabKey[]).map((k) => (
              <button
                key={k}
                onClick={() => setTab(k)}
                style={{
                  padding: '8px 14px',
                  border: 'none',
                  borderBottom: tab === k ? '2px solid #2563eb' : '2px solid transparent',
                  background: 'transparent',
                  cursor: 'pointer',
                  fontWeight: tab === k ? 600 : 400,
                  color: tab === k ? '#1d4ed8' : '#374151',
                }}
              >
                {tabLabels[k]} ({scanItems.filter((i) => i.result_type === k).length})
              </button>
            ))}
          </div>

          {scanLoading ? (
            <div style={{ color: '#6b7280', padding: 24, textAlign: 'center' }}>加载中...</div>
          ) : filteredItems.length === 0 ? (
            <div style={{ color: '#6b7280', padding: 24, textAlign: 'center' }}>该分类下无数据</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {filteredItems.map((item) => (
                <div
                  key={item.item_id}
                  style={{
                    padding: 12,
                    border: '1px solid #e5e7eb',
                    borderRadius: 6,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    gap: 12,
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>{item.interface_name}</div>
                    <div style={{ fontSize: 13, color: '#4b5563', fontFamily: 'monospace' }}>
                      {item.method_type} {item.endpoint_path || '—'}
                    </div>
                    <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
                      来源: {item.source_location} · {item.source_type}
                    </div>
                    {item.actual_params && (
                      <div style={{ fontSize: 12, color: '#92400e', marginTop: 4, background: '#fef3c7', padding: '4px 8px', borderRadius: 4 }}>
                        参数差异: {item.actual_params}
                      </div>
                    )}
                    {item.review_status && (
                      <span
                        style={{
                          display: 'inline-block',
                          marginTop: 6,
                          fontSize: 11,
                          padding: '2px 8px',
                          borderRadius: 12,
                          background: item.review_status === 'approved' ? '#dcfce7' : '#fee2e2',
                          color: item.review_status === 'approved' ? '#166534' : '#991b1b',
                        }}
                      >
                        {item.review_status === 'approved' ? '已批准' : '已驳回'}
                      </span>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0 }}>
                    {item.result_type === 'gap' && (
                      <>
                        <label style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={item.is_selected_for_writeback}
                            onChange={() => handleToggle(item)}
                          />
                          回写
                        </label>
                        <button onClick={() => handleReview(item.item_id, 'approved')} style={{ fontSize: 12 }}>
                          批准
                        </button>
                        <button onClick={() => handleReview(item.item_id, 'rejected')} style={{ fontSize: 12 }}>
                          驳回
                        </button>
                      </>
                    )}
                    {item.result_type === 'diff' && (
                      <button
                        onClick={() => { setSelectedDiffItem(item); setShowDiffModal(true) }}
                        style={{ fontSize: 12, padding: '4px 10px', background: '#eff6ff', color: '#2563eb', border: '1px solid #bfdbfe', borderRadius: 4, cursor: 'pointer' }}
                      >
                        同步差异
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 差异同步弹窗 */}
      {showDiffModal && selectedDiffItem && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
          <div style={{ background: '#fff', borderRadius: 8, padding: 24, width: 520, maxHeight: '70vh', overflow: 'auto' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600 }}>接口一致性差异同步</h3>
            <div style={{ marginBottom: 12, padding: 12, background: '#f9fafb', borderRadius: 6, fontSize: 13 }}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>{selectedDiffItem.interface_name}</div>
              <div style={{ color: '#6b7280', fontFamily: 'monospace' }}>{selectedDiffItem.method_type} {selectedDiffItem.endpoint_path}</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 16 }}>
              <div style={{ padding: 10, background: '#fef2f2', borderRadius: 4, border: '1px solid #fecaca' }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#dc2626', marginBottom: 4 }}>OpenAPI 定义</div>
                <div style={{ fontSize: 12, color: '#4b5563', fontFamily: 'monospace' }}>{selectedDiffItem.expected_params || '—'}</div>
              </div>
              <div style={{ padding: 10, background: '#eff6ff', borderRadius: 4, border: '1px solid #bfdbfe' }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#2563eb', marginBottom: 4 }}>OpenUI 绑定</div>
                <div style={{ fontSize: 12, color: '#4b5563', fontFamily: 'monospace' }}>{selectedDiffItem.actual_params || '—'}</div>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button
                onClick={() => setShowDiffModal(false)}
                style={{ padding: '8px 16px', fontSize: 13, border: '1px solid #e5e7eb', background: '#fff', borderRadius: 4, cursor: 'pointer' }}
              >
                取消
              </button>
              <button
                onClick={() => { setShowDiffModal(false); console.log('同步到 OpenUI', selectedDiffItem.item_id) }}
                style={{ padding: '8px 16px', fontSize: 13, background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
              >
                同步到 OpenUI
              </button>
              <button
                onClick={() => { setShowDiffModal(false); console.log('同步到 OpenAPI', selectedDiffItem.item_id) }}
                style={{ padding: '8px 16px', fontSize: 13, background: '#16a34a', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
              >
                同步到 OpenAPI
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ padding: '10px 14px', border: '1px solid #e5e7eb', borderRadius: 6, minWidth: 90, textAlign: 'center' }}>
      <div style={{ fontSize: 18, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{label}</div>
    </div>
  )
}
