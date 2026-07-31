import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api'

export default function ForgotPassword() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', email: '', new_password: '', confirm_password: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    try {
      const { data } = await api.post('/api/auth/password-reset/', form)
      setSuccess(data.detail)
      setTimeout(() => navigate('/login'), 1500)
    } catch (err) {
      const data = err?.response?.data
      if (data) {
        if (typeof data === 'string') {
          setError(data)
        } else if (data.detail) {
          setError(data.detail)
        } else {
          const messages = Object.entries(data)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join(' | ')
          setError(messages)
        }
      } else {
        setError('Unable to reset password. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <h1>Forgot password?</h1>
        <p className="page-sub">Enter your username and email to reset your password.</p>
        {error && <div className="error-banner">{error}</div>}
        {success && <div className="success-banner">{success}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Username</label>
            <input
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              required
              autoFocus
            />
          </div>
          <div className="field">
            <label>Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label>New password</label>
            <input
              type="password"
              minLength={6}
              value={form.new_password}
              onChange={(e) => setForm({ ...form, new_password: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label>Confirm password</label>
            <input
              type="password"
              minLength={6}
              value={form.confirm_password}
              onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
              required
            />
          </div>
          <button className="btn" type="submit" disabled={loading}>
            {loading ? 'Resetting…' : 'Reset password'}
          </button>
        </form>
        <div className="auth-switch">
          Remembered it? <Link to="/login">Log in</Link>
        </div>
      </div>
    </div>
  )
}
