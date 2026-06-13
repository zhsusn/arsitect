import { useEffect, useRef, useState } from 'react'

interface Props {
  projectId: string
}

export function SketchViewer({ projectId }: Props) {
  const [html, setHtml] = useState('')
  const [loading, setLoading] = useState(false)
  const iframeRef = useRef<HTMLIFrameElement>(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const res = await fetch(`/api/v1/c4/sketch?project_id=${projectId}`)
        const d = await res.json()
        setHtml(d.html)
      } catch (e) {
        console.error(e)
      }
      setLoading(false)
    }
    load()
  }, [projectId])

  useEffect(() => {
    const doc = iframeRef.current?.contentDocument
    if (doc && html) {
      doc.open()
      doc.write(html)
      doc.close()
    }
  }, [html])

  return (
    <div className="sketch-viewer">
      <div className="flex items-center gap-2 mb-2">
        {loading && <span className="text-xs text-gray-400">Loading...</span>}
      </div>
      <iframe
        ref={iframeRef}
        style={{ width: '100%', height: '600px', border: '1px solid #ddd' }}
        sandbox="allow-scripts allow-same-origin"
        title="sketch-preview"
      />
    </div>
  )
}
