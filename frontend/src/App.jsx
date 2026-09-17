import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Servers from './pages/Servers'
import ServerDetail from './pages/ServerDetail'
import Monitoring from './pages/Monitoring'
import Analytics from './pages/Analytics'
import MultiCloud from './pages/MultiCloud'
import Optimization from './pages/Optimization'
import Assistant from './pages/Assistant'
import AppLayout from './components/AppLayout'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-graphite-950 text-graphite-400">
        Loading GreenAI...
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <AppLayout />
              </PrivateRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="servers" element={<Servers />} />
            <Route path="servers/:serverId" element={<ServerDetail />} />
            <Route path="monitoring" element={<Monitoring />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="multi-cloud" element={<MultiCloud />} />
            <Route path="optimization" element={<Optimization />} />
            <Route path="assistant" element={<Assistant />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
