interface BadgeManagerProps {
  tabKey: string
  hasUnread: boolean
}

export default function BadgeManager({ tabKey, hasUnread }: BadgeManagerProps) {
  if (tabKey === 'annotation' && hasUnread) {
    return (
      <span className="absolute -top-0.5 -right-1.5 h-2.5 w-2.5 rounded-full bg-red-500" />
    )
  }
  return null
}
