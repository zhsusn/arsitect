import type { GateStats } from '@/stores/gateCenterStore'

interface StatCardsProps {
  stats: GateStats
  activeFilter?: string
  onFilter: (status: string) => void
}

export default function StatCards({ stats, activeFilter, onFilter }: StatCardsProps) {
  const cards = [
    {
      key: 'pending',
      label: '待审',
      count: stats.pending,
      color: 'border-blue-500 text-blue-700 bg-blue-50',
    },
    {
      key: 'passed',
      label: '已通过',
      count: stats.passed,
      color: 'border-green-500 text-green-700 bg-green-50',
    },
    {
      key: 'rejected',
      label: '已驳回',
      count: stats.rejected,
      color: 'border-red-500 text-red-700 bg-red-50',
    },
  ] as const

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      {cards.map((c) => {
        const isActive = activeFilter === c.key
        return (
          <button
            key={c.key}
            onClick={() => onFilter(isActive ? '' : c.key)}
            className={[
              'w-full text-left rounded-lg border-2 p-4 transition hover:shadow-md',
              c.color,
              isActive ? 'ring-2 ring-offset-2 ring-gray-400' : '',
            ].join(' ')}
          >
            <div className="text-sm font-medium opacity-80">{c.label}</div>
            <div className="text-3xl font-bold mt-1">{c.count}</div>
          </button>
        )
      })}
    </div>
  )
}
