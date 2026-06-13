import { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import mermaid from 'mermaid'

interface Artifact {
  path: string
  content: string
  format: 'md' | 'mmd' | 'yaml' | 'json' | 'svg' | 'html' | 'txt'
}

interface Props {
  artifact: Artifact
}

export function ArtifactRenderer({ artifact }: Props) {
  const { format, content } = artifact
  switch (format) {
    case 'md':
      return <MarkdownView content={content} />
    case 'mmd':
      return <MermaidView content={content} />
    case 'yaml':
    case 'json':
      return <CodeView content={content} lang={format} />
    case 'svg':
      return (
        <div
          className="artifact-svg"
          dangerouslySetInnerHTML={{ __html: content }}
          style={{ maxWidth: '100%', overflow: 'auto' }}
        />
      )
    case 'html':
      return <HTMLView content={content} />
    default:
      return <CodeView content={content} lang="text" />
  }
}

function MarkdownView({ content }: { content: string }) {
  return (
    <div className="artifact-md prose max-w-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  )
}

function MermaidView({ content }: { content: string }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (ref.current) {
      ref.current.innerHTML = `<div class="mermaid">${content}</div>`
      void mermaid.run({ nodes: ref.current.querySelectorAll('.mermaid') })
    }
  }, [content])
  return <div ref={ref} />
}

function CodeView({ content, lang }: { content: string; lang: string }) {
  return (
    <pre className="artifact-code bg-gray-900 text-gray-100 p-4 rounded overflow-auto text-sm">
      <code className={`language-${lang}`}>{content}</code>
    </pre>
  )
}

function HTMLView({ content }: { content: string }) {
  const ref = useRef<HTMLIFrameElement>(null)
  useEffect(() => {
    const doc = ref.current?.contentDocument
    if (doc) {
      doc.open()
      doc.write(content)
      doc.close()
    }
  }, [content])
  return (
    <iframe
      ref={ref}
      style={{ width: '100%', height: '600px', border: '1px solid #ddd' }}
      sandbox="allow-scripts"
      title="preview"
    />
  )
}
