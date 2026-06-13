import React, { useCallback, useEffect, useMemo, useRef } from 'react'

interface C4EditorProps {
  value: string
  onChange: (value: string) => void
  validationErrors?: Array<{ line: number; message: string }>
}

const KEYWORDS_C4 = [
  'Person',
  'System',
  'Container',
  'Component',
  'Rel',
  'System_Boundary',
  'Container_Boundary',
  'Enterprise_Boundary',
  'Boundary',
]
const KEYWORDS_MERMAID = [
  'graph',
  'flowchart',
  'subgraph',
  'end',
  'direction',
  'click',
  'class',
  'classDef',
  'linkStyle',
  'style',
]
const DIRECTIONS = ['TD', 'LR', 'RL', 'BT', 'TB']

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function highlightLine(line: string, isError: boolean): string {
  let html = escapeHtml(line)

  // Comments
  html = html.replace(/(%%.*$)/g, '<span class="text-gray-400">$1</span>')

  // C4 Keywords
  html = html.replace(
    new RegExp(`\\b(${KEYWORDS_C4.join('|')})\\b`, 'g'),
    '<span class="text-purple-600 font-semibold">$1</span>',
  )

  // Mermaid keywords
  html = html.replace(
    new RegExp(`\\b(${KEYWORDS_MERMAID.join('|')})\\b`, 'g'),
    '<span class="text-blue-600 font-semibold">$1</span>',
  )

  // Directions
  html = html.replace(
    new RegExp(`\\b(${DIRECTIONS.join('|')})\\b`, 'g'),
    '<span class="text-orange-500 font-semibold">$1</span>',
  )

  // Strings
  html = html.replace(/"([^"]*)"/g, '<span class="text-green-600">"$1"</span>')

  if (isError) {
    html = `<span class="bg-red-50 underline decoration-red-500 decoration-wavy">${html}</span>`
  }

  return html
}

const C4Editor: React.FC<C4EditorProps> = ({ value, onChange, validationErrors }) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const preRef = useRef<HTMLPreElement>(null)
  const lineNoRef = useRef<HTMLDivElement>(null)
  const errorLineSet = useMemo(() => {
    const set = new Set<number>()
    validationErrors?.forEach((e) => set.add(e.line))
    return set
  }, [validationErrors])

  const lines = useMemo(() => value.split('\n'), [value])

  const highlightedHtml = useMemo(() => {
    return lines
      .map((line, i) => {
        const lineNo = i + 1
        const html = highlightLine(line, errorLineSet.has(lineNo))
        return html
      })
      .join('\n')
  }, [lines, errorLineSet])

  const handleScroll = useCallback(() => {
    const ta = textareaRef.current
    const pre = preRef.current
    const ln = lineNoRef.current
    if (!ta || !pre || !ln) return
    pre.scrollTop = ta.scrollTop
    pre.scrollLeft = ta.scrollLeft
    ln.scrollTop = ta.scrollTop
  }, [])

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      onChange(e.target.value)
    },
    [onChange],
  )

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault()
      const ta = e.currentTarget
      const start = ta.selectionStart
      const end = ta.selectionEnd
      const newValue = ta.value.substring(0, start) + '  ' + ta.value.substring(end)
      onChange(newValue)
      requestAnimationFrame(() => {
        ta.selectionStart = ta.selectionEnd = start + 2
      })
    }
  }, [onChange])

  useEffect(() => {
    // Ensure scroll sync when content changes
    handleScroll()
  }, [value, handleScroll])

  return (
    <div className="flex h-full border rounded bg-white overflow-hidden">
      {/* Line numbers */}
      <div
        ref={lineNoRef}
        className="w-12 bg-gray-50 text-gray-400 text-right pr-2 py-3 text-sm font-mono select-none overflow-hidden shrink-0"
      >
        {lines.map((_, i) => {
          const lineNo = i + 1
          const hasError = errorLineSet.has(lineNo)
          return (
            <div
              key={i}
              className={`leading-6 ${hasError ? 'text-red-600 bg-red-50 font-bold' : ''}`}
            >
              {lineNo}
            </div>
          )
        })}
      </div>

      {/* Editor area */}
      <div className="relative flex-1 min-w-0">
        {/* Highlight layer */}
        <pre
          ref={preRef}
          className="absolute inset-0 m-0 p-3 font-mono text-sm pointer-events-none overflow-hidden whitespace-pre text-gray-800 leading-6"
          aria-hidden="true"
          dangerouslySetInnerHTML={{ __html: highlightedHtml + '\n' }}
        />

        {/* Input layer */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onScroll={handleScroll}
          onKeyDown={handleKeyDown}
          spellCheck={false}
          autoCapitalize="off"
          autoComplete="off"
          autoCorrect="off"
          className="absolute inset-0 w-full h-full p-3 font-mono text-sm resize-none border-none outline-none bg-transparent text-transparent caret-black whitespace-pre overflow-auto leading-6"
        />
      </div>
    </div>
  )
}

export default React.memo(C4Editor)
