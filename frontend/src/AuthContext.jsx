import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import api from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [profile, setProfile] = useState(null)
  const [ready, setReady] = useState(false)

  const loadProfile = useCallback(async () => {
    try {
      const { data } = await api.get('/api/auth/me/')
      setProfile(data)
      return data
    } catch (err) {
      setProfile(null)
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
      throw err
    }
  }, [])

  useEffect(() => {
    const token = localStorage.getItem('access')
    if (token) {
      loadProfile()
        .catch(() => {})
        .finally(() => setReady(true))
    } else {
      setReady(true)
    }
  }, [loadProfile])

  async function login(username, password) {
    // Clear any stale tokens before initiating login
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')

    const { data } = await api.post('/api/auth/login/', { username, password })
    localStorage.setItem('access', data.access)
    localStorage.setItem('refresh', data.refresh)

    try {
      await loadProfile()
    } catch (err) {
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
      setProfile(null)
      throw new Error('Successfully authenticated, but failed to load user profile. Please try signing in again.')
    }
  }

  async function register(payload) {
    // Clear any stale tokens before registering
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')

    const registerResponse = await api.post('/api/auth/register/', payload)
    // Auto-login after successful registration
    try {
      await login(payload.username, payload.password)
    } catch (err) {
      // If auto-login fails, user is registered but needs manual login
      throw new Error('Registration successful! Please sign in with your new username and password.')
    }
    return registerResponse
  }

  function logout() {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    setProfile(null)
  }

  return (
    <AuthContext.Provider value={{ profile, ready, login, register, logout, reload: loadProfile, refreshProfile: loadProfile }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
