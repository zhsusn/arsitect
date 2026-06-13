import { useState } from 'react'

interface RetryButtonProps {
  executionId: string
  retryCount: number
  maxRetries: number
  status: string
  onRetry: () => void
}

export default function RetryButton({
  executionId,
  retryCount,
  maxRetries,
  status,
  onRetry,
}: RetryButtonProps) {
  // 保留 prop 以满足接口契约，当前渲染层暂不消费
  void executionId
  const [isRetrying, setIsRetrying] = useState(false)

  const canRetry = status === 'FAILED' && retryCount < maxRetries
  const isMaxed = retryCount >= maxRetries

  const handleClick = async () => {
    if (!canRetry || isRetrying) return
    setIsRetrying(true)
    try {
      await onRetry()
    } finally {
      setIsRetrying(false)
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={!canRetry || isRetrying}
      title={isMaxed ? '已达重试上限，请联系支持' : '重新执行'}
      style={{
        padding: '4px 10px',
        fontSize: 12,
        cursor: canRetry && !isRetrying ? 'pointer' : 'not-allowed',
        opacity: canRetry && !isRetrying ? 1 : 0.6,
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
      }}
    >
      {isRetrying ? (
        <span
          style={{
            display: 'inline-block',
            width: 12,
            height: 12,
            border: '2px solid #e5e7eb',
            borderTopColor: '#374151',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
      ) : (
        <span>重试</span>
      )}
      <span>
        ({retryCount}/{maxRetries})
      </span>
    </button>
  )
}
