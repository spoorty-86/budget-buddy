import { useEffect, useState } from 'react'
import api from '../api'
import { useAuth } from '../AuthContext'

export default function Notifications() {
  const { profile } = useAuth()
  const [items, setItems] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [testSuccess, setTestSuccess] = useState('')
  const [testSending, setTestSending] = useState(false)
  const [pushStatus, setPushStatus] = useState(() => {
    return typeof Notification !== 'undefined' ? Notification.permission : 'unsupported'
  })

  const loadNotifications = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get('/api/notifications/')
      setItems(data)
    } catch (err) {
      const status = err?.response?.status
      if (status === 401) {
        setError('Please log in to view notifications.')
      } else {
        setError('Unable to load notifications. Please refresh.')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadNotifications()
  }, [])

  const handleSendTestEmail = async () => {
    setTestSending(true)
    setTestSuccess('')
    setError('')
    try {
      const { data } = await api.post('/api/notifications/test-email/')
      setTestSuccess(data?.detail || 'Test notification sent to your Google Account email!')
      await loadNotifications()
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Unable to send test notification email.'
      setError(msg)
    } finally {
      setTestSending(false)
    }
  }

  const handleRequestPushPermission = async () => {
    if (typeof Notification === 'undefined') {
      alert('Browser Push Notifications are not supported by this browser.')
      return
    }
    const perm = await Notification.requestPermission()
    setPushStatus(perm)
    if (perm === 'granted') {
      new Notification('BudgetBuddy Push Enabled 🔔', {
        body: 'Mobile and browser push notifications are active for your account!',
        icon: '/favicon.ico'
      })
    }
  }

  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  const toggleSelectAll = () => {
    if (selectedIds.length === items.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(items.map((i) => i.id))
    }
  }

  const togglePin = async (id) => {
    try {
      const { data } = await api.post(`/api/notifications/${id}/toggle-pin/`)
      setItems((prev) =>
        prev
          .map((item) => (item.id === id ? data : item))
          .sort((a, b) => (b.is_pinned ? 1 : 0) - (a.is_pinned ? 1 : 0))
      )
    } catch (err) {
      setError('Unable to pin/unpin notification.')
    }
  }

  const markRead = async (id) => {
    try {
      const { data } = await api.post(`/api/notifications/${id}/mark-read/`)
      setItems((prev) => prev.map((item) => (item.id === id ? data : item)))
    } catch (err) {
      setError('Unable to mark notification as read. Please try again.')
    }
  }

  const removeNotification = async (id) => {
    try {
      await api.delete(`/api/notifications/${id}/`)
      setItems((prev) => prev.filter((item) => item.id !== id))
      setSelectedIds((prev) => prev.filter((i) => i !== id))
    } catch (err) {
      setError('Unable to delete notification. Please try again.')
    }
  }

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return
    if (!window.confirm(`Delete ${selectedIds.length} selected notification(s)?`)) return

    try {
      await api.post('/api/notifications/bulk-delete/', { ids: selectedIds })
      setItems((prev) => prev.filter((item) => !selectedIds.includes(item.id)))
      setSelectedIds([])
    } catch (err) {
      setError('Failed to delete selected notifications.')
    }
  }

  const handleBulkPin = async (shouldPin) => {
    if (selectedIds.length === 0) return
    try {
      await api.post('/api/notifications/bulk-pin/', { ids: selectedIds, pin: shouldPin })
      setItems((prev) =>
        prev
          .map((item) => (selectedIds.includes(item.id) ? { ...item, is_pinned: shouldPin } : item))
          .sort((a, b) => (b.is_pinned ? 1 : 0) - (a.is_pinned ? 1 : 0))
      )
      setSelectedIds([])
    } catch (err) {
      setError('Failed to update pin state.')
    }
  }

  const clearAllNotifications = async () => {
    if (!window.confirm('Are you sure you want to delete all notifications?')) return
    try {
      await Promise.all(items.map((item) => api.delete(`/api/notifications/${item.id}/`)))
      setItems([])
      setSelectedIds([])
    } catch (err) {
      setError('Unable to clear notifications. Please try again.')
    }
  }

  const allSelected = items.length > 0 && selectedIds.length === items.length

  return (
    <>
      <div className="page-header" style={{ marginBottom: 20 }}>
        <div>
          <h1>Notifications</h1>
          <p className="page-sub">Select, pin to top, or delete any notifications you don't need.</p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          {selectedIds.length > 0 && (
            <>
              <button
                className="btn secondary"
                onClick={() => handleBulkPin(true)}
                style={{ fontSize: 13 }}
              >
                📌 Pin Selected ({selectedIds.length})
              </button>
              <button
                className="btn secondary"
                onClick={() => handleBulkPin(false)}
                style={{ fontSize: 13 }}
              >
                📍 Unpin Selected
              </button>
              <button
                className="btn secondary"
                onClick={handleBulkDelete}
                style={{ color: 'var(--red)', borderColor: 'var(--red-soft)', fontSize: 13 }}
              >
                🗑️ Delete Selected ({selectedIds.length})
              </button>
            </>
          )}
          {items.length > 0 && (
            <button
              className="btn secondary"
              onClick={clearAllNotifications}
              style={{ color: 'var(--red)', borderColor: 'var(--red-soft)', fontSize: 13 }}
            >
              Clear All
            </button>
          )}
        </div>
      </div>

      {/* Google Account Email & Mobile Notification Status Card */}
      <div className="card" style={{
        marginBottom: 20,
        padding: 20,
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%)',
        border: '1px solid rgba(16, 185, 129, 0.2)',
        borderRadius: 12,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <span style={{ fontSize: 20 }}>📱</span>
              <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
                Real-Time Email Notifications
              </h2>
              <span className="tag" style={{ background: '#10b981', color: '#fff', fontSize: 11 }}>Active</span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--ink-soft)', margin: 0 }}>
              All app alerts (budget breaches, expenses, income logs, and AI tips) are sent directly to <strong>{profile?.email || 'your registered email'}</strong>.
            </p>
          </div>

          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button
              className="btn"
              onClick={handleSendTestEmail}
              disabled={testSending}
              style={{
                fontSize: 13,
                background: '#10b981',
                color: '#fff',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}
            >
              {testSending ? 'Sending Test…' : '✉️ Send Test Email'}
            </button>




            {pushStatus !== 'granted' && (
              <button
                className="btn secondary"
                onClick={handleRequestPushPermission}
                style={{ fontSize: 13 }}
                title="Enable browser push popups on phone/desktop"
              >
                🔔 Enable Mobile Push Popups
              </button>
            )}
          </div>
        </div>
      </div>

      {testSuccess && (
        <div className="banner success-banner" style={{ marginBottom: 16, background: '#d1fae5', color: '#065f46', padding: '10px 14px', borderRadius: 8, fontSize: 13.5 }}>
          ✅ {testSuccess}
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}

      <div className="card">
        {loading && <p className="empty-state">Loading…</p>}
        {!loading && items.length === 0 && <p className="empty-state">No notifications yet.</p>}
        {!loading && items.length > 0 && (
          <table className="ledger">
            <thead>
              <tr>
                <th style={{ width: 36, textAlign: 'center' }}>
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleSelectAll}
                    style={{ cursor: 'pointer' }}
                  />
                </th>
                <th>Title</th>
                <th>Message</th>
                <th>Type</th>
                <th>Priority</th>
                <th>Date</th>
                <th>Status</th>
                <th className="num">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const isSelected = selectedIds.includes(item.id)
                return (
                  <tr
                    key={item.id}
                    className={item.is_read ? 'row-read' : 'row-unread'}
                    style={{
                      backgroundColor: isSelected ? 'rgba(23, 121, 91, 0.08)' : item.is_pinned ? 'var(--gold-soft)' : undefined,
                      borderLeft: item.is_pinned ? '4px solid var(--gold)' : undefined,
                    }}
                  >
                    <td style={{ textAlign: 'center' }}>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelect(item.id)}
                        style={{ cursor: 'pointer' }}
                      />
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        {item.is_pinned && <span title="Pinned to top">📌</span>}
                        <strong>{item.title}</strong>
                      </div>
                    </td>
                    <td>{item.message}</td>
                    <td><span className="tag">{item.notification_type}</span></td>
                    <td>{item.priority}</td>
                    <td style={{ fontSize: 13, color: 'var(--ink-soft)' }}>{new Date(item.created_at).toLocaleString()}</td>
                    <td>
                      {item.is_pinned && <span className="tag" style={{ background: 'var(--gold)', color: '#fff', marginRight: 4 }}>Pinned</span>}
                      {item.is_read ? 'Read' : 'Unread'}
                    </td>
                    <td className="num" style={{ whiteSpace: 'nowrap' }}>
                      <button
                        className="btn secondary"
                        style={{ marginRight: 6, padding: '4px 8px', fontSize: 12.5 }}
                        onClick={() => togglePin(item.id)}
                        title={item.is_pinned ? 'Unpin notification' : 'Pin notification to top'}
                      >
                        {item.is_pinned ? '📍 Unpin' : '📌 Pin'}
                      </button>
                      {!item.is_read && (
                        <button
                          className="btn secondary"
                          style={{ marginRight: 6, padding: '4px 8px', fontSize: 12.5 }}
                          onClick={() => markRead(item.id)}
                        >
                          Mark read
                        </button>
                      )}
                      <button
                        className="btn secondary"
                        style={{ padding: '4px 8px', fontSize: 12.5, color: 'var(--red)', borderColor: 'var(--red-soft)' }}
                        onClick={() => removeNotification(item.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
