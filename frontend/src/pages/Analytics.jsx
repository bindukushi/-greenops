import { useEffect, useState, useCallback } from 'react'
import * as api from '../services/api'
import { downloadBlob } from '../services/download'
import PageHeader from '../components/PageHeader'
import { ChartSkeleton } from '../components/Skeleton'
import { EmptyState, ErrorBanner } from '../components/States'

export default function Analytics() {
  const [servers, setServers] = useState([])
  const [selectedServer, setSelectedServer] = useState('')
  const [form, setForm] = useState({
    cpu_usage: 78, memory_usage: 65, storage: 420, network_traffic: 45,
    energy_consumption: 310, temperature: 24, region: 'ap-south-1',
    horizon_days: 7, model_name: 'random_forest',
  })
  const [prediction, setPrediction] = useState(null)
  const [modelMetrics, setModelMetrics] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [exportingCsv, setExportingCsv] = useState(false)

  const loadInitial = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [serversRes, metricsRes] = await Promise.all([
        api.getServers(),
        api.getModelMetrics().catch(() => ({ data: null })),
      ])
      setServers(serversRes.data.servers)
      if (serversRes.data.servers.length) setSelectedServer(serversRes.data.servers[0])
      setModelMetrics(metricsRes.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load analytics data.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadInitial()
  }, [loadInitial])

  useEffect(() => {
    if (!selectedServer) return
    api.getPredictionHistory({ server_id: selectedServer, limit: 5 })
      .then((r) => setHistory(r.data))
      .catch(() => setHistory([]))
  }, [selectedServer, prediction])

  const handlePredict = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const res = await api.predictEmission({ ...form, server_id: selectedServer || 'AWS001' })
      setPrediction(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed. Please check the input values.')
    } finally {
      setBusy(false)
    }
  }

  const handleDownload = async () => {
    setDownloading(true)
    try {
      const res = await api.downloadPdfReport(selectedServer)
      downloadBlob(res.data, 'greenai_carbon_report.pdf', 'application/pdf')
    } catch {
      setError('Could not generate PDF report right now.')
    } finally {
      setDownloading(false)
    }
  }

  const handleExportCsv = async () => {
    setExportingCsv(true)
    try {
      const res = await api.exportMetricsCsv(selectedServer)
      downloadBlob(res.data, `greenai_${selectedServer || 'all'}_metrics.csv`, 'text/csv')
    } catch {
      setError('Could not export CSV right now.')
    } finally {
      setExportingCsv(false)
    }
  }

  const field = (key, label, step = 1) => (
    <div>
      <label className="block text-xs font-mono text-graphite-500 mb-1.5">{label}</label>
      <input
        type="number"
        step={step}
        value={form[key]}
        onChange={(e) => setForm({ ...form, [key]: parseFloat(e.target.value) })}
        className="focus-ring w-full bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-2 text-sm text-white transition-colors focus:border-carbon-600"
      />
    </div>
  )

  return (
    <div className="px-8 py-8 max-w-7xl">
      <PageHeader
        eyebrow="Machine Learning"
        title="Analytics & Forecasting"
        description="Predict future carbon emissions using trained Random Forest / XGBoost models."
        action={
          <div className="flex gap-2">
            <button
              onClick={handleExportCsv}
              disabled={exportingCsv}
              className="focus-ring text-sm bg-graphite-800 hover:bg-graphite-700 active:scale-95 border border-graphite-700 text-graphite-300 font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-50"
            >
              {exportingCsv ? 'Exporting...' : '⬇ Export CSV'}
            </button>
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="focus-ring text-sm bg-graphite-800 hover:bg-graphite-700 active:scale-95 border border-graphite-700 text-carbon-400 font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-60"
            >
              {downloading ? 'Preparing PDF...' : '⬇ Download PDF report'}
            </button>
          </div>
        }
      />

      {error && (
        <div className="mb-6">
          <ErrorBanner message={error} onRetry={loadInitial} />
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2"><ChartSkeleton height={340} /></div>
          <ChartSkeleton height={340} />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
          <form
            onSubmit={handlePredict}
            className="lg:col-span-2 bg-graphite-900 border border-graphite-800 rounded-2xl p-6 animate-fade-in-up"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display text-sm font-semibold text-white">Forecast Emission</h3>
              {servers.length > 0 && (
                <select
                  value={selectedServer}
                  onChange={(e) => setSelectedServer(e.target.value)}
                  className="focus-ring bg-graphite-800 border border-graphite-700 rounded-lg px-2 py-1.5 text-xs text-white"
                >
                  {servers.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              )}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
              {field('cpu_usage', 'CPU usage (%)')}
              {field('memory_usage', 'Memory usage (%)')}
              {field('storage', 'Storage (GB)')}
              {field('network_traffic', 'Network (GB)')}
              {field('energy_consumption', 'Energy (kWh)')}
              {field('temperature', 'Temp (°C)')}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-5">
              <div>
                <label className="block text-xs font-mono text-graphite-500 mb-1.5">Region</label>
                <select
                  value={form.region}
                  onChange={(e) => setForm({ ...form, region: e.target.value })}
                  className="focus-ring w-full bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-2 text-sm text-white"
                >
                  {['ap-south-1', 'us-east-1', 'us-west-2', 'eu-west-1', 'eu-north-1', 'sa-east-1'].map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-mono text-graphite-500 mb-1.5">Horizon (days)</label>
                <input
                  type="number"
                  min={1}
                  max={30}
                  value={form.horizon_days}
                  onChange={(e) => setForm({ ...form, horizon_days: parseInt(e.target.value) })}
                  className="focus-ring w-full bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-2 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-graphite-500 mb-1.5">Model</label>
                <select
                  value={form.model_name}
                  onChange={(e) => setForm({ ...form, model_name: e.target.value })}
                  className="focus-ring w-full bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-2 text-sm text-white"
                >
                  <option value="random_forest">Random Forest</option>
                  <option value="xgboost">XGBoost</option>
                </select>
              </div>
            </div>
            <button
              type="submit"
              disabled={busy}
              className="focus-ring bg-carbon-500 hover:bg-carbon-400 active:scale-95 text-graphite-950 font-semibold text-sm px-5 py-2.5 rounded-lg transition-all disabled:opacity-60"
            >
              {busy ? 'Running model...' : 'Run forecast'}
            </button>
          </form>

          <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-6 flex flex-col animate-fade-in-up" style={{ animationDelay: '80ms' }}>
            <h3 className="font-display text-sm font-semibold text-white mb-4">Prediction Result</h3>
            {prediction ? (
              <div className="animate-fade-in-up">
                <div className="font-display text-4xl font-semibold text-carbon-400 mb-1">
                  {prediction.predicted_emission_kg}
                  <span className="text-lg text-graphite-500 ml-1">kg CO₂</span>
                </div>
                <p className="text-xs text-graphite-500 font-mono mb-4">
                  over next {prediction.horizon_days} days · {prediction.model_used.replace('_', ' ')}
                </p>
                <div className="flex items-center gap-2 mb-5">
                  <div className="flex-1 h-1.5 bg-graphite-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-energy-500 transition-all duration-700 ease-out"
                      style={{ width: `${prediction.confidence}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono text-graphite-400">{prediction.confidence}% confidence</span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-graphite-600 mb-4">Run a forecast to see the projected carbon output here.</p>
            )}

            {history.length > 0 && (
              <div className="pt-4 border-t border-graphite-800">
                <p className="text-xs font-mono text-graphite-500 uppercase tracking-wide mb-2">Recent predictions</p>
                <div className="space-y-1.5">
                  {history.map((h) => (
                    <div key={h.id} className="flex items-center justify-between text-xs">
                      <span className="text-graphite-500 font-mono">
                        {new Date(h.generated_at).toLocaleDateString()} · {h.model_used.replace('_', ' ')}
                      </span>
                      <span className="text-white font-mono">{h.predicted_emission_kg} kg</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {modelMetrics && (
              <div className="mt-auto pt-4 border-t border-graphite-800 text-xs font-mono text-graphite-500 space-y-1">
                <div>RF R²: {modelMetrics.random_forest.r2_score} · MAE {modelMetrics.random_forest.mae_kg_co2}kg</div>
                <div>XGB R²: {modelMetrics.xgboost.r2_score} · MAE {modelMetrics.xgboost.mae_kg_co2}kg</div>
              </div>
            )}
          </div>
        </div>
      )}

      {!loading && servers.length === 0 && (
        <EmptyState
          icon="⌇"
          title="No servers to forecast yet"
          description="Simulate CloudWatch ingest on the Dashboard first, then come back to run a forecast."
        />
      )}
    </div>
  )
}
