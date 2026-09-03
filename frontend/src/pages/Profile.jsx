import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import api from '../api'

export default function Profile() {
  const { profile, refreshProfile } = useAuth()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [currency, setCurrency] = useState('INR')
  const [monthlyTarget, setMonthlyTarget] = useState('')
  const [avatar, setAvatar] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name || '')
      setEmail(profile.email || '')
      setCurrency(profile.currency || 'INR')
      setMonthlyTarget(profile.monthly_income_target || '')
      setAvatar(profile.avatar || '')
    }
  }, [profile])

  const handleFileUpload = (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (file.size > 2 * 1024 * 1024) {
      setError('Image size should be less than 2MB.')
      return
    }

    const reader = new FileReader()
    reader.onloadend = () => {
      setAvatar(reader.result)
    }
    reader.readAsDataURL(file)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')
    setError('')

    try {
      await api.patch('/api/auth/me/', {
        full_name: fullName,
        email: email,
        currency: currency,
        monthly_income_target: monthlyTarget !== '' ? Number(monthlyTarget) : 0,
        avatar: avatar,
      })
      if (typeof refreshProfile === 'function') {
        await refreshProfile()
      }
      setMessage('Profile and email settings updated successfully! ✨')
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
          <p className="page-sub">Manage your profile photo, account email, and financial defaults.</p>
        </div>
      </div>

      {message && <div style={{ background: 'rgba(46, 125, 50, 0.12)', border: '1px solid #2e7d32', color: '#1b5e20', padding: '12px 16px', borderRadius: 8, marginBottom: 20 }}>{message}</div>}
      {error && <div className="error-banner">{error}</div>}

      {/* Profile Header Badge Card */}
      <div className="card" style={{ marginBottom: 24, display: 'flex', alignItems: 'center', gap: 20, padding: 24 }}>
        <div style={{ position: 'relative' }}>
          {avatar ? (
            <img
              src={avatar}
              alt="Profile"
              style={{
                width: 72,
                height: 72,
                borderRadius: '50%',
                objectFit: 'cover',
                border: '3px solid var(--gold)',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              }}
            />
          ) : (
            <div
              style={{
                width: 72,
                height: 72,
                borderRadius: '50%',
                background: 'var(--gold)',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 26,
                fontWeight: 700,
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              }}
            >
              {getInitials(profile?.full_name || profile?.username)}
            </div>
          )}
        </div>
        <div>
          <h2 style={{ margin: 0, fontSize: 20 }}>{profile?.full_name || profile?.username}</h2>
          <p style={{ margin: '4px 0 0', color: 'var(--ink-soft)', fontSize: 14 }}>
            @{profile?.username} • {profile?.email || 'No email registered'}
          </p>
          <span className="tag" style={{ marginTop: 8, display: 'inline-block' }}>
            Currency: {profile?.currency === 'INR' ? '₹ (INR)' : profile?.currency || 'INR'}
          </span>
        </div>
      </div>

      {/* Edit Information Form */}
      <div className="card" style={{ padding: 24 }}>
        <h3 style={{ marginTop: 0, marginBottom: 18, fontSize: 16 }}>Edit Personal Information & Photo</h3>
        <form onSubmit={handleSubmit}>
          
          {/* Profile Photo Upload Section */}
          <div style={{ marginBottom: 24, background: '#f8fafc', padding: 16, borderRadius: 10, border: '1px dashed #cbd5e1' }}>
            <label style={{ display: 'block', fontWeight: 600, fontSize: 14, marginBottom: 8 }}>📷 Profile Photo</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                id="photo-upload-input"
                style={{ display: 'none' }}
              />
              <label
                htmlFor="photo-upload-input"
                style={{
                  background: '#6366f1',
                  color: '#ffffff',
                  padding: '8px 16px',
                  borderRadius: 6,
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'inline-block',
                }}
              >
                Upload Photo 📤
              </label>

              {avatar && (
                <button
                  type="button"
                  onClick={() => setAvatar('')}
                  style={{
                    background: 'transparent',
                    border: '1px solid #ef4444',
                    color: '#ef4444',
                    padding: '7px 14px',
                    borderRadius: 6,
                    fontSize: 13,
                    cursor: 'pointer',
                    fontWeight: 600,
                  }}
                >
                  Remove Photo 🗑️
                </button>
              )}
            </div>
            
            {/* Optional URL input */}
            <div style={{ marginTop: 12 }}>
              <span style={{ fontSize: 12, color: '#64748b' }}>Or paste an image URL:</span>
              <input
                type="url"
                value={avatar.startsWith('data:') ? '' : avatar}
                onChange={(e) => setAvatar(e.target.value)}
                placeholder="https://example.com/my-photo.jpg"
                style={{ width: '100%', marginTop: 4, padding: '8px 12px', fontSize: 13, borderRadius: 6, border: '1px solid var(--line)' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <div className="field">
              <label>Username</label>
              <input value={profile?.username || ''} disabled style={{ opacity: 0.7, cursor: 'not-allowed' }} />
            </div>
            <div className="field">
              <label>Registered Notification Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your.email@example.com"
                required
              />
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
            {saving ? 'Saving...' : '💾 Save Profile & Photo'}
          </button>
        </form>
      </div>
    </div>
  )
}
