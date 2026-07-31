import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', email: '', full_name: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      // Validate inputs
      if (!form.username.trim()) throw new Error('Username is required')
      if (!form.email.trim()) throw new Error('Email is required')
      if (!form.password || form.password.length < 6) throw new Error('Password must be at least 6 characters')
      
      await register(form)
      navigate('/')
    } catch (err) {
      let msg = 'Registration failed. Please try again.'
      
      // Handle custom error messages from register function
      if (err.message) {
        msg = err.message
      }
      
      // Handle API validation errors
      const data = err?.response?.data
      if (data) {
        if (typeof data === 'string') {
          msg = data
        } else if (Array.isArray(data)) {
          msg = data.flat().join(', ')
        } else if (data.detail) {
          msg = data.detail
        } else {
          // Extract all field errors
          const errors = Object.entries(data)
            .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(', ') : errors}`)
            .join('. ')
          if (errors) msg = errors
        }
      }
      
      setError(msg)
      console.error('Registration error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <h1>Open a ledger</h1>
        <p className="page-sub">Create your BudgetBuddy account.</p>
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Full name</label>
            <input
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
          </div>
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
            <label>Password</label>
            <input
              type="password"
              minLength={6}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>
          <button className="btn" type="submit" disabled={loading}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>
        <div className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </div>
      </div>
    </div>
  )
}
