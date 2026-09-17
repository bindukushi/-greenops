import { useEffect, useState, useCallback } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'
import * as api from '../services/api'
import PageHeader from '../components/PageHeader'
import { ChartSkeleton, StatCardSkeleton } from '../components/Skeleton'
import { EmptyState, ErrorBanner } from '../components/States'

const ALERT_STYLES = {
  anomaly: { badge: 'bg-alert-500/10 text-alert-500 border-alert-500/30', icon: '⚠' },
  budget: { badge: 'bg-energy-500/10 text-energy-500 border-energy-500/30', icon: '💰' },
}

function DigestCard({ digest }) {
  if (!digest) return null
  return (
    <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-6 animate-fade-in-up">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-display text-sm font-semibold text-white">Latest Daily Digest</h3>
        <span className="text-xs font-mono text-graphite-500">{digest.date}</span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <div className="text-xs font-mono text-graphite-500 mb-1">Total Emission</div>
          <div className="font-display text-lg text-white">{digest.total_emission_kg} kg</div>
        </div>
        <div>
          <div className="text-xs font-mono text-graphite-500 mb-1">Budget</div>
          <div className={`font-display text-lg ${digest.budget_breached ? 'text-alert-500' : 'text-carbon-400'}`}>
            {digest.budget_breached ? 'Breached' : 'Within limit'}
          </div>
        </div>
        <div>
          <div className="text-xs font-mono text-graphite-500 mb-1">Top Offender</div>
          <div className="font-display text-lg text-white">{digest.top_offender_server}</div>
        </div>
        <div>
          <div className="text-xs font-mono text-graphite-500 mb-1">Anomalies</div>
          <div className={`font-display text-lg ${digest.anomalies_detected > 0 ? 'text-alert-500' : 'text-carbon-400'}`}>
            {digest.anomalies_detected}
          </div>
        </div>
      </div>
      {digest.avg_forecast_error_pct !== null && digest.avg_forecast_error_pct !== undefined && (
        <p className="text-xs text-graphite-500 mt-4 font-mono border-t border-graphite-800 pt-3">
          Forecast accuracy: avg error {digest.avg_forecast_error_pct}% across {digest.accuracy_records} scored predictions
        </p>
      )}
    </div>
  )
}

export default function Monitoring() {
  const [servers, setServers] = useState([])
  const [selectedServer, setSelectedServer] = useState('')
  const [digest, setDigest] = useState(null)
  const [reports, setReports] = useState([])
  const [alerts, setAlerts] = useState([])
  const [accuracy, setAccuracy] = useState([])
  const [budget, setBudget] = useState(null)
  const [budgetInput, setBudgetInput] = useState('')
  const [schedulerStatus, setSchedulerStatus] = useState(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [running, setRunning] = useState(false)
  const [savingBudget, setSavingBudget] = useState(false)
  const [injecting, setInjecting] = useState(false)

  const loadAll = useCallback(async (serverForAccuracy) => {
    setError('')
    try {
      const [serversRes, reportsRes, alertsRes, budgetRes, schedRes] = await Promise.all([
        api.getServers(),
        api.getDailyReports(10),
        api.getAlerts({ limit: 20 }),
        api.getMonitoringBudget(),
        api.getMonitoringSchedulerStatus(),
      ])
      setServers(serversRes.data.servers)
      const svr = serverForAccuracy || selectedServer || serversRes.data.servers[0] || ''
      setSelectedServer(svr)
      setReports(reportsRes.data.reports)
      setDigest(reportsRes.data.reports[0] || null)
      setAlerts(alertsRes.data.alerts)
      setBudget(budgetRes.data.daily_limit_kg)
      setBudgetInput(String(budgetRes.data.daily_limit_kg))
      setSchedulerStatus(schedRes.data)

      if (svr) {
        const accRes = await api.getForecastAccuracy({ server_id: svr, limit: 20 })
        setAccuracy(
          accRes.data.accuracy.map((a, i) => ({
            index: i + 1,
            predicted: a.predicted_emission_kg,
            actual: a.actual_emission_kg,
          }))
        )
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load monitoring data.')
    } finally {
      setLoading(false)
    }
  }, [selectedServer])

  useEffect(() => {
    loadAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (selectedServer) {
      api.getForecastAccuracy({ server_id: selectedServer, limit: 20 }).then((res) => {
        setAccuracy(
          res.data.accuracy.map((a, i) => ({
            index: i + 1,
            predicted: a.predicted_emission_kg,
            actual: a.actual_emission_kg,
          }))
        )
      }).catch(() => {})
    }
  }, [selectedServer])

  const handleRunJob = async () => {
    setRunning(true)
    setError('')
    try {
      await api.runDailyJob()
      await loadAll()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not run the daily job.')
    } finally {
      setRunning(false)
    }
  }

  const handleSaveBudget = async () => {
    const value = parseFloat(budgetInput)
    if (!value || value <= 0) return
    setSavingBudget(true)
    try {
      await api.setMonitoringBudget(value)
      setBudget(value)
    } catch {
      setError('Could not update the carbon budget.')
    } finally {
      setSavingBudget(false)
    }
  }

  const handleInjectAnomaly = async () => {
    if (!selectedServer) return
    setInjecting(true)
    try {
      await api.injectTestAnomaly(selectedServer)
      await api.runDailyJob()
      await loadAll(selectedServer)
    } catch {
      setError('Could not inject the test anomaly.')
    } finally {
      setInjecting(false)
    }
  }

  const noData = !loading && servers.length === 0

  return (
    <div className="px-8 py-8 max-w-6xl">
      <PageHeader
        eyebrow="MLOps · Real-Time Monitoring"
        title="Daily Monitoring"
        description="Scheduled forecasting, forecast-accuracy tracking, anomaly detection, and carbon budget alerts."
        action={
          <button
            onClick={handleRunJob}
            disabled={running || noData}
            className="focus-ring text-sm bg-carbon-500 hover:bg-carbon-400 active:scale-95 text-graphite-950 font-semibold px-4 py-2 rounded-lg transition-all disabled:opacity-50"
          >
            {running ? 'Running cycle...' : '▶ Run Daily Job Now'}
          </button>
        }
      />

      {error && (
        <div className="mb-6">
          <ErrorBanner message={error} onRetry={() => loadAll()} />
        </div>
      )}

      {schedulerStatus && (
        <p className="text-xs font-mono text-graphite-600 mb-6 -mt-4">
          Background scheduler: {schedulerStatus.running ? 'active' : 'inactive'} · {schedulerStatus.interval}
        </p>
      )}

      {loading ? (
        <div className="space-y-5">
          <ChartSkeleton height={140} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <ChartSkeleton /><ChartSkeleton />
          </div>
        </div>
      ) : noData ? (
        <EmptyState
          icon="◈"
          title="No telemetry to monitor yet"
          description={'Visit the Dashboard and click "Simulate CloudWatch ingest" first, then come back and run the daily job.'}
        />
      ) : (
        <>
          <div className="mb-5">
            <DigestCard digest={digest} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
            {/* Carbon budget */}
            <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-6 animate-fade-in-up" style={{ animationDelay: '60ms' }}>
              <h3 className="font-display text-sm font-semibold text-white mb-1">Carbon Budget</h3>
              <p className="text-xs text-graphite-500 mb-4 font-mono">
                Daily fleet-wide limit — breaching it raises an alert on the next run
              </p>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={budgetInput}
                  onChange={(e) => setBudgetInput(e.target.value)}
                  className="focus-ring flex-1 bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-2 text-sm text-white"
                />
                <span className="flex items-center text-xs text-graphite-500 font-mono">kg CO₂</span>
                <button
                  onClick={handleSaveBudget}
                  disabled={savingBudget}
                  className="focus-ring text-sm bg-graphite-800 hover:bg-graphite-700 active:scale-95 border border-graphite-700 text-carbon-400 font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-50"
                >
                  {savingBudget ? 'Saving...' : 'Save'}
                </button>
              </div>
              <p className="text-xs text-graphite-600 mt-2 font-mono">Current: {budget} kg CO₂ / day</p>
            </div>

            {/* Anomaly injection utility */}
            <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-6 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
              <h3 className="font-display text-sm font-semibold text-white mb-1">Test the Alerting Pipeline</h3>
              <p className="text-xs text-graphite-500 mb-4 font-mono">
                Injects a deliberate spike reading, then runs the daily job to catch it
              </p>
              <div className="flex gap-2">
                <select
                  value={selectedServer}
                  onChange={(e) => setSelectedServer(e.target.value)}
                  className="focus-ring flex-1 bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-2 text-sm text-white"
                >
                  {servers.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
                <button
                  onClick={handleInjectAnomaly}
                  disabled={injecting}
                  className="focus-ring text-sm bg-alert-500/10 hover:bg-alert-500/20 active:scale-95 border border-alert-500/30 text-alert-500 font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-50 whitespace-nowrap"
                >
                  {injecting ? 'Injecting...' : 'Inject spike'}
                </button>
              </div>
            </div>
          </div>

          {/* Forecast accuracy chart */}
          <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-6 mb-5 animate-fade-in-up" style={{ animationDelay: '140ms' }}>
            <h3 className="font-display text-sm font-semibold text-white mb-1">
              Forecast Accuracy — {selectedServer || '—'}
            </h3>
            <p className="text-xs text-graphite-500 mb-4 font-mono">
              Predicted vs. actual emission, scored on each daily job run (model monitoring over time)
            </p>
            {accuracy.length === 0 ? (
              <p className="text-sm text-graphite-600 py-8 text-center">
                Run the daily job at least twice to see accuracy data — the first run creates a
                forecast, the second scores it against what actually happened.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={accuracy}>
                  <CartesianGrid stroke="#26332D" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="index" stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: '#1C2622', border: '1px solid #354339', borderRadius: 8 }} labelStyle={{ color: '#E7ECE9' }} />
                  <Legend wrapperStyle={{ fontSize: 11, color: '#5B6E63' }} />
                  <Line type="monotone" dataKey="predicted" name="Predicted" stroke="#F5A623" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="actual" name="Actual" stroke="#3DDC84" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Alerts */}
            <div className="animate-fade-in-up" style={{ animationDelay: '180ms' }}>
              <h3 className="font-display text-sm font-semibold text-white mb-3">Recent Alerts</h3>
              {alerts.length === 0 ? (
                <p className="text-sm text-graphite-600">No alerts yet — the fleet is clean.</p>
              ) : (
                <div className="space-y-2">
                  {alerts.map((a, i) => {
                    const style = ALERT_STYLES[a.type] || ALERT_STYLES.anomaly
                    return (
                      <div
                        key={a.id}
                        className={`border rounded-lg px-4 py-3 text-sm animate-fade-in-up ${style.badge}`}
                        style={{ animationDelay: `${i * 40}ms` }}
                      >
                        {a.type === 'anomaly' ? (
                          <>
                            {style.icon} <strong>{a.server_id}</strong> — {a.direction} to {a.carbon_emission} kg
                            (z={a.z_score}, expected ~{a.expected_avg_kg} kg)
                          </>
                        ) : (
                          <>
                            {style.icon} Fleet-wide budget breached: {a.total_emission_kg} kg / {a.budget_kg} kg limit
                          </>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Daily reports history */}
            <div className="animate-fade-in-up" style={{ animationDelay: '220ms' }}>
              <h3 className="font-display text-sm font-semibold text-white mb-3">Daily Report History</h3>
              {reports.length === 0 ? (
                <p className="text-sm text-graphite-600">No reports yet — run the daily job.</p>
              ) : (
                <div className="space-y-2">
                  {reports.map((r, i) => (
                    <div
                      key={r.id}
                      className="bg-graphite-900 border border-graphite-800 rounded-lg px-4 py-3 text-sm flex items-center justify-between animate-fade-in-up"
                      style={{ animationDelay: `${i * 40}ms` }}
                    >
                      <span className="text-graphite-400 font-mono text-xs">
                        {new Date(r.generated_at).toLocaleString()}
                      </span>
                      <span className="text-white font-mono">{r.total_emission_kg} kg</span>
                      {r.budget_breached && <span className="text-alert-500 text-xs">over budget</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
