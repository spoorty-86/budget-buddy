import { Component, StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import { AuthProvider } from './AuthContext.jsx'
import './styles.css'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught React Error:", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#0f172a', color: '#ffffff', padding: 20, textAlign: 'center' }}>
          <h2 style={{ fontSize: 24, marginBottom: 10, fontWeight: 700 }}>Application Notice</h2>
          <p style={{ color: '#94a3b8', maxWidth: 500, marginBottom: 20, fontSize: 14 }}>
            {this.state.error?.message || 'A session or rendering mismatch occurred.'}
          </p>
          <button
            onClick={() => {
              localStorage.clear()
              window.location.href = '/login'
            }}
            style={{ background: 'linear-gradient(135deg, #4f46e5, #6366f1)', color: '#fff', border: 'none', padding: '12px 24px', borderRadius: 8, cursor: 'pointer', fontWeight: 600, fontSize: 14 }}
          >
            Reset Session & Reload Application 🔄
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </StrictMode>,
)
