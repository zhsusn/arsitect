/// <reference types="vitest/globals" />
import { renderHook } from '@testing-library/react'
import { useUnsavedGuard, confirmDiscard } from './useUnsavedGuard'

describe('useUnsavedGuard', () => {
  it('registers and removes the beforeunload listener', () => {
    const addEventListenerSpy = vi.spyOn(window, 'addEventListener')
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')

    const { unmount } = renderHook(() => useUnsavedGuard(true))
    expect(addEventListenerSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function))

    unmount()
    expect(removeEventListenerSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function))

    addEventListenerSpy.mockRestore()
    removeEventListenerSpy.mockRestore()
  })

  it('prevents page unload when there are unsaved changes', () => {
    renderHook(() => useUnsavedGuard(true))
    const event = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(event)
    expect(event.defaultPrevented).toBe(true)
  })

  it('does not prevent page unload when there are no unsaved changes', () => {
    renderHook(() => useUnsavedGuard(false))
    const event = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(event)
    expect(event.defaultPrevented).toBe(false)
  })
})

describe('confirmDiscard', () => {
  it('uses window.confirm with the discard message', () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    expect(confirmDiscard()).toBe(true)
    expect(confirmSpy).toHaveBeenCalledWith('当前有未保存的更改，是否放弃并继续？')
    confirmSpy.mockRestore()
  })
})
