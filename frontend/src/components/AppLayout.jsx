import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: '⌁', end: true },
  { to: '/servers', label: 'Servers', icon: '▤' },
  { to: '/monitoring', label: 'Monitoring', icon: '◈' },
  { to: '/analytics', label: 'Analytics', icon: '⌇' },
  { to: '/multi-cloud', label: 'Multi-Cloud', icon: '☁' },
  { to: '/optimization', label: 'Optimization', icon: '⟴' },
  { to: '/assistant', label: 'AI Assistant', icon: '✦' },
]

export default function AppLayout() {
  const { user, signOut } = useAuth()

  return (
    <div className="min-h-screen flex bg-graphite-950">
      <aside className="w-64 shrink-0 border-r border-graphite-800 flex flex-col">
        <div className="px-6 py-6">
          <div className="flex items-center gap-2">
            <span className="text-carbon-500 font-mono text-lg animate-pulse-dot">◉</span>
            <span className="font-display font-semibold text-lg tracking-tight text-white">
              Green<span className="text-carbon-500">AI</span>
            </span>
          </div>
          <p className="text-xs text-graphite-600 font-mono mt-1">GreenOps Control Room</p>
        </div>
        <div className="grid-divider mx-6" />

        <nav className="flex-1 px-3 py-6 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `focus-ring flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-graphite-800 text-carbon-400 border border-carbon-600/30'
                    : 'text-graphite-400 hover:text-white hover:bg-graphite-900'
                }`
              }
            >
              <span className="font-mono text-base w-4 text-center">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="grid-divider mx-6" />
        <div className="px-6 py-5">
          <p className="text-sm text-white font-medium truncate">{user?.name}</p>
          <p className="text-xs text-graphite-600 truncate mb-3">{user?.email}</p>
          <button
            onClick={signOut}
            className="focus-ring text-xs text-graphite-500 hover:text-alert-500 transition-colors"
          >
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
