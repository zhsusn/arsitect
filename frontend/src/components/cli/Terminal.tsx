import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react'
import { Terminal as XTerm, type ITerminalOptions } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

export interface TerminalHandle {
  write: (text: string) => void
  clear: () => void
  focus: () => void
}

interface TerminalProps {
  onSubmit: (line: string) => void
  prompt?: string
}

export default forwardRef<TerminalHandle, TerminalProps>(function Terminal(
  { onSubmit, prompt = '$ ' },
  ref,
) {
  const containerRef = useRef<HTMLDivElement>(null)
  const terminalRef = useRef<XTerm | null>(null)
  const inputRef = useRef('')
  const onSubmitRef = useRef(onSubmit)

  useEffect(() => {
    onSubmitRef.current = onSubmit
  })

  useImperativeHandle(
    ref,
    () => ({
      write: (text) => {
        terminalRef.current?.write(text)
      },
      clear: () => {
        terminalRef.current?.clear()
      },
      focus: () => {
        terminalRef.current?.focus()
      },
    }),
    [],
  )

  useEffect(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    let rafId = 0
    let timeoutId = 0
    let disposed = false

    const options: ITerminalOptions = {
      fontSize: 14,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      cursorBlink: true,
      cursorStyle: 'block',
      theme: {
        background: '#0f172a',
        foreground: '#e2e8f0',
        cursor: '#38bdf8',
        selectionBackground: '#334155',
      },
      convertEol: true,
      scrollback: 1000,
    }

    const term = new XTerm(options)
    const fit = new FitAddon()
    term.loadAddon(fit)
    terminalRef.current = term

    const initTerminal = () => {
      if (disposed || !container.isConnected) return
      // xterm.js crashes if the container has no layout dimensions.
      // Retry on the next frame until it does.
      if (container.clientWidth === 0 || container.clientHeight === 0) {
        rafId = requestAnimationFrame(initTerminal)
        return
      }
      term.open(container)
      term.writeln('\x1b[36m[AI]\x1b[0m 欢迎使用 AI CLI 终端')
      term.writeln('\x1b[90m[系统]\x1b[0m 输入命令后按回车发送，或点击快捷操作按钮')
      term.write(prompt)
      fit.fit()
    }

    // Defer initialization until React has committed the modal layout.
    timeoutId = window.setTimeout(() => {
      rafId = requestAnimationFrame(initTerminal)
    }, 0)

    const disposable = term.onKey(({ key, domEvent }) => {
      const printable =
        !domEvent.altKey && !domEvent.ctrlKey && !domEvent.metaKey && key.length === 1
      if (domEvent.key === 'Enter') {
        const line = inputRef.current
        inputRef.current = ''
        term.writeln('')
        onSubmitRef.current(line)
      } else if (domEvent.key === 'Backspace') {
        if (inputRef.current.length > 0) {
          inputRef.current = inputRef.current.slice(0, -1)
          term.write('\b \b')
        }
      } else if (printable) {
        inputRef.current += key
        term.write(key)
      }
    })

    const handleResize = () => {
      fit.fit()
    }
    window.addEventListener('resize', handleResize)

    return () => {
      disposed = true
      window.clearTimeout(timeoutId)
      cancelAnimationFrame(rafId)
      window.removeEventListener('resize', handleResize)
      disposable.dispose()
      term.dispose()
      terminalRef.current = null
    }
  }, [prompt])

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
})
