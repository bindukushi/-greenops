import { useCountUp } from '../hooks/useCountUp'

export default function StatCard({ label, value, unit, accent = 'carbon', trend }) {
  const accentColor =
    accent === 'energy' ? 'text-energy-500' : accent === 'alert' ? 'text-alert-500' : 'text-carbon-400'

  const numericValue = typeof value === 'number' ? value : parseFloat(value)
  const displayValue = useCountUp(Number.isFinite(numericValue) ? numericValue : value)

  return (
    <div className="group bg-graphite-900 border border-graphite-800 rounded-2xl p-5 flex flex-col gap-2 transition-all duration-300 hover:border-graphite-600 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/30 animate-fade-in-up">
      <span className="text-xs font-mono text-graphite-500 uppercase tracking-wide">{label}</span>
      <div className="flex items-baseline gap-1.5">
        <span className={`font-display text-3xl font-semibold tabular-nums ${accentColor}`}>
          {displayValue}
        </span>
        {unit && <span className="text-sm text-graphite-500">{unit}</span>}
      </div>
      {trend !== undefined && (
        <span className={`text-xs font-mono ${trend >= 0 ? 'text-alert-500' : 'text-carbon-400'}`}>
          {trend >= 0 ? '▲' : '▼'} {Math.abs(trend)}% vs. prior period
        </span>
      )}
    </div>
  )
}
