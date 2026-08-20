import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import './Landing.css'

export default function Landing() {
  const [darkMode, setDarkMode] = useState(false)
  const { profile } = useAuth()

  const toggleTheme = () => {
    setDarkMode(!darkMode)
  }

  const features = [
    {
      icon: '💰',
      title: 'Income Tracking',
      description: 'Log and monitor all your income sources. See earnings growth month over month.',
      link: '/incomes'
    },
    {
      icon: '💸',
      title: 'Expense Management',
      description: 'Record daily purchases, categorize transactions, and identify saving opportunities.',
      link: '/expenses'
    },
    {
      icon: '📊',
      title: 'Smart Budgets',
      description: 'Set monthly budgets per category and receive alerts when you approach limits.',
      link: '/budgets'
    },
    {
      icon: '🎯',
      title: 'Savings Goals',
      description: 'Save for milestones like vacations or emergency funds and track your progress.',
      link: '/savings'
    },
    {
      icon: '📈',
      title: 'Reports & Analytics',
      description: 'View financial summaries with interactive charts to understand trends.',
      link: '/reports'
    },
    {
      icon: '🔔',
      title: 'Real-time Notifications',
      description: 'Get budget warnings, savings reminders, and instant update confirmations.',
      link: '/notifications'
    },
    {
      icon: '🤖',
      title: 'AI Financial Assistant',
      description: 'Receive AI-powered spending analysis, budget advice, and instant financial guidance.',
      link: '/ai-portal'
    },
    {
      icon: '🏷️',
      title: 'Custom Categories',
      description: 'Organize transactions with custom categories and visual icons tailored to your lifestyle.',
      link: '/categories'
    }
  ]

  return (
    <div className={`landing-container ${darkMode ? 'dark' : 'light'}`}>
      {/* Header */}
      <header className="landing-header">
        <Link to="/" className="landing-logo">
          <div className="logo-icon">B</div>
          <span>BudgetBuddy</span>
        </Link>
        <div className="landing-nav-actions">
          <button className="theme-toggle-btn" onClick={toggleTheme} aria-label="Toggle theme">
            {darkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
          </button>
          {profile ? (
            <Link to="/" className="btn-get-started">
              Go to Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="btn-signin">
                Sign In
              </Link>
              <Link to="/register" className="btn-get-started">
                Get Started
              </Link>
            </>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section className="landing-hero">
        <div className="hero-pill">Personal Finance Simplified</div>
        <h1 className="hero-title">
          Master Your Money, <br />
          Build Your Future.
        </h1>
        <p className="hero-subtitle">
          BudgetBuddy helps you track expenses, manage budgets, set savings goals, and visualize your financial health in one beautiful interface.
        </p>
        <div className="hero-cta-group">
          {profile ? (
            <Link to="/" className="btn-hero-primary">
              Open Dashboard
            </Link>
          ) : (
            <>
              <Link to="/register" className="btn-hero-primary">
                Start Free Trial
              </Link>
              <Link to="/login" className="btn-hero-secondary">
                Sign In
              </Link>
            </>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="landing-features-section">
        <h2 className="features-heading">Features designed to keep you on track</h2>
        <div className="features-grid">
          {features.map((item, idx) => (
            <div key={idx} className="feature-card">
              <div className="feature-icon-wrapper">{item.icon}</div>
              <h3 className="feature-card-title">{item.title}</h3>
              <p className="feature-card-desc">{item.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        © 2026 BudgetBuddy — All rights Reserved.
      </footer>
    </div>
  )
}
