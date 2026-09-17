import { useEffect, useState, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
} from 'recharts'
import * as api from '../services/api'
import { downloadBlob } from '../services/download'
import PageHeader from '../components/PageHeader'
import { ChartSkeleton } from '../components/Skeleton'
import { EmptyState, ErrorBanner } from '../components/States'

const PROVIDER_META = {
  AWS: { color: '#F5A623', label: 'Amazon Web Services' },
  Azure: { color: '#3DDC84', label: 'Microsoft Azure' },
  GCP: { color: '#6EE7A8', label: 'Google Cloud Platform' },
}

function ProviderCard({ item, rank }) {
  const meta = PROVIDER_META[item.provider] || { color: '#5B6E63', label: item.provider }
  const isGreenest = rank === 1

  return (
    <div
      className={`bg-graphite-900 border rounded-2xl p-5 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/30 animate-fade-in-up ${
        isGreenest ? 'border-carbon-600/40' : 'border-graphite-800'
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: meta.color }} />
          <span className="font-display font-semibold text-white">{item.provider}</span>
        </div>
        {isGreenest && (
          <span className="text-[10px] font-mono uppercase tracking-wide bg-carbon-500/10 text-carbon-400 border border-carbon-600/30 px-2 py-0.5 rounded-full">
            Greenest
          </span>
        )}
      </div>
      <p className="text-xs text-graphite-500 mb-4">{meta.label}</p>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div className="text-xs font-mono text-graphite-500 mb-0.5">Avg Carbon</div>
          <div className="font-display text-lg text-white">{item.avg_carbon_kg} kg</div>
        </div>
        <div>
          <div className="text-xs font-mono text-graphite-500 mb-0.5">Avg Energy</div>
          <div className="font-display text-lg text-white">{item.avg_energy_kwh} kWh</div>
        </div>
        <div>
          <div className="text-xs font-mono text-graphite-500 mb-0.5">Servers</div>
          <div className="font-display text-lg text-white">{item.server_count}</div>
        </div>
        <div>
          <div className="text-xs font-mono text-graphite-500 mb-0.5">Rank</div>
          <div className="font-display text-lg text-white">#{item.efficiency_rank}</div>
        </div>
      </div>
    </div>
  )
}

export default function MultiCloud() {
  const [providerData, setProviderData] = useState([])
  const [regionData, setRegionData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState(false)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [providerRes, regionRes] = await Promise.all([
        api.getProviderComparison(),
        api.getMultiCloudComparison(),
      ])
      setProviderData(providerRes.data.comparison)
      setRegionData(regionRes.data.comparison)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load multi-cloud comparison.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleExport = async () => {
    setExporting(true)
    try {
      const res = await api.exportMetricsCsv()
      downloadBlob(res.data, 'greenai_multi_cloud_metrics.csv', 'text/csv')
    } catch {
      setError('Could not export CSV right now.')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="px-8 py-8 max-w-6xl">
      <PageHeader
        eyebrow="Multi-Cloud"
        title="AWS vs Azure vs GCP"
        description="Carbon efficiency ranking across simulated cloud providers and regions."
        action={
          <button
            onClick={handleExport}
            disabled={exporting}
            className="focus-ring text-sm bg-graphite-800 hover:bg-graphite-700 active:scale-95 border border-graphite-700 text-graphite-300 font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-50"
          >
            {exporting ? 'Exporting...' : '⬇ Export CSV'}
          </button>
        }
      />

      {error && (
        <div className="mb-6">
          <ErrorBanner message={error} onRetry={loadData} />
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
          {Array.from({ length: 3 }).map((_, i) => (
            <ChartSkeleton key={i} height={140} />
          ))}
        </div>
      ) : providerData.length === 0 ? (
        <EmptyState
          icon="☁"
          title="No multi-cloud data yet"
          description="Visit the Dashboard and click 'Simulate CloudWatch ingest' to populate telemetry across AWS, Azure, and GCP."
        />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
            {providerData.map((item) => (
              <ProviderCard key={item.provider} item={item} rank={item.efficiency_rank} />
            ))}
          </div>

          <div className="bg-graphite-900 border border-graphite-800 rounded-2xl p-6">
            <h3 className="font-display text-sm font-semibold text-white mb-1">Region-Level Breakdown</h3>
            <p className="text-xs text-graphite-500 mb-4 font-mono">
              Average carbon output per region across all providers — lower is greener
            </p>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={regionData}>
                <CartesianGrid stroke="#26332D" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="region" stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#5B6E63" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ background: '#1C2622', border: '1px solid #354339', borderRadius: 8 }}
                  labelStyle={{ color: '#E7ECE9' }}
                />
                <Bar dataKey="avg_carbon_kg" radius={[6, 6, 0, 0]} animationDuration={800}>
                  {regionData.map((_, i) => (
                    <Cell
                      key={i}
                      fill={['#3DDC84', '#6EE7A8', '#F5A623', '#FFC670', '#F2664B', '#5B6E63'][i % 6]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  )
}
