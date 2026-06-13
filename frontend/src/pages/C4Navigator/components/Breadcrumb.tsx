import React from 'react'
import { useNavigate } from 'react-router'
import type { BreadcrumbItem } from '../../../stores/c4NavigatorStore'

interface BreadcrumbProps {
  items: BreadcrumbItem[]
}

const Breadcrumb: React.FC<BreadcrumbProps> = ({ items }) => {
  const navigate = useNavigate()

  if (items.length === 0) return null

  return (
    <nav className="flex items-center text-sm text-gray-600 mb-3" aria-label="Breadcrumb">
      <ol className="flex items-center flex-wrap gap-1">
        {items.map((item, index) => {
          const isLast = index === items.length - 1
          return (
            <li key={index} className="flex items-center">
              {index > 0 && (
                <span className="mx-2 text-gray-300">&gt;</span>
              )}
              {item.href && !isLast ? (
                <button
                  onClick={() => navigate(item.href!)}
                  className="hover:text-blue-600 transition-colors"
                >
                  {item.label}
                </button>
              ) : (
                <span className={isLast ? 'font-medium text-gray-900' : ''}>
                  {item.label}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

export default React.memo(Breadcrumb)
