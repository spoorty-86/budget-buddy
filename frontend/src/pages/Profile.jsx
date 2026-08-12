import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import api from '../api'

export default function Profile() {
  const { profile, refreshProfile } = useAuth()
  const [fullName, setFullName] = useState('')
  const [currency, setCurrency] = useState('INR')
  const [monthlyTarget, setMonthlyTarget] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name || '')
      setCurrency(profile.currency || 'INR')
      setMonthlyTarget(profile.monthly_income_target || '')
    }
  }, [profile])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')
    setError('')

    try {
      await api.patch('/api/auth/me/', {
        full_name: fullName,
        currency: currency,
        monthly_income_target: monthlyTarget !== '' ? Number(monthlyTarget) : 0,
      })
      if (typeof refreshProfile === 'function') {
        await refreshProfile()
      }
      setMessage('Profile updated successfully!')
    } catch (err) {
      const detail = err?.response?.data
        ? JSON.stringify(err.response.data)
        : err?.message || 'Failed to update profile. Please check your inputs.'
      setError(detail)
    } finally {
      setSaving(false)
    }
  }

  const getInitials = (name) => {
    if (!name) return 'U'
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .substring(0, 2)
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div>
          <h1>My Profile</h1>
          <p className="page-sub">Manage your account details, preferences, and financial defaults.</p>
        </div>
      </div>

      {message && <div style={{ background: 'rgba(46, 125, 50, 0.12)', border: '1px solid #2e7d32', color: '#1b5e20', padding: '12px 16px', borderRadius: 8, marginBottom: 20 }}>{message}</div>}
      {error && <div className="error-banner">{error}</div>}

      <div className="card" style={{ marginBottom: 24, display: 'flex', alignItems: 'center', gap: 20, padding: 24 }}>
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: 'var(--gold)',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 24,
            fontWeight: 700,
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          }}
        >
          {getInitials(profile?.full_name || profile?.username)}
        </div>
        <div>
          <h2 style={{ margin: 0, fontSize: 20 }}>{profile?.full_name || profile?.username}</h2>
          <p style={{ margin: '4px 0 0', color: 'var(--ink-soft)', fontSize: 14 }}>
            @{profile?.username} • {profile?.email}
          </p>
          <span className="tag" style={{ marginTop: 8, display: 'inline-block' }}>
            Currency: {profile?.currency === 'INR' ? '₹ (INR)' : profile?.currency || 'INR'}
          </span>
        </div>
      </div>

      <div className="card" style={{ padding: 24 }}>
        <h3 style={{ marginTop: 0, marginBottom: 18, fontSize: 16 }}>Edit Personal Information</h3>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div className="field">
              <label>Username</label>
              <input value={profile?.username || ''} disabled style={{ opacity: 0.7, cursor: 'not-allowed' }} />
            </div>
            <div className="field">
              <label>Email Address</label>
              <input value={profile?.email || ''} disabled style={{ opacity: 0.7, cursor: 'not-allowed' }} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div className="field">
              <label>Full Name</label>
              <input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Your Full Name"
              />
            </div>
            <div className="field">
              <label>Preferred Currency</label>
              <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
                <option value="INR">₹ (Indian Rupee - INR)</option>
                <option value="USD">$ (US Dollar - USD)</option>
                <option value="EUR">€ (Euro - EUR)</option>
                <option value="GBP">£ (British Pound - GBP)</option>
              </select>
            </div>
          </div>

          <div className="field" style={{ marginBottom: 24 }}>
            <label>Monthly Income Target</label>
            <input
              type="number"
              step="0.01"
              value={monthlyTarget}
              onChange={(e) => setMonthlyTarget(e.target.value)}
              placeholder="e.g. 50000.00"
            />
          </div>

          <button className="btn" type="submit" disabled={saving}>
            {saving ? 'Saving...' : '💾 Save Profile Changes'}
          </button>
        </form>
      </div>
    </div>
  )
}
