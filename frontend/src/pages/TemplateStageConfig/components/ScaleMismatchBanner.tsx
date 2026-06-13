import { useNavigate } from 'react-router'

interface ScaleMismatchBannerProps {
  projectId?: string
  dismissible?: boolean
  onDismiss?: () => void
}

export default function ScaleMismatchBanner({
  projectId,
  dismissible = true,
  onDismiss,
}: ScaleMismatchBannerProps) {
  const navigate = useNavigate()

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 flex items-center justify-between mb-4">
      <div className="flex items-center gap-2 text-sm text-yellow-800">
        <span className="text-base">⚠️</span>
        <span>当前项目规模与模板不匹配，建议重新评估</span>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={() => {
            if (projectId) {
              navigate(`/complexity-router?projectId=${projectId}`)
            } else {
              navigate('/complexity-router')
            }
          }}
          className="text-sm px-3 py-1.5 bg-yellow-100 hover:bg-yellow-200 text-yellow-900 rounded-md font-medium transition-colors"
        >
          重新评估
        </button>
        {dismissible && onDismiss && (
          <button
            onClick={onDismiss}
            className="text-sm px-2 py-1.5 text-yellow-700 hover:text-yellow-900 transition-colors"
          >
            忽略
          </button>
        )}
      </div>
    </div>
  )
}
