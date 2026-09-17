import { useEffect, useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  BarChart, Bar, Cell,
} from 'recharts'
import * as api from '../services/api'
import { downloadBlob } from '../services/download'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import GreenScoreGauge from '../components/GreenScoreGauge'
import { StatCardSkeleton, ChartSkeleton } from '../components/Skeleton'
import { EmptyState, ErrorBanner } from '../components/States'

const SERVER_COLORS = ['#3DDC84', '#6EE7A8', '#F5A623', '#FFC670', '#5B6E63', '#8FE3C0']
const POLL_MS = 4000

export default function Dashboard() {
  const navigate = useNavigate()
  const [summary, setSummary] = useState(null)
  const [trend, setTrend] = useState([])
  const [energyTrend, setEnergyTrend] = useState([])
  const [resourceUsage, setResourceUsage] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [simulating, setSimulating] = useState(false)
  const [exporting, setExporting] = useState(false)

  // Live mode
  const [liveRunning, setLiveRunning] = useState(false)
  const [liveToggling, setLiveToggling] = useState(false)
  const [tickCount, setTickCount] = useState(0)
  const pollRef = useRef(null)

  // Real AWS integration
  const [awsConfigured, setAwsConfigured] = useState(false)
  const [awsInstanceIds, setAwsInstanceIds] = useState('')
  const [awsSyncing, setAwsSyncing] = useState(false)
  const [awsMessage, setAwsMessage] = useState('')

  const fetchAll = useCallback(async () => {
    const [summaryRes, trendRes, energyRes, usageRes] = await Promise.all([
      api.getSummary(),
      api.getCarbonTrend({ days: 30 }),
      api.getEnergyTrend({ days: 30 }),
      api.getResourceUsage(),
    ])
    setSummary(summaryRes.data)
    setTrend(trendRes.data.labels.map((l, i) => ({ date: l.slice(5), emission: trendRes.data.values[i] })))
    setEnergyTrend(energyRes.data.labels.map((l, i) => ({ date: l.slice(5), energy: energyRes.data.values[i] })))
    setResourceUsage(usageRes.data.servers)
  }, [])

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      await fetchAll()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load dashboard data.')
    } finally {
      setLoading(false)
    }
  }, [fetchAll])

  // Silent refresh used while polling live mode — no skeleton flicker
  const refreshSilently = useCallback(async () => {
    try {
      await fetchAll()
    } catch {
      // stay quiet on transient poll errors; the next tick will retry
    }
  }, [fetchAll])

  useEffect(() => {
    loadData()
    api.getLiveStatus().then((r) => {
      setLiveRunning(r.data.running)
      setTickCount(r.data.tick_count)
    }).catch(() => {})
    api.getAwsStatus().then((r) => setAwsConfigured(r.data.configured)).catch(() => {})
  }, [loadData])

  // Poll while live mode is on
  useEffect(() => {
    if (liveRunning) {
      pollRef.current = setInterval(async () => {
        await refreshSilently()
        try {
          const r = await api.getLiveStatus()
          setTickCount(r.data.tick_count)
        } catch { /* ignore */ }
      }, POLL_MS)
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [liveRunning, refreshSilently])

  const handleSimulate = async () => {
    setSimulating(true)
    setError('')
    try {
      await api.simulateCloudWatch(60)
      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not simulate CloudWatch data.')
    } finally {
      setSimulating(false)
    }
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      const res = await api.exportMetricsCsv()
      downloadBlob(res.data, 'greenai_metrics.csv', 'text/csv')
    } catch {
      setError('Could not export CSV. Try again in a moment.')
    } finally {
      setExporting(false)
    }
  }

  const handleToggleLive = async () => {
    setLiveToggling(true)
    setError('')
    try {
      if (liveRunning) {
        await api.stopLiveMode()
        setLiveRunning(false)
      } else {
        await api.startLiveMode(4)
        setLiveRunning(true)
        await loadData()
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not toggle live mode.')
    } finally {
      setLiveToggling(false)
    }
  }

  const handleAwsSync = async () => {
    if (!awsInstanceIds.trim()) return
    setAwsSyncing(true)
    setAwsMessage('')
    try {
      const res = await api.syncRealAws(awsInstanceIds.trim())
      setAwsMessage(res.data.message)
      await loadData()
    } catch (err) {
      setAwsMessage(err.response?.data?.detail || 'Could not sync real AWS data.')
    } finally {
      setAwsSyncing(false)
    }
  }

  const noData = summary && summary.server_count === 0

  return (
    <div className="px-8 py-8 max-w-7xl">
      <PageHeader
        eyebrow="Cloud Monitoring"
        title={
          <span className="inline-flex items-center gap-2.5">
            GreenOps Dashboard
            {liveRunning && (
              <span className="inline-flex items-center gap-1.5 text-xs font-mono bg-alert-500/10 text-alert-500 border border-alert-500/30 px-2 py-0.5 rounded-full align-middle">
                <span className="w-1.5 h-1.5 rounded-full bg-alert-500 animate-pulse-dot" />
                LIVE · {tickCount} ticks
              </span>
            )}
          </span>
        }
        description="Real-time snapshot of your cloud fleet's energy use and carbon footprint."
        action={
          <div className="flex gap-2">
            <button
              onClick={handleToggleLive}
              disabled={liveToggling}
              className={`focus-ring text-sm active:scale-95 border font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-60 ${
                liveRunning
                  ? 'bg-alert-500/10 border-alert-500/30 text-alert-500 hover:bg-alert-500/20'
                  : 'bg-graphite-800 hover:bg-graphite-700 border-graphite-700 text-graphite-300'
              }`}
            >
              {liveToggling ? '...' : liveRunning ? '■ Stop Live Mode' : '● Start Live Mode'}
            </button>
            <button
              onClick={handleExport}
              disabled={exporting || noData}
              className="focus-ring text-sm bg-graphite-800 hover:bg-graphite-700 active:scale-95 border border-graphite-700 text-graphite-300 font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-50"
            >
              {exporting ? 'Exporting...' : '⬇ Export CSV'}
            </button>
            <button
              onClick={handleSimulate}
              disabled={simulating}
              className="focus-ring text-sm bg-graphite-800 hover:bg-graphite-700 active:scale-95 border border-graphite-700 text-carbon-400 font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-60"
            >
              {simulating ? 'Pulling CloudWatch data...' : '⟳ Simulate CloudWatch ingest'}
            </button>
          </div>
        }
      />

      {error && (
        <div className="mb-6">
          <ErrorBanner message={error} onRetry={loadData} />
        </div>
      )}

      {noData && !loading && !error && (
        <div className="mb-8 bg-energy-500/10 border border-energy-500/30 rounded-xl px-5 py-4 text-sm text-energy-400 animate-fade-in">
          No monitoring data yet. Click <strong>Simulate CloudWatch ingest</strong> for an instant
          historical backfill, or <strong>Start Live Mode</strong> to stream new readings in real time.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-8">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)
        ) : (
          <>
            <StatCard label="Total Emission" value={summary?.total_emission_kg ?? 0} unit="kg CO₂" accent="carbon" />
            <StatCard label="Energy Used" value={summary?.total_energy_kwh ?? 0} unit="kWh" accent="energy" />
            <StatCard label="Monitored Servers" value={summary?.server_count ?? 0} accent="carbon" />
            <StatCard
              label="Emission Trend"
              value={summary?.trend_pct ?? 0}
              unit="%"
              accent={summary?.trend_pct > 0 ? 'alert' : 'carbon'}
            />
          </>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">
        {loading ? (
          <>
            <div className="lg:col-span-2"><ChartSkeleton /></div>
            <ChartSkeleton height={200} />
          </>
        ) : noData ? (
          <div className="lg:col-span-3">
            <EmptyState
              icon="⌁"
              title="No telemetry yet"
              description="Simulate CloudWatch ingest, or start Live Mode, to see the carbon trend and sustainability scoring."
            />
          </div>
        ) : (
          <>
            <div className="lg:col-span-2 bg-graphite-900 border border-graphite-800 rounded-2xl p-6 animate-fade-in-up">
              <h3 className="font-display text-sm font-semibold text-white mb-1">Carbon Emission Trend</h3>
              <p className="text-xs text-graphite-500 mb-4 font-mono">Last 30 days, aggregated daily (kg CO₂)</p>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={trend}>
                  <CartesianGrid stroke="#26332D" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#1C2622', border: '1px solid #354339', borderRadius: 8 }}
                    labelStyle={{ color: '#E7ECE9' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="emission"
                    stroke="#3DDC84"
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{ r: 4 }}
                    isAnimationActive={!liveRunning}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-6 flex flex-col animate-fade-in-up" style={{ animationDelay: '80ms' }}>
              <h3 className="font-display text-sm font-semibold text-white mb-1">Sustainability Score</h3>
              <p className="text-xs text-graphite-500 mb-6 font-mono">Composite utilization + carbon efficiency</p>
              <div className="flex-1 flex items-center justify-center">
                <GreenScoreGauge score={summary?.avg_green_score ?? 0} />
              </div>
              <p className="text-xs text-graphite-500 text-center mt-4">
                {(summary?.avg_green_score ?? 0) >= 75
                  ? 'Fleet is well-optimized.'
                  : (summary?.avg_green_score ?? 0) >= 45
                  ? 'Moderate efficiency — review the Optimization page.'
                  : 'Significant waste detected — action recommended.'}
              </p>
            </div>
          </>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        {loading ? (
          <>
            <ChartSkeleton />
            <ChartSkeleton />
          </>
        ) : noData ? null : (
          <>
            <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-6 animate-fade-in-up" style={{ animationDelay: '120ms' }}>
              <h3 className="font-display text-sm font-semibold text-white mb-1">Energy Consumption Trend</h3>
              <p className="text-xs text-graphite-500 mb-4 font-mono">Last 30 days, aggregated daily (kWh)</p>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={energyTrend}>
                  <CartesianGrid stroke="#26332D" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#1C2622', border: '1px solid #354339', borderRadius: 8 }}
                    labelStyle={{ color: '#E7ECE9' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="energy"
                    stroke="#F5A623"
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{ r: 4 }}
                    isAnimationActive={!liveRunning}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-6 animate-fade-in-up" style={{ animationDelay: '160ms' }}>
              <h3 className="font-display text-sm font-semibold text-white mb-1">Resource Usage by Server</h3>
              <p className="text-xs text-graphite-500 mb-4 font-mono">
                Average CPU utilization (%) across monitored fleet · click a bar for details
              </p>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={resourceUsage}>
                  <CartesianGrid stroke="#26332D" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="server_id" stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#1C2622', border: '1px solid #354339', borderRadius: 8 }}
                    labelStyle={{ color: '#E7ECE9' }}
                  />
                  <Bar
                    dataKey="avg_cpu"
                    radius={[6, 6, 0, 0]}
                    isAnimationActive={!liveRunning}
                    cursor="pointer"
                    onClick={(data) => navigate(`/servers/${data.server_id}`)}
                  >
                    {resourceUsage.map((_, i) => (
                      <Cell key={i} fill={SERVER_COLORS[i % SERVER_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </div>

      {/* Optional real AWS CloudWatch sync panel */}
      <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-6 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-display text-sm font-semibold text-white">Real AWS CloudWatch Sync</h3>
          <span
            className={`text-xs font-mono px-2 py-0.5 rounded-full border ${
              awsConfigured
                ? 'bg-carbon-500/10 text-carbon-400 border-carbon-600/30'
                : 'bg-graphite-800 text-graphite-500 border-graphite-700'
            }`}
          >
            {awsConfigured ? 'Configured' : 'Not configured'}
          </span>
        </div>
        {awsConfigured ? (
          <>
            <p className="text-xs text-graphite-500 mb-3 font-mono">
              Pull real CPUUtilization data for your own EC2 instances (comma-separated IDs)
            </p>
            <div className="flex gap-2">
              <input
                value={awsInstanceIds}
                onChange={(e) => setAwsInstanceIds(e.target.value)}
                placeholder="i-0123456789abcdef0, i-0abc..."
                className="focus-ring flex-1 bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-2 text-sm text-white placeholder-graphite-600"
              />
              <button
                onClick={handleAwsSync}
                disabled={awsSyncing || !awsInstanceIds.trim()}
                className="focus-ring text-sm bg-carbon-500 hover:bg-carbon-400 active:scale-95 text-graphite-950 font-semibold px-4 py-2 rounded-lg transition-all disabled:opacity-50"
              >
                {awsSyncing ? 'Syncing...' : 'Sync real data'}
              </button>
            </div>
          </>
        ) : (
          <p className="text-xs text-graphite-500 font-mono">
            Every other data source here is simulated. To pull genuinely real telemetry from your
            own AWS account: <code className="text-carbon-400">pip install boto3</code> and set{' '}
            <code className="text-carbon-400">AWS_ACCESS_KEY_ID</code> /{' '}
            <code className="text-carbon-400">AWS_SECRET_ACCESS_KEY</code> in your environment,
            then restart the backend.
          </p>
        )}
        {awsMessage && <p className="text-xs text-graphite-400 mt-3">{awsMessage}</p>}
      </div>
    </div>
  )
}
