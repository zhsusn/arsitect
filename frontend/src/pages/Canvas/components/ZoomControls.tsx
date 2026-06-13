import { useCallback, useEffect, useRef } from 'react'
import { useReactFlow, useStore } from '@xyflow/react'

interface ZoomControlsProps {
  className?: string
}

export default function ZoomControls({ className }: ZoomControlsProps) {
  const { zoomIn, zoomOut, fitView, zoomTo } = useReactFlow()
  const storeZoom = useStore((s) => s.transform[2])
  const zoom = Math.round(storeZoom * 100)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const startContinuousZoom = useCallback(
    (action: 'in' | 'out') => {
      const step = () => {
        if (action === 'in') zoomIn({ duration: 100 })
        else zoomOut({ duration: 100 })
      }
      step()
      timeoutRef.current = setTimeout(() => {
        intervalRef.current = setInterval(step, 120)
      }, 300)
    },
    [zoomIn, zoomOut],
  )

  const stopContinuousZoom = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    if (intervalRef.current) clearInterval(intervalRef.current)
    timeoutRef.current = null
    intervalRef.current = null
  }, [])

  const handleFitView = useCallback(() => {
    fitView({ duration: 300, padding: 0.2 })
  }, [fitView])

  const handleResetZoom = useCallback(() => {
    zoomTo(1, { duration: 300 })
  }, [zoomTo])

  useEffect(() => {
    return () => stopContinuousZoom()
  }, [stopContinuousZoom])

  return (
    <div
      className={`flex items-center gap-1 bg-white border border-gray-200 rounded-lg shadow-sm px-2 py-1 ${className || ''}`}
    >
      <button
        onMouseDown={() => startContinuousZoom('out')}
        onMouseUp={stopContinuousZoom}
        onMouseLeave={stopContinuousZoom}
        onTouchStart={() => startContinuousZoom('out')}
        onTouchEnd={stopContinuousZoom}
        className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-gray-100 text-gray-600 text-lg select-none"
        title="缩小"
      >
        −
      </button>

      <span className="min-w-[48px] text-center text-xs font-medium text-gray-700 tabular-nums">
        {zoom}%
      </span>

      <button
        onMouseDown={() => startContinuousZoom('in')}
        onMouseUp={stopContinuousZoom}
        onMouseLeave={stopContinuousZoom}
        onTouchStart={() => startContinuousZoom('in')}
        onTouchEnd={stopContinuousZoom}
        className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-gray-100 text-gray-600 text-lg select-none"
        title="放大"
      >
        +
      </button>

      <div className="w-px h-5 bg-gray-200 mx-1" />

      <button
        onClick={handleFitView}
        className="px-2 h-8 flex items-center justify-center rounded-md hover:bg-gray-100 text-xs text-gray-600"
        title="适应视图"
      >
        适应
      </button>

      <button
        onClick={handleResetZoom}
        className="px-2 h-8 flex items-center justify-center rounded-md hover:bg-gray-100 text-xs text-gray-600"
        title="100%"
      >
        100%
      </button>
    </div>
  )
}
