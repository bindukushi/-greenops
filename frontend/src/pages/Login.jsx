import { useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { user, signIn, signUp } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('admin@greenai.io')
  const [password, setPassword] = useState('GreenAI@123')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      if (mode === 'login') {
        await signIn(email, password)
      } else {
        await signUp(name, email, password)
      }
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex bg-graphite-950 relative overflow-hidden">
      {/* Ambient grid pulse lines - signature element evoking a power/telemetry readout */}
      <div className="absolute inset-0 pointer-events-none opacity-40">
        {[18, 38, 62, 84].map((top) => (
          <div key={top} className="grid-divider absolute left-0 right-0" style={{ top: `${top}%` }} />
        ))}
      </div>

      <div className="hidden lg:flex flex-col justify-between w-1/2 px-16 py-14 relative z-10">
        <div className="flex items-center gap-2">
          <span className="text-carbon-500 font-mono text-xl">◉</span>
          <span className="font-display font-semibold text-xl text-white">
            Green<span className="text-carbon-500">AI</span>
          </span>
        </div>

        <div>
          <p className="font-mono text-xs text-energy-500 tracking-widest uppercase mb-4">
            Cloud Sustainability Platform
          </p>
          <h1 className="font-display text-5xl leading-tight text-white font-semibold mb-6">
            Every watt,<br />
            <span className="text-carbon-400">accounted for.</span>
          </h1>
          <p className="text-graphite-400 max-w-md leading-relaxed">
            Monitor cloud infrastructure, forecast carbon emissions with machine learning,
            and act on GreenOps recommendations before waste hits your footprint — or your bill.
          </p>
        </div>

        <div className="flex gap-8 font-mono text-sm text-graphite-500">
          <div>
            <div className="text-carbon-400 text-2xl font-display">97.4%</div>
            model confidence
          </div>
          <div>
            <div className="text-energy-500 text-2xl font-display">6</div>
            regions compared
          </div>
          <div>
            <div className="text-white text-2xl font-display">24/7</div>
            live monitoring
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center px-6 relative z-10">
        <div className="w-full max-w-sm bg-graphite-900 border border-graphite-800 rounded-2xl p-8 shadow-2xl shadow-black/40">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <span className="text-carbon-500 font-mono text-lg">◉</span>
            <span className="font-display font-semibold text-lg text-white">
              Green<span className="text-carbon-500">AI</span>
            </span>
          </div>

          <h2 className="font-display text-xl text-white font-semibold mb-1">
            {mode === 'login' ? 'Welcome back' : 'Create your account'}
          </h2>
          <p className="text-sm text-graphite-500 mb-6">
            {mode === 'login'
              ? 'Sign in to your GreenOps console.'
              : 'Set up access to the sustainability dashboard.'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="block text-xs font-mono text-graphite-500 mb-1.5">Name</label>
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="focus-ring w-full bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-graphite-600"
                  placeholder="Ada Lovelace"
                />
              </div>
            )}
            <div>
              <label className="block text-xs font-mono text-graphite-500 mb-1.5">Email</label>
              <input
                required
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="focus-ring w-full bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-graphite-600"
                placeholder="you@company.com"
              />
            </div>
            <div>
              <label className="block text-xs font-mono text-graphite-500 mb-1.5">Password</label>
              <input
                required
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={6}
                className="focus-ring w-full bg-graphite-800 border border-graphite-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder-graphite-600"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <p className="text-sm text-alert-500 bg-alert-500/10 border border-alert-500/20 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={busy}
              className="focus-ring w-full bg-carbon-500 hover:bg-carbon-400 active:scale-95 disabled:opacity-60 text-graphite-950 font-semibold text-sm rounded-lg py-2.5 transition-all"
            >
              {busy ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>

          <p className="text-xs text-graphite-600 mt-4 font-mono">
            Demo login: admin@greenai.io / GreenAI@123 (run seed.py first)
          </p>

          <button
            onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
            className="focus-ring text-sm text-graphite-400 hover:text-carbon-400 mt-6 w-full text-center transition-colors"
          >
            {mode === 'login' ? "Don't have an account? Register" : 'Already have an account? Sign in'}
          </button>
        </div>
      </div>
    </div>
  )
}
