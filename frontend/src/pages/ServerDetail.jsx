import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import * as api from '../services/api'
import { downloadBlob } from '../services/download'
import GreenScoreGauge from '../components/GreenScoreGauge'
import { ChartSkeleton, StatCardSkeleton } from '../components/Skeleton'
import { EmptyState, ErrorBanner } from '../components/States'

const PROVIDER_DOT = { AWS: '#F5A623', Azure: '#3DDC84', GCP: '#6EE7A8' }

const PRIORITY_STYLES = {
  high: 'bg-alert-500/10 text-alert-500 border-alert-500/30',
  medium: 'bg-energy-500/10 text-energy-500 border-energy-500/30',
  low: 'bg-carbon-500/10 text-carbon-400 border-carbon-600/30',
  info: 'bg-graphite-700/40 text-graphite-400 border-graphite-700',
}

function MiniStat({ label, value, unit }) {
  return (
    <div className="bg-graphite-900 border border-graphite-800 rounded-xl p-4">
      <div className="text-xs font-mono text-graphite-500 uppercase tracking-wide mb-1">{label}</div>
      <div className="font-display text-xl font-semibold text-white">
        {value} {unit && <span className="text-sm text-graphite-500">{unit}</span>}
      </div>
    </div>
  )
}

export default function ServerDetail() {
  const { serverId } = useParams()
  const navigate = useNavigate()

  const [detail, setDetail] = useState(null)
  const [carbonTrend, setCarbonTrend] = useState([])
  const [energyTrend, setEnergyTrend] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notFound, setNotFound] = useState(false)
  const [exporting, setExporting] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    setNotFound(false)
    try {
      const [detailRes, carbonRes, energyRes, recsRes] = await Promise.all([
        api.getServerDetail(serverId),
        api.getCarbonTrend({ server_id: serverId, days: 30 }),
        api.getEnergyTrend({ server_id: serverId, days: 30 }),
        api.getRecommendations(serverId),
      ])
      setDetail(detailRes.data)
      setCarbonTrend(
        carbonRes.data.labels.map((l, i) => ({ date: l.slice(5), emission: carbonRes.data.values[i] }))
      )
      setEnergyTrend(
        energyRes.data.labels.map((l, i) => ({ date: l.slice(5), energy: energyRes.data.values[i] }))
      )
      setRecommendations(recsRes.data.recommendations || [])
    } catch (err) {
      if (err.response?.status === 404) {
        setNotFound(true)
      } else {
        setError(err.response?.data?.detail || 'Could not load server details.')
      }
    } finally {
      setLoading(false)
    }
  }, [serverId])

  useEffect(() => {
    load()
  }, [load])

  const handleExport = async () => {
    setExporting(true)
    try {
      const res = await api.exportMetricsCsv(serverId)
      downloadBlob(res.data, `greenai_${serverId}_metrics.csv`, 'text/csv')
    } catch {
      setError('Could not export CSV right now.')
    } finally {
      setExporting(false)
    }
  }

  if (notFound) {
    return (
      <div className="px-8 py-8 max-w-4xl">
        <EmptyState
          icon="▤"
          title={`No telemetry found for "${serverId}"`}
          description="This server hasn't reported any data yet."
          action={
            <button
              onClick={() => navigate('/servers')}
              className="focus-ring text-sm bg-graphite-800 hover:bg-graphite-700 border border-graphite-700 text-carbon-400 font-medium px-4 py-2 rounded-lg transition-colors"
            >
              ← Back to Servers
            </button>
          }
        />
      </div>
    )
  }

  return (
    <div className="px-8 py-8 max-w-6xl">
      <Link
        to="/servers"
        className="focus-ring text-xs font-mono text-graphite-500 hover:text-carbon-400 transition-colors inline-block mb-4"
      >
        ← Back to Servers
      </Link>

      <div className="flex items-start justify-between gap-6 mb-8">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="font-display text-2xl font-semibold text-white">{serverId}</h1>
            {detail && (
              <span className="inline-flex items-center gap-1.5 text-xs font-mono bg-graphite-800 border border-graphite-700 text-graphite-400 px-2.5 py-1 rounded-full">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ background: PROVIDER_DOT[detail.provider] || '#5B6E63' }}
                />
                {detail.provider} · {detail.region}
              </span>
            )}
          </div>
          <p className="text-sm text-graphite-500">
            {detail ? `${detail.record_count} readings recorded` : 'Loading server telemetry...'}
          </p>
        </div>
        <button
          onClick={handleExport}
          disabled={exporting || !detail}
          className="focus-ring text-sm bg-graphite-800 hover:bg-graphite-700 active:scale-95 border border-graphite-700 text-graphite-300 font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-50"
        >
          {exporting ? 'Exporting...' : '⬇ Export CSV'}
        </button>
      </div>

      {error && (
        <div className="mb-6">
          <ErrorBanner message={error} onRetry={load} />
        </div>
      )}

      {loading ? (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <ChartSkeleton /><ChartSkeleton />
          </div>
        </>
      ) : detail && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 animate-fade-in-up">
            <MiniStat label="Avg CPU" value={detail.averages.cpu_usage} unit="%" />
            <MiniStat label="Avg Memory" value={detail.averages.memory_usage} unit="%" />
            <MiniStat label="Avg Energy" value={detail.averages.energy_consumption} unit="kWh" />
            <MiniStat label="Total Carbon" value={detail.total_carbon_kg} unit="kg CO₂" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">
            <div className="lg:col-span-2 bg-graphite-900 border border-graphite-800 rounded-2xl p-6 animate-fade-in-up">
              <h3 className="font-display text-sm font-semibold text-white mb-1">Carbon Emission History</h3>
              <p className="text-xs text-graphite-500 mb-4 font-mono">Last 30 days (kg CO₂)</p>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={carbonTrend}>
                  <CartesianGrid stroke="#26332D" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: '#1C2622', border: '1px solid #354339', borderRadius: 8 }} labelStyle={{ color: '#E7ECE9' }} />
                  <Line type="monotone" dataKey="emission" stroke="#3DDC84" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} animationDuration={800} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-6 flex flex-col items-center justify-center animate-fade-in-up" style={{ animationDelay: '80ms' }}>
              <h3 className="font-display text-sm font-semibold text-white mb-4 self-start">Green Score</h3>
              <GreenScoreGauge score={detail.green_score} />
            </div>
          </div>

          <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-6 mb-8 animate-fade-in-up" style={{ animationDelay: '120ms' }}>
            <h3 className="font-display text-sm font-semibold text-white mb-1">Energy Consumption History</h3>
            <p className="text-xs text-graphite-500 mb-4 font-mono">Last 30 days (kWh)</p>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={energyTrend}>
                <CartesianGrid stroke="#26332D" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: '#1C2622', border: '1px solid #354339', borderRadius: 8 }} labelStyle={{ color: '#E7ECE9' }} />
                <Line type="monotone" dataKey="energy" stroke="#F5A623" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} animationDuration={800} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <h3 className="font-display text-sm font-semibold text-white mb-4">Recommendations for {serverId}</h3>
          <div className="space-y-3">
            {recommendations.map((rec, i) => (
              <div
                key={i}
                className="bg-graphite-900 border border-graphite-800 rounded-xl p-4 animate-fade-in-up"
                style={{ animationDelay: `${160 + i * 60}ms` }}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <span className="text-xs font-mono text-graphite-500 uppercase tracking-wide">{rec.category}</span>
                  <span className={`text-xs font-mono px-2 py-0.5 rounded-full border shrink-0 ${PRIORITY_STYLES[rec.priority]}`}>
                    {rec.priority}
                  </span>
                </div>
                <p className="text-sm text-white mb-1">{rec.problem}</p>
                <p className="text-sm text-graphite-400">→ {rec.suggestion}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
