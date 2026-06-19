import { useEffect, useRef } from 'react'

export function useUnsavedGuard(hasUnsavedChanges: boolean): void {
  const guardRef = useRef(hasUnsavedChanges)
  guardRef.current = hasUnsavedChanges

  useEffect(() => {
    const handler = (event: BeforeUnloadEvent) => {
      if (!guardRef.current) return
      event.preventDefault()
      // 现代浏览器需要 returnValue 来显示默认提示
      event.returnValue = ''
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [])
}

export function confirmDiscard(): boolean {
  return window.confirm('当前有未保存的更改，是否放弃并继续？')
}
