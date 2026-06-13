import { useState, useMemo } from 'react'
import type { ArtifactFile } from '../../../stores/artifactViewerStore'

interface TreeNode {
  name: string
  path: string
  type: 'directory' | 'file'
  children: TreeNode[]
  file?: ArtifactFile
}

interface ArtifactTreeProps {
  directories: string[]
  files: ArtifactFile[]
  searchQuery: string
  filterType: string
  selectedArtifact: ArtifactFile | null
  onSelect: (artifact: ArtifactFile) => void
}

function buildTree(directories: string[], files: ArtifactFile[]): TreeNode {
  const root: TreeNode = { name: 'root', path: '', type: 'directory', children: [] }

  directories.forEach((dir) => {
    const parts = dir.split('/')
    let current = root
    parts.forEach((part) => {
      let child = current.children.find((c) => c.name === part && c.type === 'directory')
      if (!child) {
        child = {
          name: part,
          path: current.path ? `${current.path}/${part}` : part,
          type: 'directory',
          children: [],
        }
        current.children.push(child)
      }
      current = child
    })
  })

  files.forEach((file) => {
    const lastSlash = file.file_path.lastIndexOf('/')
    const dirPath = lastSlash >= 0 ? file.file_path.substring(0, lastSlash) : ''
    const fileName = lastSlash >= 0 ? file.file_path.substring(lastSlash + 1) : file.file_path

    let current = root
    if (dirPath) {
      const parts = dirPath.split('/')
      parts.forEach((part) => {
        let child = current.children.find((c) => c.name === part && c.type === 'directory')
        if (!child) {
          child = {
            name: part,
            path: current.path ? `${current.path}/${part}` : part,
            type: 'directory',
            children: [],
          }
          current.children.push(child)
        }
        current = child
      })
    }

    current.children.push({
      name: file.file_name || fileName,
      path: file.file_path,
      type: 'file',
      children: [],
      file,
    })
  })

  const sortNodes = (node: TreeNode) => {
    node.children.sort((a, b) => {
      if (a.type === b.type) return a.name.localeCompare(b.name)
      return a.type === 'directory' ? -1 : 1
    })
    node.children.forEach(sortNodes)
  }
  sortNodes(root)

  return root
}

function pruneEmptyDirs(node: TreeNode): TreeNode {
  const newChildren = node.children
    .map(pruneEmptyDirs)
    .filter((child) => {
      if (child.type === 'directory') {
        return child.children.length > 0
      }
      return true
    })
  return { ...node, children: newChildren }
}

function getFileTypeLabel(type: ArtifactFile['file_type']) {
  const labels: Record<string, string> = {
    md: 'MD',
    yaml: 'YAML',
    json: 'JSON',
    mermaid: 'Mermaid',
    openapi: 'API',
    txt: 'TXT',
    other: 'File',
  }
  return labels[type] || 'File'
}

function getFileTypeColor(type: ArtifactFile['file_type']) {
  const colors: Record<string, string> = {
    md: 'text-blue-700 bg-blue-50',
    yaml: 'text-yellow-700 bg-yellow-50',
    json: 'text-green-700 bg-green-50',
    mermaid: 'text-purple-700 bg-purple-50',
    openapi: 'text-orange-700 bg-orange-50',
    txt: 'text-gray-700 bg-gray-50',
    other: 'text-gray-600 bg-gray-50',
  }
  return colors[type] || colors.other
}

export default function ArtifactTree({
  directories,
  files,
  searchQuery,
  filterType,
  selectedArtifact,
  onSelect,
}: ArtifactTreeProps) {
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set())

  const filteredFiles = useMemo(() => {
    return (files || []).filter((file) => {
      const matchSearch =
        !searchQuery || file.file_name.toLowerCase().includes(searchQuery.toLowerCase())
      const matchType = !filterType || file.file_type === filterType
      return matchSearch && matchType
    })
  }, [files, searchQuery, filterType])

  const tree = useMemo(() => {
    const raw = buildTree(directories || [], filteredFiles)
    return pruneEmptyDirs(raw)
  }, [directories, filteredFiles])

  const toggleDir = (path: string) => {
    setExpandedDirs((prev) => {
      const next = new Set(prev)
      if (next.has(path)) {
        next.delete(path)
      } else {
        next.add(path)
      }
      return next
    })
  }

  const renderNode = (node: TreeNode, depth: number) => {
    if (node.type === 'directory') {
      const isExpanded = expandedDirs.has(node.path) || searchQuery.length > 0
      return (
        <div key={node.path}>
          <div
            className="flex items-center gap-1 py-1 px-2 hover:bg-gray-100 cursor-pointer select-none rounded"
            style={{ paddingLeft: `${depth * 12 + 8}px` }}
            onClick={() => toggleDir(node.path)}
          >
            <span className="text-gray-500 text-xs w-4">{isExpanded ? '▼' : '▶'}</span>
            <span className="font-medium text-sm text-gray-700">📁 {node.name}</span>
          </div>
          {isExpanded && node.children.map((child) => renderNode(child, depth + 1))}
        </div>
      )
    }

    const isSelected = selectedArtifact?.artifact_id === node.file?.artifact_id
    const isDeleted = node.file?.external_status === 'deleted'
    return (
      <div
        key={node.path}
        className={`flex items-center gap-2 py-1 px-2 cursor-pointer select-none rounded mx-1 ${
          isSelected ? 'bg-blue-100 text-blue-900' : 'hover:bg-gray-50 text-gray-700'
        }`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={() => {
          if (node.file) {
            if (isDeleted) {
              alert('文件已被外部删除')
            } else {
              onSelect(node.file)
            }
          }
        }}
      >
        <span
          className={`text-xs px-1.5 py-0.5 rounded ${getFileTypeColor(node.file!.file_type)}`}
        >
          {getFileTypeLabel(node.file!.file_type)}
        </span>
        <span className={`text-sm truncate ${isDeleted ? 'line-through text-gray-400' : ''}`}>
          {node.name}
        </span>
        {isDeleted && (
          <span className="text-yellow-500 text-xs" title="文件已被外部删除">⚠️</span>
        )}
      </div>
    )
  }

  return (
    <div className="overflow-auto h-full p-2">
      {tree.children.map((node) => renderNode(node, 0))}
      {tree.children.length === 0 && (
        <div className="p-4 text-center text-gray-400 text-sm">无匹配文件</div>
      )}
    </div>
  )
}
