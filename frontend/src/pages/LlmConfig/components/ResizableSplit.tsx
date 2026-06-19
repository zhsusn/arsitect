import { useEffect, useRef, useState } from 'react'

interface ResizableSplitProps {
  left: React.ReactNode
  right: React.ReactNode
  defaultWidth?: number
  minWidth?: number
  maxWidth?: number
  storageKey?: string
  className?: string
}

export default function ResizableSplit({
  left,
  right,
  defaultWidth = 340,
  minWidth = 280,
  maxWidth = 480,
  storageKey = 'llm-config-master-width',
  className = '',
}: ResizableSplitProps) {
  const [width, setWidth] = useState(() => {
    try {
      const saved = localStorage.getItem(storageKey)
      return saved ? Math.min(maxWidth, Math.max(minWidth, parseInt(saved, 10))) : defaultWidth
    } catch {
      return defaultWidth
    }
  })
  const [isDragging, setIsDragging] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isDragging) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const nextWidth = Math.min(maxWidth, Math.max(minWidth, e.clientX - rect.left))
      setWidth(nextWidth)
    }

    const handleMouseUp = () => {
      setIsDragging(false)
      try {
        localStorage.setItem(storageKey, String(width))
      } catch {
        // ignore storage errors
      }
    }

    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp, { once: true })

    return () => {
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      window.removeEventListener('mousemove', handleMouseMove)
    }
  }, [isDragging, maxWidth, minWidth, storageKey, width])

  return (
    <div ref={containerRef} className={`flex h-full ${className}`}>
      <div
        className="shrink-0 h-full overflow-hidden flex flex-col border-r border-gray-200 bg-white"
        style={{ width }}
      >
        {left}
      </div>
      <div
        className="w-1 shrink-0 cursor-col-resize hover:bg-blue-200 active:bg-blue-300 transition-colors"
        onMouseDown={() => setIsDragging(true)}
        role="separator"
        aria-label="调整左右分栏宽度"
      />
      <div className="flex-1 min-w-0 h-full overflow-hidden flex flex-col bg-white">{right}</div>
    </div>
  )
}
