interface LeanIndicatorProps {
  lean: number | null
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

export function LeanIndicator({ lean, size = 'md', showLabel = true }: LeanIndicatorProps) {
  if (lean === null) {
    return <span className="text-gray-400 text-sm">N/A</span>
  }

  const sizeClasses = {
    sm: 'w-24 h-2',
    md: 'w-32 h-3',
    lg: 'w-48 h-4',
  }

  const position = Math.min(Math.max(lean, 0), 1) * 100

  return (
    <div className="flex items-center gap-2">
      <div className={`${sizeClasses[size]} relative rounded-full overflow-hidden`}>
        <div className="absolute inset-0 lean-gradient opacity-30" />
        <div
          className="absolute top-0 bottom-0 w-1 bg-gray-800 rounded-full"
          style={{ left: `calc(${position}% - 2px)` }}
        />
      </div>
      {showLabel && (
        <span className="text-sm font-medium text-gray-700">
          {(lean * 100).toFixed(1)}% R
        </span>
      )}
    </div>
  )
}

export function LeanBadge({ lean }: { lean: number | null }) {
  if (lean === null) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
        Unknown
      </span>
    )
  }

  if (lean < 0.45) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-democratic-100 text-democratic-700">
        Leans D ({(lean * 100).toFixed(1)}%)
      </span>
    )
  }

  if (lean > 0.55) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-republican-100 text-republican-700">
        Leans R ({(lean * 100).toFixed(1)}%)
      </span>
    )
  }

  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
      Balanced ({(lean * 100).toFixed(1)}%)
    </span>
  )
}
