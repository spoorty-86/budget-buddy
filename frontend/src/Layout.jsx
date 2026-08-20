import { useEffect, useState, useRef } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext'
import api from './api'

const LINKS = [
  { to: '/', label: 'Dashboard', icon: '📊', end: true },
  { to: '/landing', label: 'Welcome Page', icon: '✨' },
  { to: '/ai-portal', label: 'AI Portal', icon: '🤖', badge: 'AI' },
  { to: '/expenses', label: 'Expenses', icon: '💸' },
  { to: '/incomes', label: 'Incomes', icon: '💰' },
  { to: '/budgets', label: 'Budgets', icon: '🎯' },
  { to: '/categories', label: 'Categories', icon: '🏷️' },
  { to: '/savings', label: 'Savings Goals', icon: '🏦' },
  { to: '/reports', label: 'Reports & Export', icon: '📑' },
  { to: '/profile', label: 'Profile', icon: '👤' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
]

export default function Layout() {
  const { profile, ready, logout } = useAuth()
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [showNotifDropdown, setShowNotifDropdown] = useState(false)
  const notifRef = useRef(null)
  const navigate = useNavigate()

  const fetchNotifications = () => {
    if (!ready || !profile) return
    const saved = localStorage.getItem('budgetbuddy_settings')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        if (parsed.notifications_enabled === false) {
          setNotifications([])
          setUnreadCount(0)
          return
        }
      } catch (e) {}
    }
    api.get('/api/notifications/')
      .then(({ data }) => {
        const list = Array.isArray(data) ? data : (data?.results || [])
        setNotifications(list)
        setUnreadCount(list.filter((item) => item && !item.is_read).length)
      })
      .catch(() => {
        setNotifications([])
        setUnreadCount(0)
      })
  }

  useEffect(() => {
    fetchNotifications()
    const interval = setInterval(fetchNotifications, 5000)
    return () => clearInterval(interval)
  }, [profile, ready])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setShowNotifDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const handleMarkSingleRead = async (id) => {
    try {
      await api.patch(`/api/notifications/${id}/mark-read/`)
      fetchNotifications()
    } catch (e) {
      console.error(e)
    }
  }

  const handleMarkAllRead = async () => {
    const list = Array.isArray(notifications) ? notifications : []
    const unread = list.filter((n) => n && !n.is_read)
    for (const n of unread) {
      try {
        await api.patch(`/api/notifications/${n.id}/mark-read/`)
      } catch (e) {}
    }
    fetchNotifications()
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

  const getPriorityClass = (pri) => {
    if (typeof pri === 'string') return pri.toLowerCase()
    if (typeof pri === 'number') {
      if (pri >= 3) return 'high'
      if (pri === 2) return 'warning'
      return 'info'
    }
    return 'info'
  }

  const notifListSafe = Array.isArray(notifications) ? notifications : []

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">Budget<span>Buddy</span></div>
        <nav>
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
            >
              <span style={{ fontSize: 16, width: 20, textAlign: 'center', display: 'inline-block' }}>{link.icon}</span>
              <span style={{ flex: 1 }}>{link.label}</span>
              {link.to === '/notifications' && unreadCount > 0 && (
                <span className="badge" style={{ marginLeft: 6 }}>{unreadCount}</span>
              )}
              {link.badge && (
                <span className="badge-ai-glow" style={{ marginLeft: 6 }}>{link.badge}</span>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="nav-footer">
          <NavLink
            to="/profile"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              color: '#fff',
              textDecoration: 'none',
              marginBottom: 12,
              padding: '6px 8px',
              borderRadius: 6,
              background: 'rgba(255,255,255,0.06)',
            }}
          >
            {profile?.avatar ? (
              <img
                src={profile.avatar}
                alt="Profile"
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: '1px solid var(--gold)',
                }}
              />
            ) : (
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  background: 'var(--gold)',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 13,
                  fontWeight: 700,
                }}
              >
                {getInitials(profile?.full_name || profile?.username)}
              </div>
            )}
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <div style={{ fontSize: 13.5, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {profile?.full_name || profile?.username}
              </div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)' }}>View Profile</div>
            </div>
          </NavLink>
          <button className="logout-btn" onClick={handleLogout}>Log out</button>
        </div>
      </aside>

      <main className="main">
        {/* Top Header Navigation Bar */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            gap: 16,
            marginBottom: 20,
            paddingBottom: 12,
            borderBottom: '1px solid var(--line)',
            position: 'relative',
          }}
        >
          {/* Notification Bell Dropdown Button */}
          <div ref={notifRef} style={{ position: 'relative' }}>
            <button
              onClick={() => setShowNotifDropdown(!showNotifDropdown)}
              className="notif-bell-btn"
              title="Notifications"
            >
              <span style={{ fontSize: 18 }}>🔔</span>
              {unreadCount > 0 && (
                <span className="notif-bell-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
              )}
            </button>

            {/* Notification Dropdown Flyout Card */}
            {showNotifDropdown && (
              <div className="notif-flyout-card">
                <div className="notif-flyout-header">
                  <div style={{ fontWeight: 700, fontSize: 14, color: '#0f172a' }}>
                    Notifications {unreadCount > 0 && <span style={{ fontSize: 12, color: '#6366f1', marginLeft: 4 }}>({unreadCount} new)</span>}
                  </div>
                  {unreadCount > 0 && (
                    <button className="notif-mark-all-btn" onClick={handleMarkAllRead}>
                      Mark all read
                    </button>
                  )}
                </div>

                <div className="notif-flyout-list">
                  {notifListSafe.length === 0 ? (
                    <div className="notif-empty-state">No notifications available</div>
                  ) : (
                    notifListSafe.slice(0, 6).map((n) => (
                      <div
                        key={n.id}
                        className={`notif-flyout-item ${!n.is_read ? 'unread' : ''}`}
                        onClick={() => handleMarkSingleRead(n.id)}
                      >
                        <div className="notif-item-title-row">
                          <span className={`priority-dot priority-${getPriorityClass(n.priority)}`} />
                          <strong className="notif-item-title">{n.title}</strong>
                          {!n.is_read && <span className="unread-dot" />}
                        </div>
                        <div className="notif-item-msg">{n.message}</div>
                        <div className="notif-item-time">
                          {n.created_at ? new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <div className="notif-flyout-footer">
                  <NavLink
                    to="/notifications"
                    onClick={() => setShowNotifDropdown(false)}
                    style={{ color: '#6366f1', textDecoration: 'none', fontWeight: 600, fontSize: 13 }}
                  >
                    View all notifications →
                  </NavLink>
                </div>
              </div>
            )}
          </div>

          {/* Profile Header Badge */}
          <NavLink
            to="/profile"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '6px 14px',
              borderRadius: 20,
              background: 'var(--bg-card)',
              border: '1px solid var(--line)',
              color: 'var(--ink)',
              textDecoration: 'none',
              fontSize: 13.5,
              fontWeight: 500,
              boxShadow: '0 2px 4px rgba(0,0,0,0.04)',
              transition: 'transform 0.15s, boxShadow 0.15s',
            }}
          >
            {profile?.avatar ? (
              <img
                src={profile.avatar}
                alt="Profile"
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: '1px solid var(--gold)',
                }}
              />
            ) : (
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: '50%',
                  background: 'var(--gold)',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 12,
                  fontWeight: 700,
                }}
              >
                {getInitials(profile?.full_name || profile?.username)}
              </div>
            )}
            <span>👤 <strong>{profile?.full_name || profile?.username}</strong></span>
          </NavLink>
        </div>

        <Outlet />
      </main>
    </div>
  )
}
