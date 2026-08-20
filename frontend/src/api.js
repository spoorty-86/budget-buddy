import axios from 'axios'

const rawApiUrl = import.meta.env.VITE_API_URL || 'https://budgetbuddy-backend-es1w.onrender.com'
const API_URL = rawApiUrl.replace(/\/+$/, '')

const api = axios.create({ baseURL: API_URL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  config.headers['bypass-tunnel-reminder'] = '1'
  return config
})

// If a request fails with 401, try refreshing the access token once,
// then replay the original request.
let refreshing = null

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const { config, response } = error
    if (response?.status === 401 && !config._retried) {
      config._retried = true
      const refresh = localStorage.getItem('refresh')
      if (refresh) {
        try {
          refreshing = refreshing || axios.post(`${API_URL}/api/auth/refresh/`, { refresh })
          const { data } = await refreshing
          refreshing = null
          localStorage.setItem('access', data.access)
          config.headers.Authorization = `Bearer ${data.access}`
          return api(config)
        } catch (e) {
          refreshing = null
          localStorage.removeItem('access')
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api
export { API_URL }
