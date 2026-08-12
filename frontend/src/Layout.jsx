import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext'
import api from './api'

const LINKS = [
  { to: '/', label: 'Dashboard', icon: '📊', end: true },
  { to: '/expenses', label: 'Expenses', icon: '💸' },
  { to: '/incomes', label: 'Incomes', icon: '💰' },
  { to: '/budgets', label: 'Budgets', icon: '🎯' },
  { to: '/categories', label: 'Categories', icon: '🏷️' },
  { to: '/savings', label: 'Savings Goals', icon: '🏦' },
  { to: '/notifications', label: 'Notifications', icon: '🔔' },
  { to: '/reports', label: 'Reports & Export', icon: '📑' },
  { to: '/profile', label: 'Profile', icon: '👤' },
]

export default function Layout() {
  const { profile, ready, logout } = useAuth()
  const [unreadCount, setUnreadCount] = useState(0)
  const navigate = useNavigate()

  const fetchUnread = () => {
    if (!ready || !profile) return
    api.get('/api/notifications/').then(({ data }) => {
      setUnreadCount(data.filter((item) => !item.is_read).length)
    }).catch(() => {
      setUnreadCount(0)
    })
  }

  useEffect(() => {
    fetchUnread()
    const interval = setInterval(fetchUnread, 4000)
    return () => clearInterval(interval)
  }, [profile, ready])

  function handleLogout() {
    logout()
    navigate('/login')
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
        <div
          style={{
            display: 'flex',
            justify: 'flex-end',
            alignItems: 'center',
            marginBottom: 20,
            paddingBottom: 12,
            borderBottom: '1px solid var(--line)',
          }}
        >
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
            <span>👤 <strong>{profile?.full_name || profile?.username}</strong></span>
          </NavLink>
        </div>
        <Outlet />
      </main>
    </div>
  )
}
