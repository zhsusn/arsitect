import React from 'react'
import type { C4NodeInfo } from '../utils/c4Parser'

interface NodeDetailPanelProps {
  node: C4NodeInfo | null
  isOpen: boolean
  onClose: () => void
  currentLevel: string
}

const TYPE_LABELS: Record<string, string> = {
  Person: '人员',
  System: '系统',
  Container: '容器',
  Component: '组件',
  Boundary: '边界',
  unknown: '节点',
}

const TYPE_COLORS: Record<string, string> = {
  Person: 'bg-blue-100 text-blue-800',
  System: 'bg-green-100 text-green-800',
  Container: 'bg-purple-100 text-purple-800',
  Component: 'bg-orange-100 text-orange-800',
  Boundary: 'bg-gray-100 text-gray-800',
  unknown: 'bg-gray-100 text-gray-800',
}

const NodeDetailPanel: React.FC<NodeDetailPanelProps> = ({ node, isOpen, onClose, currentLevel }) => {
  const openInVscode = () => {
    if (node?.filePath) {
      window.open(`vscode://${node.filePath}`, '_blank')
    }
  }

  const showVscodeButton = (currentLevel === 'L3' || currentLevel === 'L4') && !!node?.filePath

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="absolute inset-0 bg-black/10 z-40"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Panel */}
      <div
        className={`absolute right-0 top-0 bottom-0 w-[400px] bg-white shadow-xl border-l border-gray-200 transform transition-transform duration-300 ease-in-out z-50 flex flex-col ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-800">节点详情</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors text-2xl leading-none"
            aria-label="关闭"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-5">
          {node ? (
            <div className="space-y-5">
              {/* Name & Type */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                      TYPE_COLORS[node.type] || TYPE_COLORS.unknown
                    }`}
                  >
                    {TYPE_LABELS[node.type] || node.type}
                  </span>
                </div>
                <h2 className="text-xl font-bold text-gray-900">{node.name}</h2>
                <p className="text-sm text-gray-500 font-mono mt-1">ID: {node.id}</p>
              </div>

              {/* Description */}
              {node.description && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-1">描述</h4>
                  <p className="text-sm text-gray-600 leading-relaxed">{node.description}</p>
                </div>
              )}

              {/* Tech Stack */}
              {node.tech && node.tech.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">技术栈</h4>
                  <div className="flex flex-wrap gap-2">
                    {node.tech.map((t, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-1 bg-gray-100 text-gray-700 text-xs rounded-full border border-gray-200"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* File Path */}
              {node.filePath && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-1">关联文件</h4>
                  <p className="text-sm text-gray-600 font-mono break-all bg-gray-50 p-2 rounded border border-gray-100">
                    {node.filePath}
                  </p>
                </div>
              )}

              {/* Interfaces */}
              {node.interfaces && node.interfaces.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">关联接口</h4>
                  <ul className="space-y-1">
                    {node.interfaces.map((iface, i) => (
                      <li
                        key={i}
                        className="text-sm text-gray-600 font-mono bg-gray-50 px-2 py-1 rounded border border-gray-100"
                      >
                        {iface}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Actions */}
              <div className="pt-2 space-y-2">
                {showVscodeButton && (
                  <button
                    onClick={openInVscode}
                    className="w-full px-4 py-2 bg-gray-900 text-white text-sm rounded hover:bg-gray-800 transition-colors"
                  >
                    在编辑器中打开 (VS Code)
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="text-gray-400 text-center mt-10">未选择节点</div>
          )}
        </div>
      </div>
    </>
  )
}

export default React.memo(NodeDetailPanel)
