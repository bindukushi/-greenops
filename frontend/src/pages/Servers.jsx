import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import * as api from '../services/api'
import PageHeader from '../components/PageHeader'
import { ChartSkeleton } from '../components/Skeleton'
import { EmptyState, ErrorBanner } from '../components/States'

const PROVIDER_DOT = { AWS: '#F5A623', Azure: '#3DDC84', GCP: '#6EE7A8' }

function scoreColor(score) {
  if (score >= 75) return 'text-carbon-400'
  if (score >= 45) return 'text-energy-500'
  return 'text-alert-500'
}

export default function Servers() {
  const [servers, setServers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.getServersOverview()
      setServers(res.data.servers)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load servers.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="px-8 py-8 max-w-6xl">
      <PageHeader
        eyebrow="Fleet Inventory"
        title="Servers"
        description="Click any server for its full history, recommendations, and a live forecast."
      />

      {error && (
        <div className="mb-6">
          <ErrorBanner message={error} onRetry={load} />
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <ChartSkeleton key={i} height={56} />
          ))}
        </div>
      ) : servers.length === 0 ? (
        <EmptyState
          icon="▤"
          title="No servers yet"
          description={'Visit the Dashboard and click "Simulate CloudWatch ingest" first.'}
        />
      ) : (
        <div className="bg-graphite-900 border border-graphite-800 rounded-2xl overflow-hidden animate-fade-in-up">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs font-mono text-graphite-500 uppercase tracking-wide border-b border-graphite-800">
                <th className="px-5 py-3">Server</th>
                <th className="px-5 py-3">Provider / Region</th>
                <th className="px-5 py-3">Avg CPU</th>
                <th className="px-5 py-3">Avg Energy</th>
                <th className="px-5 py-3">Total Carbon</th>
                <th className="px-5 py-3">Green Score</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {servers.map((s, i) => (
                <tr
                  key={s.server_id}
                  onClick={() => navigate(`/servers/${s.server_id}`)}
                  className="border-b border-graphite-800 last:border-0 cursor-pointer transition-colors hover:bg-graphite-800/60 animate-fade-in-up"
                  style={{ animationDelay: `${i * 40}ms` }}
                >
                  <td className="px-5 py-3.5 font-display font-medium text-white">{s.server_id}</td>
                  <td className="px-5 py-3.5">
                    <span className="inline-flex items-center gap-1.5 text-graphite-400">
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ background: PROVIDER_DOT[s.provider] || '#5B6E63' }}
                      />
                      {s.provider} · {s.region}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-graphite-300 font-mono">{s.avg_cpu}%</td>
                  <td className="px-5 py-3.5 text-graphite-300 font-mono">{s.avg_energy_kwh} kWh</td>
                  <td className="px-5 py-3.5 text-graphite-300 font-mono">{s.total_carbon_kg} kg</td>
                  <td className={`px-5 py-3.5 font-mono font-semibold ${scoreColor(s.green_score)}`}>
                    {s.green_score}
                  </td>
                  <td className="px-5 py-3.5 text-graphite-600 text-right">→</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
