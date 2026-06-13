import React, { useCallback, useState } from 'react'

export interface ExportOptions {
  format: 'png' | 'svg'
  width?: number
  height?: number
  background: 'white' | 'transparent' | 'dark'
}

interface ExportPanelProps {
  isOpen: boolean
  onClose: () => void
  svgContent: string
}

async function svgToBlob(
  svgString: string,
  format: 'png' | 'svg',
  options: ExportOptions,
): Promise<Blob> {
  if (format === 'svg') {
    let modified = svgString
    if (options.background && options.background !== 'transparent') {
      const parser = new DOMParser()
      const doc = parser.parseFromString(svgString, 'image/svg+xml')
      const svg = doc.querySelector('svg')
      if (svg) {
        const rect = doc.createElementNS('http://www.w3.org/2000/svg', 'rect')
        rect.setAttribute('width', '100%')
        rect.setAttribute('height', '100%')
        rect.setAttribute(
          'fill',
          options.background === 'dark' ? '#1f2937' : '#ffffff',
        )
        svg.insertBefore(rect, svg.firstChild)
        modified = new XMLSerializer().serializeToString(svg)
      }
    }
    return new Blob([modified], { type: 'image/svg+xml' })
  }

  // PNG export
  return new Promise((resolve, reject) => {
    const parser = new DOMParser()
    const doc = parser.parseFromString(svgString, 'image/svg+xml')
    const svg = doc.querySelector('svg')
    if (!svg) {
      reject(new Error('无效的 SVG'))
      return
    }

    const viewBox = svg.viewBox.baseVal
    const width = options.width || viewBox.width || 800
    const height = options.height || viewBox.height || 600

    svg.setAttribute('width', String(width))
    svg.setAttribute('height', String(height))

    if (options.background && options.background !== 'transparent') {
      const rect = doc.createElementNS('http://www.w3.org/2000/svg', 'rect')
      rect.setAttribute('width', '100%')
      rect.setAttribute('height', '100%')
      rect.setAttribute(
        'fill',
        options.background === 'dark' ? '#1f2937' : '#ffffff',
      )
      svg.insertBefore(rect, svg.firstChild)
    }

    const svgStr = new XMLSerializer().serializeToString(svg)
    const blob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const img = new Image()

    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        URL.revokeObjectURL(url)
        reject(new Error('Canvas 初始化失败'))
        return
      }

      if (options.background === 'transparent') {
        ctx.clearRect(0, 0, width, height)
      } else {
        ctx.fillStyle = options.background === 'dark' ? '#1f2937' : '#ffffff'
        ctx.fillRect(0, 0, width, height)
      }

      ctx.drawImage(img, 0, 0, width, height)
      URL.revokeObjectURL(url)
      canvas.toBlob((b) => {
        if (b) resolve(b)
        else reject(new Error('Canvas 转换失败'))
      }, 'image/png')
    }

    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('SVG 加载失败'))
    }

    img.src = url
  })
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const ExportPanel: React.FC<ExportPanelProps> = ({ isOpen, onClose, svgContent }) => {
  const [format, setFormat] = useState<'png' | 'svg'>('png')
  const [useCustomSize, setUseCustomSize] = useState(false)
  const [width, setWidth] = useState(1200)
  const [height, setHeight] = useState(800)
  const [background, setBackground] = useState<'white' | 'transparent' | 'dark'>('white')
  const [exporting, setExporting] = useState(false)

  const handleExport = useCallback(async () => {
    if (!svgContent) return
    setExporting(true)
    try {
      const options: ExportOptions = {
        format,
        background,
        ...(useCustomSize ? { width, height } : {}),
      }
      const blob = await svgToBlob(svgContent, format, options)
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
      const filename = `c4-export-${timestamp}.${format}`
      downloadBlob(blob, filename)
      onClose()
    } catch (err) {
      alert(err instanceof Error ? err.message : '导出失败')
    } finally {
      setExporting(false)
    }
  }, [svgContent, format, background, useCustomSize, width, height, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-[480px] p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-semibold text-gray-900">导出设置</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            aria-label="关闭"
          >
            ×
          </button>
        </div>

        <div className="space-y-5">
          {/* Format */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">格式</label>
            <div className="flex gap-3">
              {(['png', 'svg'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFormat(f)}
                  className={`px-4 py-2 rounded border text-sm capitalize transition-colors ${
                    format === f
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {f.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {/* Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">尺寸</label>
            <div className="flex items-center gap-3 mb-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={!useCustomSize}
                  onChange={() => setUseCustomSize(false)}
                  className="accent-blue-600"
                />
                <span className="text-sm text-gray-700">默认</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  checked={useCustomSize}
                  onChange={() => setUseCustomSize(true)}
                  className="accent-blue-600"
                />
                <span className="text-sm text-gray-700">自定义</span>
              </label>
            </div>
            {useCustomSize && (
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  value={width}
                  onChange={(e) => setWidth(Number(e.target.value))}
                  min={100}
                  className="w-24 px-3 py-2 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="宽"
                />
                <span className="text-gray-400">×</span>
                <input
                  type="number"
                  value={height}
                  onChange={(e) => setHeight(Number(e.target.value))}
                  min={100}
                  className="w-24 px-3 py-2 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="高"
                />
                <span className="text-xs text-gray-500">px</span>
              </div>
            )}
          </div>

          {/* Background */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">背景</label>
            <div className="flex gap-3">
              {(
                [
                  { key: 'white', label: '白色' },
                  { key: 'transparent', label: '透明' },
                  { key: 'dark', label: '深色' },
                ] as const
              ).map((b) => (
                <button
                  key={b.key}
                  onClick={() => setBackground(b.key)}
                  className={`px-4 py-2 rounded border text-sm transition-colors ${
                    background === b.key
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {b.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleExport}
            disabled={exporting || !svgContent}
            className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {exporting ? '导出中...' : '确认导出'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default React.memo(ExportPanel)
