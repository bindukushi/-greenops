import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('greenai_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('greenai_token')
      localStorage.removeItem('greenai_user')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

// --- Auth ---
export const login = (email, password) => api.post('/auth/login', { email, password })
export const register = (name, email, password) => api.post('/auth/register', { name, email, password })
export const getMe = () => api.get('/auth/me')

// --- Cloud monitoring ---
export const getSummary = () => api.get('/cloud/summary')
export const getServers = () => api.get('/cloud/servers')
export const getServersOverview = () => api.get('/cloud/servers/overview')
export const getServerDetail = (serverId) => api.get(`/cloud/servers/${serverId}/detail`)
export const getMetrics = (params) => api.get('/cloud/metrics', { params })
export const simulateCloudWatch = (days = 60) => api.post(`/cloud/simulate?days=${days}`)
export const ingestMetric = (payload) => api.post('/cloud/metrics', payload)
export const getResourceUsage = () => api.get('/cloud/resource-usage')
export const exportMetricsCsv = (server_id) =>
  api.get('/cloud/export/csv', { params: server_id ? { server_id } : {}, responseType: 'blob' })

// --- Live mode (real-time simulated streaming) ---
export const startLiveMode = (interval_seconds = 5) =>
  api.post(`/cloud/live/start?interval_seconds=${interval_seconds}`)
export const stopLiveMode = () => api.post('/cloud/live/stop')
export const getLiveStatus = () => api.get('/cloud/live/status')

// --- Real AWS CloudWatch integration (optional add-on) ---
export const getAwsStatus = () => api.get('/cloud/aws/status')
export const syncRealAws = (instanceIds, region) =>
  api.post('/cloud/aws/sync', null, { params: { instance_ids: instanceIds, region } })

// --- Daily monitoring: scheduled forecasts, accuracy, anomalies, budget ---
export const runDailyJob = () => api.post('/monitoring/run-daily-job')
export const getDailyReports = (limit = 14) => api.get('/monitoring/daily-reports', { params: { limit } })
export const getAlerts = (params) => api.get('/monitoring/alerts', { params })
export const getForecastAccuracy = (params) => api.get('/monitoring/forecast-accuracy', { params })
export const getMonitoringBudget = () => api.get('/monitoring/budget')
export const setMonitoringBudget = (daily_limit_kg) => api.put('/monitoring/budget', { daily_limit_kg })
export const getMonitoringSchedulerStatus = () => api.get('/monitoring/scheduler/status')
export const injectTestAnomaly = (server_id) =>
  api.post('/monitoring/inject-test-anomaly', null, { params: { server_id } })

// --- Carbon engine ---
export const calculateCarbon = (energy_kwh, region) => api.post('/carbon/calculate', { energy_kwh, region })
export const getCarbonTrend = (params) => api.get('/carbon/trend', { params })
export const getEnergyTrend = (params) => api.get('/carbon/energy-trend', { params })
export const getMultiCloudComparison = () => api.get('/carbon/multi-cloud-comparison')
export const getProviderComparison = () => api.get('/carbon/provider-comparison')
export const downloadPdfReport = (server_id) =>
  api.get('/carbon/report/pdf', { params: { server_id }, responseType: 'blob' })

// --- Prediction ---
export const predictEmission = (payload) => api.post('/predict/', payload)
export const getModelMetrics = () => api.get('/predict/metrics')
export const getPredictionHistory = (params) => api.get('/predict/history', { params })

// --- GreenOps ---
export const getRecommendations = (server_id) =>
  api.get('/greenops/recommendations', { params: server_id ? { server_id } : {} })

// --- AI Assistant ---
export const askAssistant = (message, server_id) => api.post('/chat/ask', { message, server_id })
export const getChatHistory = () => api.get('/chat/history')

export default api
