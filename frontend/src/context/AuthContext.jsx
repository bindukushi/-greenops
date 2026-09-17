import { createContext, useContext, useEffect, useState } from 'react'
import * as api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('greenai_user')
    return stored ? JSON.parse(stored) : null
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('greenai_token')
    if (!token) {
      setLoading(false)
      return
    }
    api.getMe()
      .then((res) => setUser(res.data))
      .catch(() => {
        localStorage.removeItem('greenai_token')
        localStorage.removeItem('greenai_user')
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const signIn = async (email, password) => {
    const res = await api.login(email, password)
    localStorage.setItem('greenai_token', res.data.access_token)
    localStorage.setItem('greenai_user', JSON.stringify(res.data.user))
    setUser(res.data.user)
    return res.data.user
  }

  const signUp = async (name, email, password) => {
    const res = await api.register(name, email, password)
    localStorage.setItem('greenai_token', res.data.access_token)
    localStorage.setItem('greenai_user', JSON.stringify(res.data.user))
    setUser(res.data.user)
    return res.data.user
  }

  const signOut = () => {
    localStorage.removeItem('greenai_token')
    localStorage.removeItem('greenai_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
