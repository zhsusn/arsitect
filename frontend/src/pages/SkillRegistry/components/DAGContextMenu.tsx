import { useSkillRegistryStore } from '../../../stores/skillRegistryStore'

interface DAGContextMenuProps {
  x: number
  y: number
  nodeId: string | null
  onClose: () => void
}

export function DAGContextMenu({ x, y, nodeId, onClose }: DAGContextMenuProps) {
  const { deleteDAGNode } = useSkillRegistryStore()

  const handleDelete = async () => {
    if (!nodeId) return
    try {
      await deleteDAGNode(nodeId)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : '删除失败')
    }
    onClose()
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: y,
        left: x,
        background: '#fff',
        border: '1px solid #e5e7eb',
        borderRadius: 6,
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        zIndex: 200,
        minWidth: 120,
      }}
    >
      {nodeId ? (
        <>
          <div
            style={{
              padding: '8px 12px',
              fontSize: 13,
              color: '#6b7280',
              borderBottom: '1px solid #f3f4f6',
            }}
          >
            节点: {nodeId.slice(0, 8)}...
          </div>
          <button
            onClick={handleDelete}
            style={{
              display: 'block',
              width: '100%',
              padding: '8px 12px',
              textAlign: 'left',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: 13,
              color: '#ef4444',
            }}
          >
            删除节点
          </button>
        </>
      ) : (
        <div style={{ padding: '8px 12px', fontSize: 13, color: '#6b7280' }}>
          空白区域
        </div>
      )}
    </div>
  )
}
