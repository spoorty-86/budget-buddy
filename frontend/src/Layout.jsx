import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext'
import api from './api'

const LINKS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/expenses', label: 'Expenses' },
  { to: '/incomes', label: 'Incomes' },
  { to: '/budgets', label: 'Budgets' },
  { to: '/categories', label: 'Categories' },
  { to: '/savings', label: 'Savings Goals' },
  { to: '/notifications', label: 'Notifications' },
]

export default function Layout() {
  const { profile, ready, logout } = useAuth()
  const [unreadCount, setUnreadCount] = useState(0)
  const navigate = useNavigate()

  useEffect(() => {
    if (!ready || !profile) return
    let active = true
    api.get('/api/notifications/').then(({ data }) => {
      if (!active) return
      setUnreadCount(data.filter((item) => !item.is_read).length)
    }).catch(() => {
      setUnreadCount(0)
    })
    return () => { active = false }
  }, [profile, ready])

  function handleLogout() {
    logout()
    navigate('/login')
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
              {link.label}
              {link.to === '/notifications' && unreadCount > 0 && (
                <span className="badge">{unreadCount}</span>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="nav-footer">
          <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, marginBottom: 10 }}>
            {profile?.full_name || profile?.username}
          </p>
          <button className="logout-btn" onClick={handleLogout}>Log out</button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
