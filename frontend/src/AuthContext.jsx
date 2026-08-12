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
    } catch {
      setProfile(null)
    }
  }, [])

  useEffect(() => {
    const token = localStorage.getItem('access')
    if (token) {
      loadProfile().finally(() => setReady(true))
    } else {
      setReady(true)
    }
  }, [loadProfile])

  async function login(username, password) {
    const { data } = await api.post('/api/auth/login/', { username, password })
    localStorage.setItem('access', data.access)
    localStorage.setItem('refresh', data.refresh)
    await loadProfile()
  }

  async function register(payload) {
    // Register the user
    const registerResponse = await api.post('/api/auth/register/', payload)
    // Auto-login after successful registration
    try {
      await login(payload.username, payload.password)
    } catch (err) {
      // If auto-login fails, at least the user is registered
      // Re-throw so the component can handle it
      throw new Error('Registration successful but login failed. Please try logging in manually.')
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
