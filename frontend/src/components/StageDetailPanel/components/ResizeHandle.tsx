import { useCallback, useEffect, useRef, useState } from 'react'
import { useStageDetailStore } from '../../../stores/stageDetailStore'

export default function ResizeHandle() {
  const setWidth = useStageDetailStore((state) => state.setWidth)
  const [isDragging, setIsDragging] = useState(false)
  const startXRef = useRef(0)
  const startWidthRef = useRef(0)

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      setIsDragging(true)
      startXRef.current = e.clientX
      startWidthRef.current = useStageDetailStore.getState().width
      e.preventDefault()
    },
    []
  )

  useEffect(() => {
    if (!isDragging) return

    const handleMouseMove = (e: MouseEvent) => {
      const delta = startXRef.current - e.clientX
      const newWidth = Math.min(
        Math.max(startWidthRef.current + delta, 400),
        1200
      )
      setWidth(newWidth)
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging, setWidth])

  return (
    <div
      className="absolute top-0 left-0 h-full w-1 cursor-col-resize hover:bg-blue-400"
      onMouseDown={handleMouseDown}
      role="separator"
      aria-label="调整面板宽度"
      style={{ zIndex: 10 }}
    />
  )
}
