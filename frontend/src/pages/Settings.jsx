import { useState, useEffect } from 'react'
import api from '../api'
import { useAuth } from '../AuthContext'

export default function Settings() {
  const { profile } = useAuth()
  const [activeTab, setActiveTab] = useState('notifications')
  const [testSending, setTestSending] = useState(false)
  const [testMsg, setTestMsg] = useState('')
  
  // Settings State (loaded from localStorage or defaults)
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('budgetbuddy_settings')
    if (saved) {
      try {
        return JSON.parse(saved)
      } catch (e) {}
    }
    return {
      notifications_enabled: true,
      budget_alerts: true,
      expense_alerts: true,
      savings_alerts: true,
      email_alerts: true,
      sound_alerts: true,
      currency: '₹',
      date_format: 'DD/MM/YYYY',
      ai_style: 'balanced',
      ai_auto_save: false,
      export_format: 'PDF',
    }
  })

  const [saveMessage, setSaveMessage] = useState('')
  
  // Password Change State
  const [passForm, setPassForm] = useState({ old_password: '', new_password: '', confirm_password: '' })
  const [passMsg, setPassMsg] = useState({ text: '', type: '' })
  const [passLoading, setPassLoading] = useState(false)

  // Calculator State
  const [calcDisplay, setCalcDisplay] = useState('0')
  const [calcFormula, setCalcFormula] = useState('')
  const [calcHistory, setCalcHistory] = useState([])
  const [calcSplitResult, setCalcSplitResult] = useState(null)

  useEffect(() => {
    localStorage.setItem('budgetbuddy_settings', JSON.stringify(settings))
  }, [settings])

  const handleToggle = (key) => {
    setSettings((prev) => {
      const updated = { ...prev, [key]: !prev[key] }
      return updated
    })
    triggerSaveMsg('Settings updated successfully!')
  }

  const handleChange = (key, val) => {
    setSettings((prev) => ({ ...prev, [key]: val }))
    triggerSaveMsg('Preference saved!')
  }

  const triggerSaveMsg = (msg) => {
    setSaveMessage(msg)
    setTimeout(() => setSaveMessage(''), 2500)
  }

  // Handle Password Submit
  const handlePasswordChange = async (e) => {
    e.preventDefault()
    setPassMsg({ text: '', type: '' })

    if (passForm.new_password !== passForm.confirm_password) {
      setPassMsg({ text: 'New password and confirmation do not match.', type: 'error' })
      return
    }
    if (passForm.new_password.length < 6) {
      setPassMsg({ text: 'Password must be at least 6 characters long.', type: 'error' })
      return
    }

    setPassLoading(true)
    try {
      await api.post('/api/auth/change-password/', {
        old_password: passForm.old_password,
        new_password: passForm.new_password,
      })
      setPassMsg({ text: 'Password changed successfully! ✅', type: 'success' })
      setPassForm({ old_password: '', new_password: '', confirm_password: '' })
    } catch (err) {
      const detail = err?.response?.data?.detail || err?.response?.data?.error || 'Failed to change password. Check your current password.'
      setPassMsg({ text: detail, type: 'error' })
    } finally {
      setPassLoading(false)
    }
  }

  // Calculator Logic
  const handleCalcDigit = (digit) => {
    setCalcSplitResult(null)
    if (calcDisplay === '0' || calcDisplay === 'Error') {
      setCalcDisplay(digit)
    } else {
      setCalcDisplay((prev) => prev + digit)
    }
  }

  const handleCalcOperator = (op) => {
    setCalcSplitResult(null)
    setCalcFormula((prev) => calcDisplay + ' ' + op + ' ')
    setCalcDisplay('0')
  }

  const handleCalcClear = () => {
    setCalcDisplay('0')
    setCalcFormula('')
    setCalcSplitResult(null)
  }

  const handleCalcBackspace = () => {
    if (calcDisplay.length > 1) {
      setCalcDisplay(calcDisplay.slice(0, -1))
    } else {
      setCalcDisplay('0')
    }
  }

  const handleCalcEqual = () => {
    try {
      const fullExpression = (calcFormula + calcDisplay).replace(/×/g, '*').replace(/÷/g, '/')
      // Safe math evaluation
      const safeEval = (fn) => new Function(`'use strict'; return (${fn})`)()
      const result = safeEval(fullExpression)
      const formatted = Number.isInteger(result) ? String(result) : String(parseFloat(result.toFixed(2)))
      
      setCalcHistory((prev) => [
        { expr: calcFormula + calcDisplay, res: formatted, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) },
        ...prev.slice(0, 9)
      ])
      setCalcFormula('')
      setCalcDisplay(formatted)
    } catch (e) {
      setCalcDisplay('Error')
    }
  }

  // Calculator Financial Helper Presets
  const handleApplyGST = (ratePct) => {
    const num = parseFloat(calcDisplay) || 0
    const tax = num * (ratePct / 100)
    const total = num + tax
    setCalcFormula(`${num} + ${ratePct}% Tax = `)
    setCalcDisplay(String(total.toFixed(2)))
  }

  const handle503020Rule = () => {
    const total = parseFloat(calcDisplay) || 0
    if (total <= 0) return
    const needs = total * 0.50
    const wants = total * 0.30
    const savings = total * 0.20

    setCalcSplitResult({
      total,
      needs: needs.toFixed(2),
      wants: wants.toFixed(2),
      savings: savings.toFixed(2)
    })
  }

  const handleMonthlyToYearly = () => {
    const num = parseFloat(calcDisplay) || 0
    const yearly = num * 12
    setCalcFormula(`${num}/mo × 12 = `)
    setCalcDisplay(String(yearly.toFixed(2)))
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: 'var(--ink)' }}>⚙️ Preferences & Settings</h1>
          <p style={{ color: '#64748b', fontSize: 14, marginTop: 4, margin: 0 }}>
            Manage notification alerts, use the financial calculator, and customize your BudgetBuddy experience.
          </p>
        </div>
        {saveMessage && (
          <div className="save-toast-banner" style={{ background: '#10b981', color: '#fff', padding: '6px 16px', borderRadius: 20, fontSize: 13, fontWeight: 600 }}>
            {saveMessage}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid var(--line)', marginBottom: 24, flexWrap: 'wrap' }}>
        {[
          { id: 'notifications', label: '🔔 Notifications', desc: 'Alerts & Email Toggles' },
          { id: 'calculator', label: '🧮 Financial Calculator', desc: 'Built-in Math & 50/30/20' },
          { id: 'appearance', label: '🎨 Regional & Currency', desc: 'Currency & Format' },
          { id: 'ai_settings', label: '🤖 AI Companion', desc: 'Smart Assistant Tuning' },
          { id: 'security', label: '🔒 Password & Security', desc: 'Account Protection' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '10px 18px',
              borderRadius: '8px 8px 0 0',
              border: 'none',
              borderBottom: activeTab === tab.id ? '3px solid #6366f1' : '3px solid transparent',
              background: activeTab === tab.id ? 'var(--bg-card)' : 'transparent',
              color: activeTab === tab.id ? '#6366f1' : 'var(--ink-soft)',
              fontWeight: activeTab === tab.id ? 700 : 500,
              fontSize: 14,
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: NOTIFICATIONS */}
      {activeTab === 'notifications' && (
        <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 12, border: '1px solid var(--line)' }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>🔔 Notification Controls</h2>
          <p style={{ fontSize: 13.5, color: '#64748b', marginBottom: 20 }}>
            Choose which alerts you want to receive in the top header bell menu and via email.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Master Toggle */}
            <div className="setting-toggle-row" style={{ background: '#f8fafc', padding: 16, borderRadius: 8, border: '1px solid #e2e8f0' }}>
              <div>
                <strong style={{ fontSize: 15, color: '#0f172a' }}>Allow In-App Notifications</strong>
                <div style={{ fontSize: 12.5, color: '#64748b', marginTop: 2 }}>Master control to enable or silence all notification alerts in the top bell icon.</div>
              </div>
              <label className="switch">
                <input
                  type="checkbox"
                  checked={settings.notifications_enabled}
                  onChange={() => handleToggle('notifications_enabled')}
                />
                <span className="slider round"></span>
              </label>
            </div>

            {/* Sub Toggles */}
            <div style={{ opacity: settings.notifications_enabled ? 1 : 0.5, pointerEvents: settings.notifications_enabled ? 'auto' : 'none', display: 'flex', flexDirection: 'column', gap: 14, paddingLeft: 8 }}>
              <div className="setting-toggle-row">
                <div>
                  <strong>⚠️ Budget Breach Warnings</strong>
                  <div style={{ fontSize: 12, color: '#64748b' }}>Get instant alerts when your monthly category spending exceeds set limits.</div>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={settings.budget_alerts}
                    onChange={() => handleToggle('budget_alerts')}
                  />
                  <span className="slider round"></span>
                </label>
              </div>

              <div className="setting-toggle-row">
                <div>
                  <strong>💸 Expense Addition Confirmations</strong>
                  <div style={{ fontSize: 12, color: '#64748b' }}>Receive confirmation logs when expenses are recorded.</div>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={settings.expense_alerts}
                    onChange={() => handleToggle('expense_alerts')}
                  />
                  <span className="slider round"></span>
                </label>
              </div>

              <div className="setting-toggle-row">
                <div>
                  <strong>🎯 Savings Goal Milestones</strong>
                  <div style={{ fontSize: 12, color: '#64748b' }}>Celebrate progress alerts when you reach target savings thresholds.</div>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={settings.savings_alerts}
                    onChange={() => handleToggle('savings_alerts')}
                  />
                  <span className="slider round"></span>
                </label>
              </div>

              <div className="setting-toggle-row">
                <div>
                  <strong>📧 Google Account Email Notifications</strong>
                  <div style={{ fontSize: 12, color: '#64748b' }}>
                    Real-time notifications sent to <strong>{profile?.email || 'your Google Account email'}</strong> for mobile alerts.
                  </div>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={settings.email_alerts}
                    onChange={() => handleToggle('email_alerts')}
                  />
                  <span className="slider round"></span>
                </label>
              </div>

              {/* Test Google Account Notification Section */}
              <div style={{
                marginTop: 16,
                padding: 16,
                background: '#f0fdf4',
                border: '1px solid #bbf7d0',
                borderRadius: 8,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: 12
              }}>
                <div>
                  <strong style={{ color: '#166534', fontSize: 14 }}>📱 Test Real-Time Mobile Email Delivery</strong>
                  <div style={{ fontSize: 12.5, color: '#15803d', marginTop: 2 }}>
                    Trigger a test alert to verify Brevo SMTP & Google Account inbox notification delivery.
                  </div>
                </div>
                <button
                  type="button"
                  onClick={async () => {
                    setTestSending(true)
                    setTestMsg('')
                    try {
                      const { data } = await api.post('/api/notifications/test-email/')
                      setTestMsg(data?.detail || 'Test email dispatched!')
                    } catch (e) {
                      setTestMsg(e?.response?.data?.detail || 'Failed to send test email.')
                    } finally {
                      setTestSending(false)
                    }
                  }}
                  disabled={testSending}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 6,
                    border: 'none',
                    background: '#16a34a',
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: 13,
                    cursor: testSending ? 'wait' : 'pointer'
                  }}
                >
                  {testSending ? 'Sending...' : '✉️ Send Test Notification'}
                </button>
              </div>
              {testMsg && (
                <div style={{ fontSize: 13, fontWeight: 500, color: testMsg.includes('Failed') ? '#dc2626' : '#15803d', marginTop: 8 }}>
                  {testMsg}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: FINANCIAL CALCULATOR */}
      {activeTab === 'calculator' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 24 }}>
          {/* Main Calculator Widget */}
          <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 12, border: '1px solid var(--line)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>🧮 Interactive Financial Calculator</h2>
              <span style={{ fontSize: 12, color: '#6366f1', fontWeight: 600 }}>Quick Math & Tax Helper</span>
            </div>

            {/* Calc Display Screen */}
            <div className="calc-screen">
              <div className="calc-formula">{calcFormula || ' '}</div>
              <div className="calc-main-display">{calcDisplay}</div>
            </div>

            {/* Quick Financial Presets */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 16 }}>
              <button className="calc-preset-btn" onClick={() => handleApplyGST(18)}>+18% GST</button>
              <button className="calc-preset-btn" onClick={() => handleApplyGST(5)}>+5% Tax</button>
              <button className="calc-preset-btn" onClick={handleMonthlyToYearly}>Monthly×12</button>
              <button className="calc-preset-btn highlight" onClick={handle503020Rule}>50/30/20 Rule</button>
            </div>

            {/* 50/30/20 Breakdown Result */}
            {calcSplitResult && (
              <div className="calc-rule-card">
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6, color: '#4f46e5' }}>
                  📊 50/30/20 Budget Breakdown for {settings.currency}{calcSplitResult.total}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, fontSize: 12 }}>
                  <div style={{ background: '#e0e7ff', padding: 8, borderRadius: 6 }}>
                    <strong>🏠 50% Needs</strong>
                    <div>{settings.currency}{calcSplitResult.needs}</div>
                  </div>
                  <div style={{ background: '#fef3c7', padding: 8, borderRadius: 6 }}>
                    <strong>🎬 30% Wants</strong>
                    <div>{settings.currency}{calcSplitResult.wants}</div>
                  </div>
                  <div style={{ background: '#d1fae5', padding: 8, borderRadius: 6 }}>
                    <strong>🏦 20% Savings</strong>
                    <div>{settings.currency}{calcSplitResult.savings}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Keypad Buttons */}
            <div className="calc-grid">
              <button className="calc-key op" onClick={handleCalcClear}>C</button>
              <button className="calc-key op" onClick={handleCalcBackspace}>⌫</button>
              <button className="calc-key op" onClick={() => handleCalcOperator('%')}>%</button>
              <button className="calc-key op" onClick={() => handleCalcOperator('÷')}>÷</button>

              <button className="calc-key" onClick={() => handleCalcDigit('7')}>7</button>
              <button className="calc-key" onClick={() => handleCalcDigit('8')}>8</button>
              <button className="calc-key" onClick={() => handleCalcDigit('9')}>9</button>
              <button className="calc-key op" onClick={() => handleCalcOperator('×')}>×</button>

              <button className="calc-key" onClick={() => handleCalcDigit('4')}>4</button>
              <button className="calc-key" onClick={() => handleCalcDigit('5')}>5</button>
              <button className="calc-key" onClick={() => handleCalcDigit('6')}>6</button>
              <button className="calc-key op" onClick={() => handleCalcOperator('-')}>-</button>

              <button className="calc-key" onClick={() => handleCalcDigit('1')}>1</button>
              <button className="calc-key" onClick={() => handleCalcDigit('2')}>2</button>
              <button className="calc-key" onClick={() => handleCalcDigit('3')}>3</button>
              <button className="calc-key op" onClick={() => handleCalcOperator('+')}>+</button>

              <button className="calc-key zero" onClick={() => handleCalcDigit('0')}>0</button>
              <button className="calc-key" onClick={() => handleCalcDigit('.')}>.</button>
              <button className="calc-key equals" onClick={handleCalcEqual}>=</button>
            </div>
          </div>

          {/* History Sidebar */}
          <div style={{ background: 'var(--bg-card)', padding: 20, borderRadius: 12, border: '1px solid var(--line)', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>📜 Calculation Log</h3>
              {calcHistory.length > 0 && (
                <button
                  onClick={() => setCalcHistory([])}
                  style={{ background: 'none', border: 'none', color: '#ef4444', fontSize: 11.5, cursor: 'pointer', fontWeight: 600 }}
                >
                  Clear Log
                </button>
              )}
            </div>

            {calcHistory.length === 0 ? (
              <div style={{ color: '#94a3b8', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
                No recent calculations yet. Use the keypad to compute totals!
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, overflowY: 'auto', maxHeight: 380 }}>
                {calcHistory.map((h, i) => (
                  <div
                    key={i}
                    onClick={() => setCalcDisplay(h.res)}
                    style={{ background: '#f8fafc', padding: '8px 12px', borderRadius: 6, cursor: 'pointer', border: '1px solid #e2e8f0' }}
                    title="Click to copy result into calculator"
                  >
                    <div style={{ fontSize: 11, color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
                      <span>{h.expr}</span>
                      <span>{h.time}</span>
                    </div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: '#0f172a', textAlign: 'right' }}>
                      = {settings.currency}{h.res}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: REGIONAL & APPEARANCE */}
      {activeTab === 'appearance' && (
        <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 12, border: '1px solid var(--line)' }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>🎨 Regional & Display Preferences</h2>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13.5, fontWeight: 600, marginBottom: 6 }}>
                Preferred Currency Symbol
              </label>
              <select
                value={settings.currency}
                onChange={(e) => handleChange('currency', e.target.value)}
                style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--line)' }}
              >
                <option value="₹">₹ (INR - Indian Rupee)</option>
                <option value="$">$ (USD - US Dollar)</option>
                <option value="€">€ (EUR - Euro)</option>
                <option value="£">£ (GBP - British Pound)</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 13.5, fontWeight: 600, marginBottom: 6 }}>
                Date Format Display
              </label>
              <select
                value={settings.date_format}
                onChange={(e) => handleChange('date_format', e.target.value)}
                style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--line)' }}
              >
                <option value="DD/MM/YYYY">DD/MM/YYYY (e.g. 17/08/2026)</option>
                <option value="MM/DD/YYYY">MM/DD/YYYY (e.g. 08/17/2026)</option>
                <option value="YYYY-MM-DD">YYYY-MM-DD (e.g. 2026-08-17)</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: AI COMPANION SETTINGS */}
      {activeTab === 'ai_settings' && (
        <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 12, border: '1px solid var(--line)' }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>🤖 AI Assistant Preferences</h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13.5, fontWeight: 600, marginBottom: 6 }}>
                AI Advice Strictness Mode
              </label>
              <select
                value={settings.ai_style}
                onChange={(e) => handleChange('ai_style', e.target.value)}
                style={{ width: '100%', maxWidth: 400, padding: '10px 12px', borderRadius: 8, border: '1px solid var(--line)' }}
              >
                <option value="balanced">Balanced Advisor (Default)</option>
                <option value="aggressive">Aggressive Saver (Strict spending cuts)</option>
                <option value="relaxed">Relaxed / Flexible (Gentle guidance)</option>
              </select>
            </div>

            <div className="setting-toggle-row" style={{ marginTop: 8 }}>
              <div>
                <strong>⚡ Auto NLP Expense Quick-Save</strong>
                <div style={{ fontSize: 12, color: '#64748b' }}>Automatically save parsed natural language expenses without asking for confirmation.</div>
              </div>
              <label className="switch">
                <input
                  type="checkbox"
                  checked={settings.ai_auto_save}
                  onChange={() => handleToggle('ai_auto_save')}
                />
                <span className="slider round"></span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: SECURITY */}
      {activeTab === 'security' && (
        <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 12, border: '1px solid var(--line)', maxWidth: 500 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>🔒 Change Account Password</h2>

          {passMsg.text && (
            <div className={`banner ${passMsg.type === 'error' ? 'error-banner' : 'success-banner'}`} style={{ marginBottom: 16 }}>
              {passMsg.text}
            </div>
          )}

          <form onSubmit={handlePasswordChange} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 4 }}>Current Password</label>
              <input
                type="password"
                required
                value={passForm.old_password}
                onChange={(e) => setPassForm({ ...passForm, old_password: e.target.value })}
                placeholder="Enter current password"
                style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--line)' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 4 }}>New Password</label>
              <input
                type="password"
                required
                value={passForm.new_password}
                onChange={(e) => setPassForm({ ...passForm, new_password: e.target.value })}
                placeholder="Enter new password"
                style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--line)' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 4 }}>Confirm New Password</label>
              <input
                type="password"
                required
                value={passForm.confirm_password}
                onChange={(e) => setPassForm({ ...passForm, confirm_password: e.target.value })}
                placeholder="Confirm new password"
                style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--line)' }}
              />
            </div>

            <button
              className="btn"
              type="submit"
              disabled={passLoading}
              style={{ marginTop: 8, background: '#6366f1', color: '#fff', padding: '12px 20px', fontWeight: 600 }}
            >
              {passLoading ? 'Updating Password...' : 'Update Password'}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
