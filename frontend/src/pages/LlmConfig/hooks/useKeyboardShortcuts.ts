import { useEffect } from 'react'

interface UseKeyboardShortcutsOptions {
  formId: string
  hasChanges: boolean
  onCancel: () => void
}

export function useKeyboardShortcuts({ formId, hasChanges, onCancel }: UseKeyboardShortcutsOptions) {
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
        event.preventDefault()
        const form = document.getElementById(formId) as HTMLFormElement | null
        form?.requestSubmit()
        return
      }

      if (event.key === 'Escape') {
        if (hasChanges) {
          if (window.confirm('当前有未保存的更改，是否放弃并取消？')) {
            onCancel()
          }
        } else {
          onCancel()
        }
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [formId, hasChanges, onCancel])
}
