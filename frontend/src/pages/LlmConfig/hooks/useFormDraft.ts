import { useCallback, useEffect } from 'react'

interface UseFormDraftOptions<T> {
  /** localStorage key */
  key: string
  /** current form state used for comparison */
  form: T
  /** whether the form has unsaved changes */
  isDirty: boolean
  /** called when the user chooses to restore a draft */
  onRestore: (draft: T) => void
}

export function useFormDraft<T>({ key, form, isDirty, onRestore }: UseFormDraftOptions<T>) {
  const clearDraft = useCallback(() => {
    try {
      localStorage.removeItem(key)
    } catch {
      // ignore storage errors
    }
  }, [key])

  // Restore draft on mount if it differs from the current initial state.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(key)
      if (!raw) return
      const draft = JSON.parse(raw) as T
      if (JSON.stringify(draft) !== JSON.stringify(form)) {
        if (window.confirm('检测到未提交的草稿，是否恢复？')) {
          onRestore(draft)
        } else {
          localStorage.removeItem(key)
        }
      } else {
        localStorage.removeItem(key)
      }
    } catch {
      localStorage.removeItem(key)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  // Auto-save draft 5 seconds after the last change.
  useEffect(() => {
    if (!isDirty) return
    const timer = setTimeout(() => {
      try {
        localStorage.setItem(key, JSON.stringify(form))
      } catch {
        // ignore storage errors
      }
    }, 5000)
    return () => clearTimeout(timer)
  }, [form, isDirty, key])

  return { clearDraft }
}
