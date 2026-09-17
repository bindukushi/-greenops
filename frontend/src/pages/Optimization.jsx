import { useEffect, useState, useCallback } from 'react'
import * as api from '../services/api'
import PageHeader from '../components/PageHeader'
import { ChartSkeleton } from '../components/Skeleton'
import { EmptyState, ErrorBanner } from '../components/States'

const PRIORITY_STYLES = {
  high: 'bg-alert-500/10 text-alert-500 border-alert-500/30',
  medium: 'bg-energy-500/10 text-energy-500 border-energy-500/30',
  low: 'bg-carbon-500/10 text-carbon-400 border-carbon-600/30',
  info: 'bg-graphite-700/40 text-graphite-400 border-graphite-700',
}

function RecommendationCard({ rec, index }) {
  return (
    <div
      className="bg-graphite-900 border border-graphite-800 rounded-xl p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-graphite-600 hover:shadow-lg hover:shadow-black/30 animate-fade-in-up"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <span className="text-xs font-mono text-graphite-500 uppercase tracking-wide">{rec.category}</span>
          <p className="text-sm text-white mt-1">{rec.problem}</p>
        </div>
        <span className={`text-xs font-mono px-2 py-1 rounded-full border shrink-0 ${PRIORITY_STYLES[rec.priority]}`}>
          {rec.priority}
        </span>
      </div>
      <p className="text-sm text-graphite-400 mb-4">→ {rec.suggestion}</p>
      <div className="flex flex-wrap gap-4 text-xs font-mono">
        <div>
          <span className="text-graphite-600">Energy ↓</span>{' '}
          <span className="text-energy-500">{rec.expected_energy_reduction_pct}%</span>
        </div>
        <div>
          <span className="text-graphite-600">Carbon ↓</span>{' '}
          <span className="text-carbon-400">{rec.expected_carbon_reduction_pct}%</span>
        </div>
        {rec.estimated_savings?.cost_saved_usd > 0 && (
          <div>
            <span className="text-graphite-600">Est. savings</span>{' '}
            <span className="text-white">${rec.estimated_savings.cost_saved_usd}</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default function Optimization() {
  const [servers, setServers] = useState([])
  const [selected, setSelected] = useState('')
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadServers = useCallback(async () => {
    setError('')
    try {
      const r = await api.getServers()
      setServers(r.data.servers)
      if (r.data.servers.length) setSelected(r.data.servers[0])
      else setLoading(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load servers.')
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadServers()
  }, [loadServers])

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    setError('')
    api.getRecommendations(selected)
      .then((r) => setRecommendations(r.data.recommendations || []))
      .catch((err) => setError(err.response?.data?.detail || 'Could not load recommendations.'))
      .finally(() => setLoading(false))
  }, [selected])

  return (
    <div className="px-8 py-8 max-w-4xl">
      <PageHeader
        eyebrow="GreenOps Engine"
        title="Optimization Report"
        description="Rule-based + statistical recommendations to reduce waste, energy, and cost."
        action={
          servers.length > 0 && (
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="focus-ring bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-2 text-sm text-white transition-colors"
            >
              {servers.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          )
        }
      />

      {error && (
        <div className="mb-6">
          <ErrorBanner message={error} onRetry={loadServers} />
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <ChartSkeleton key={i} height={90} />
          ))}
        </div>
      ) : servers.length === 0 ? (
        <EmptyState
          icon="⟴"
          title="No telemetry to analyze yet"
          description={'Visit the Dashboard and click "Simulate CloudWatch ingest" first.'}
        />
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec, i) => (
            <RecommendationCard key={i} rec={rec} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}
