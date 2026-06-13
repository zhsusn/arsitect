import { useState, useEffect, useCallback } from 'react'

type Urgency = 'normal' | 'warning' | 'danger' | 'expired'

interface CountdownResult {
  text: string
  urgency: Urgency
  isExpired: boolean
}

function formatMs(ms: number): string {
  if (ms <= 0) return '00:00:00'
  const totalSeconds = Math.floor(ms / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

export function useBypassCountdown(deadlineAt: string | null | undefined): CountdownResult {
  const calculate = useCallback((): CountdownResult => {
    if (!deadlineAt) {
      return { text: '--:--:--', urgency: 'normal', isExpired: false }
    }
    const now = Date.now()
    const deadline = new Date(deadlineAt).getTime()
    const remaining = deadline - now

    if (remaining <= 0) {
      return { text: '已超时', urgency: 'expired', isExpired: true }
    }

    const hours = remaining / (1000 * 60 * 60)
    let urgency: Urgency = 'normal'
    if (hours <= 1) urgency = 'danger'
    else if (hours <= 4) urgency = 'warning'

    return {
      text: formatMs(remaining),
      urgency,
      isExpired: false,
    }
  }, [deadlineAt])

  const [result, setResult] = useState<CountdownResult>(calculate)

  useEffect(() => {
    setResult(calculate())
    const timer = setInterval(() => {
      setResult(calculate())
    }, 1000)
    return () => clearInterval(timer)
  }, [calculate])

  return result
}
