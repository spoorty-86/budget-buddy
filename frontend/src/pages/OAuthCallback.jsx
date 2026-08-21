import { useEffect, useState, useRef } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import api from '../api'
import { formatApiError } from '../utils/errors'

export default function OAuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { reload } = useAuth()
  const [status, setStatus] = useState('Authenticating with OAuth provider...')
  const [error, setError] = useState('')
  const processedRef = useRef(false)

  useEffect(() => {
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const providerParam = searchParams.get('provider')
    const provider = providerParam || state || (window.location.href.includes('google') ? 'google' : 'github')

    if (!code) {
      const authError = searchParams.get('error_description') || searchParams.get('error') || 'No authorization code was provided by the identity provider.'
      setError(`OAuth Login Canceled or Failed: ${authError}`)
      return
    }

    if (processedRef.current) {
      return
    }
    processedRef.current = true

    const redirectUri = `${window.location.origin}/oauth/callback`

    const processOAuth = async () => {
      try {
        setStatus(`Completing sign in with ${provider.charAt(0).toUpperCase() + provider.slice(1)}…`)

        const { data } = await api.post('/api/auth/oauth/', {
          provider,
          code,
          redirect_uri: redirectUri,
        })

        if (!data.access || !data.refresh) {
          throw new Error('Server response did not include valid authentication tokens.')
        }

        // Store tokens
        localStorage.setItem('access', data.access)
        localStorage.setItem('refresh', data.refresh)

        // Reload user profile in AuthContext
        await reload()

        setStatus('Authentication successful! Redirecting...')
        navigate('/', { replace: true })
      } catch (err) {
        localStorage.removeItem('access')
        localStorage.removeItem('refresh')
        const msg = formatApiError(err, `Failed to complete ${provider} authentication.`)
        setError(msg)
      }
    }

    processOAuth()
  }, [searchParams, navigate, reload])

  return (
    <div className="auth-shell">
      <div className="auth-card" style={{ textAlign: 'center', padding: '36px 24px' }}>
        <div className="brand" style={{ padding: 0, borderBottom: 'none', marginBottom: 16, fontSize: 30 }}>
          Budget<span>Buddy</span>
        </div>

        {error ? (
          <div>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                color: '#ef4444',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 16px auto',
              }}
            >
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <h2 style={{ fontSize: 20, marginBottom: 8, color: 'var(--ink-primary)' }}>Authentication Failed</h2>
            <p style={{ color: 'var(--ink-soft)', fontSize: 14, marginBottom: 24, lineHeight: 1.5 }}>{error}</p>
            <Link to="/login" className="btn" style={{ display: 'inline-block', textDecoration: 'none' }}>
              Return to Sign In
            </Link>
          </div>
        ) : (
          <div>
            <div style={{ margin: '20px 0' }}>
              <div
                style={{
                  width: 44,
                  height: 44,
                  border: '3px solid var(--border-color, #e2e8f0)',
                  borderTopColor: 'var(--green, #10b981)',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                  margin: '0 auto 16px auto',
                }}
              />
              <style>{`
                @keyframes spin {
                  0% { transform: rotate(0deg); }
                  100% { transform: rotate(360deg); }
                }
              `}</style>
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8, color: 'var(--ink-primary)' }}>Social Authentication</h2>
            <p style={{ color: 'var(--ink-soft)', fontSize: 14 }}>{status}</p>
          </div>
        )}
      </div>
    </div>
  )
}
