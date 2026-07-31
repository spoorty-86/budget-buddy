import { useEffect, useState } from 'react'
import api from '../api'

export default function Notifications() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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

  const markRead = async (id) => {
    try {
      const { data } = await api.post(`/api/notifications/${id}/mark-read/`)
      setItems((prev) => prev.map((item) => (item.id === id ? data : item)))
    } catch (err) {
      setError('Unable to mark notification as read. Please try again.')
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Notifications</h1>
          <p className="page-sub">Your latest alerts and updates.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="card">
        {loading && <p className="empty-state">Loading…</p>}
        {!loading && items.length === 0 && <p className="empty-state">No notifications yet.</p>}
        {!loading && items.length > 0 && (
          <table className="ledger">
            <thead>
              <tr>
                <th>Title</th>
                <th>Message</th>
                <th>Type</th>
                <th>Priority</th>
                <th>Date</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className={item.is_read ? 'row-read' : 'row-unread'}>
                  <td>{item.title}</td>
                  <td>{item.message}</td>
                  <td>{item.notification_type}</td>
                  <td>{item.priority}</td>
                  <td>{new Date(item.created_at).toLocaleString()}</td>
                  <td>{item.is_read ? 'Read' : 'Unread'}</td>
                  <td className="num">
                    {!item.is_read && (
                      <button className="btn secondary" onClick={() => markRead(item.id)}>
                        Mark read
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
