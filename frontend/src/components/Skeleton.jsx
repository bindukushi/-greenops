export function Skeleton({ className = '', style }) {
  return (
    <div
      className={`relative overflow-hidden bg-graphite-800 rounded-lg ${className}`}
      style={style}
    >
      <div
        className="absolute inset-0 animate-shimmer"
        style={{
          backgroundImage:
            'linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent)',
          backgroundSize: '400px 100%',
        }}
      />
    </div>
  )
}

export function StatCardSkeleton() {
  return (
    <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-5 flex flex-col gap-3">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="h-8 w-20" />
    </div>
  )
}

export function ChartSkeleton({ height = 260 }) {
  return (
    <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-6">
      <Skeleton className="h-3 w-40 mb-2" />
      <Skeleton className="h-3 w-56 mb-6" />
      <Skeleton className={`w-full`} style={{ height }} />
    </div>
  )
}
