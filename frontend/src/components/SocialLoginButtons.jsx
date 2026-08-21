import { useEffect, useState } from 'react'
import api from '../api'

export default function SocialLoginButtons({ error, setError }) {
  const [config, setConfig] = useState({
    googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
    githubClientId: import.meta.env.VITE_GITHUB_CLIENT_ID || '',
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Fetch fresh OAuth credentials dynamically from backend
    api.get('/api/auth/oauth/urls/')
      .then(({ data }) => {
        setConfig({
          googleClientId: data.google_client_id || import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
          githubClientId: data.github_client_id || import.meta.env.VITE_GITHUB_CLIENT_ID || '',
        })
      })
      .catch((err) => {
        console.warn('OAuth status check warning:', err?.message)
      })
  }, [])

  const redirectUri = `${window.location.origin}/oauth/callback`

  const handleGoogleLogin = async () => {
    setLoading(true)
    let clientId = ''
    try {
      const { data } = await api.get('/api/auth/oauth/urls/')
      clientId = data.google_client_id
    } catch (e) {
      // ignore
    }
    if (!clientId) {
      clientId = config.googleClientId || import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    }
    if (!clientId) {
      setLoading(false)
      if (setError) setError('Google OAuth is not configured yet. Please add GOOGLE_CLIENT_ID or VITE_GOOGLE_CLIENT_ID to your environment variables.')
      return
    }
    const scope = encodeURIComponent('openid email profile')
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=${scope}&state=google`
    window.location.href = authUrl
  }

  const handleGithubLogin = async () => {
    setLoading(true)
    let clientId = ''
    try {
      const { data } = await api.get('/api/auth/oauth/urls/')
      clientId = data.github_client_id
    } catch (e) {
      // ignore
    }
    if (!clientId) {
      clientId = config.githubClientId || import.meta.env.VITE_GITHUB_CLIENT_ID || ''
    }
    if (!clientId) {
      setLoading(false)
      if (setError) setError('GitHub OAuth is not configured yet. Please add GITHUB_CLIENT_ID or VITE_GITHUB_CLIENT_ID to your environment variables.')
      return
    }
    const scope = encodeURIComponent('user:email')
    const authUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${scope}&state=github`
    window.location.href = authUrl
  }

  return (
    <div className="social-auth-container" style={{ marginTop: '20px', marginBottom: '20px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          textAlign: 'center',
          color: 'var(--ink-soft, #64748b)',
          fontSize: '13px',
          fontWeight: 500,
          margin: '16px 0',
        }}
      >
        <div style={{ flex: 1, height: '1px', backgroundColor: 'var(--border-color, #e2e8f0)' }}></div>
        <span style={{ padding: '0 12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Or continue with</span>
        <div style={{ flex: 1, height: '1px', backgroundColor: 'var(--border-color, #e2e8f0)' }}></div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <button
          type="button"
          onClick={handleGoogleLogin}
          disabled={loading}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '10px 14px',
            borderRadius: '8px',
            border: '1px solid var(--border-color, #cbd5e1)',
            background: 'var(--surface-card, #ffffff)',
            color: 'var(--ink-primary, #0f172a)',
            fontSize: '14px',
            fontWeight: 600,
            cursor: loading ? 'wait' : 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = '#94a3b8'
            e.currentTarget.style.backgroundColor = 'var(--surface-hover, #f8fafc)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--border-color, #cbd5e1)'
            e.currentTarget.style.backgroundColor = 'var(--surface-card, #ffffff)'
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
            />
            <path
              fill="#34A853"
              d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.29v3.15C3.26 21.3 7.36 24 12 24z"
            />
            <path
              fill="#FBBC05"
              d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.29C.47 8.21 0 10.05 0 12s.47 3.79 1.29 5.42l3.99-3.15z"
            />
            <path
              fill="#EA4335"
              d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.36 0 3.26 2.7 1.29 6.58l3.99 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
            />
          </svg>
          <span>Google</span>
        </button>

        <button
          type="button"
          onClick={handleGithubLogin}
          disabled={loading}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '10px 14px',
            borderRadius: '8px',
            border: '1px solid var(--border-color, #cbd5e1)',
            background: '#24292e',
            color: '#ffffff',
            fontSize: '14px',
            fontWeight: 600,
            cursor: loading ? 'wait' : 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#1b1f23'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#24292e'
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path
              fillRule="evenodd"
              clipRule="evenodd"
              d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
            />
          </svg>
          <span>GitHub</span>
        </button>
      </div>
    </div>
  )
}
