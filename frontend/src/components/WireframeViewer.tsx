import { useEffect, useState } from 'react'

interface WireframePage {
  id: string
  title: string
  type: string
}

interface WireframeResponse {
  svg: string
  page_count: number
  edge_count: number
  orphan_pages: string[]
  pages: WireframePage[]
}

interface Props {
  projectId: string
}

export function WireframeViewer({ projectId }: Props) {
  const [data, setData] = useState<WireframeResponse | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const res = await fetch(`/api/v1/c4/wireframe?project_id=${projectId}`)
        const d = await res.json()
        setData(d)
      } catch (e) {
        console.error(e)
      }
      setLoading(false)
    }
    load()
  }, [projectId])

  return (
    <div className="wireframe-viewer">
      <div className="flex gap-2 mb-2 items-center">
        {data && (
          <span className="text-xs text-gray-500">
            {data.page_count} pages, {data.edge_count} edges
          </span>
        )}
        {data && data.orphan_pages.length > 0 && (
          <span className="text-xs text-orange-500">
            {data.orphan_pages.length} orphan pages
          </span>
        )}
      </div>
      <div className="bg-white border rounded p-2 overflow-auto">
        {loading && <div className="text-gray-400 p-4">Loading...</div>}
        {data && (
          <div
            className="wireframe-svg"
            dangerouslySetInnerHTML={{ __html: data.svg }}
          />
        )}
      </div>
      {data && data.pages.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {data.pages.map((p) => (
            <span
              key={p.id}
              className="text-xs px-2 py-0.5 bg-gray-100 rounded text-gray-600"
            >
              {p.title} ({p.type})
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
