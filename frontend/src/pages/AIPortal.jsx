// Quick AI Logger v2.0 - Forced Cache Invalidation
import { useEffect, useState, useRef } from 'react'
import api from '../api'

export default function AIPortal() {
  const [activeTab, setActiveTab] = useState('chat') // 'chat' | 'insights' | 'nlp' | 'simulate'

  // --- 1. Chat State ---
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'ai',
      text: "Hello! I am your BudgetBuddy AI Financial Assistant. Ask me anything about your spending, budget status, or savings targets!",
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      source: 'BudgetBuddy AI'
    }
  ])
  const [inputPrompt, setInputPrompt] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)
  const [showContextDrawer, setShowContextDrawer] = useState(false)
  const [rawContext, setRawContext] = useState(null)
  const chatBottomRef = useRef(null)

  // --- 2. Insights State ---
  const [insightsData, setInsightsData] = useState(null)
  const [isInsightsLoading, setIsInsightsLoading] = useState(false)

  // --- 3. NLP Expense Logger State ---
  const [nlpText, setNlpText] = useState('')
  const [nlpResult, setNlpResult] = useState(null)
  const [isNlpLoading, setIsNlpLoading] = useState(false)
  const [saveSuccessMsg, setSaveSuccessMsg] = useState('')
  const [nlpError, setNlpError] = useState('')

  const nlpSamplePrompts = [
    "🛒 Spent ₹450 on groceries at Supermarket yesterday",
    "⛽ Paid ₹1,200 for petrol at Shell today",
    "☕ Spent ₹250 on coffee with team",
    "⚡ Paid ₹1,500 for electricity bill yesterday"
  ]

  // --- 4. What-If Simulator State ---
  const [simIncomeChange, setSimIncomeChange] = useState(0)
  const [simExpenseCut, setSimExpenseCut] = useState(10)
  const [simExtraSavings, setSimExtraSavings] = useState(500)
  const [simResults, setSimResults] = useState(null)
  const [isSimLoading, setIsSimLoading] = useState(false)

  // Fetch initial Insights & Context on load
  useEffect(() => {
    fetchInsights()
    fetchContext()
  }, [])

  useEffect(() => {
    if (activeTab === 'chat') {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, activeTab])

  const fetchInsights = async () => {
    setIsInsightsLoading(true)
    try {
      const res = await api.get('/api/ai/insights/')
      setInsightsData(res.data)
    } catch (err) {
      console.error("Failed to load AI insights:", err)
    } finally {
      setIsInsightsLoading(false)
    }
  }

  const fetchContext = async () => {
    try {
      const res = await api.get('/api/ai/context/')
      setRawContext(res.data)
    } catch (err) {
      console.error("Failed to load AI context:", err)
    }
  }

  // Handle AI Chat Submit
  const handleSendChat = async (promptToSend) => {
    const text = promptToSend || inputPrompt
    if (!text.trim() || isChatLoading) return

    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: text,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    setMessages((prev) => [...prev, userMsg])
    if (!promptToSend) setInputPrompt('')
    setIsChatLoading(true)

    try {
      const res = await api.post('/api/ai/chat/', { prompt: text })
      const aiMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: res.data.reply,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        source: res.data.source || 'BudgetBuddy AI'
      }
      setMessages((prev) => [...prev, aiMsg])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'ai',
          text: "I encountered an issue connecting to the AI engine. Please ensure your backend server is running properly.",
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isError: true
        }
      ])
    } finally {
      setIsChatLoading(false)
    }
  }

  // Quick prompt chips
  const quickPrompts = [
    "📊 Where am I spending the most?",
    "⚖️ Check my budget limits status",
    "🏦 How are my savings goals doing?",
    "💡 Give me 3 tips to cut monthly expenses",
    "🛍️ Can I afford a ₹1,000 purchase?"
  ]

  // NLP Parse Handler
  const handleNlpParse = async (autoSave = false, customText = null) => {
    let targetText = (customText !== null ? customText : nlpText).trim()
    if (!targetText) {
      targetText = "Spent ₹450 on groceries at Supermarket yesterday"
      setNlpText(targetText)
    }
    setIsNlpLoading(true)
    setSaveSuccessMsg('')
    setNlpError('')
    try {
      const res = await api.post('/api/ai/parse-expense/', { text: targetText, auto_save: autoSave })
      setNlpResult(res.data)
      if (autoSave && (res.data.created_expense || res.data.title)) {
        const savedTitle = res.data.created_expense?.title || res.data.title
        const savedAmt = res.data.created_expense?.amount || res.data.amount
        setSaveSuccessMsg(`Expense "${savedTitle}" of ₹${savedAmt} successfully added!`)
        fetchInsights() // refresh insights after saving
      }
    } catch (err) {
      console.error("NLP Parse Error:", err)
      setNlpError("Failed to parse expense with AI. Please check your text input or network connection.")
    } finally {
      setIsNlpLoading(false)
    }
  }

  // Simulation Handler
  const handleRunSimulation = async () => {
    setIsSimLoading(true)
    try {
      const res = await api.post('/api/ai/simulate/', {
        income_change: simIncomeChange,
        expense_cut_pct: simExpenseCut,
        custom_monthly_savings: simExtraSavings
      })
      setSimResults(res.data)
    } catch (err) {
      console.error("Simulation Error:", err)
    } finally {
      setIsSimLoading(false)
    }
  }

  // Trigger initial simulation when entering simulate tab if not loaded
  useEffect(() => {
    if (activeTab === 'simulate' && !simResults) {
      handleRunSimulation()
    }
  }, [activeTab])

  return (
    <div className="ai-portal-container">
      {/* Header Banner */}
      <div className="ai-header-card">
        <div className="ai-header-title-group">
          <div className="ai-badge-glowing">
            <span>✨ AI Financial Portal</span>
          </div>
          <h1>BudgetBuddy <span>AI Companion</span></h1>
          <p>Real-time financial intelligence, predictive health auditing, and natural language expense automation.</p>
        </div>
        
        {insightsData && (
          <div className="ai-header-score-pill" style={{ borderColor: insightsData.status_color }}>
            <div className="score-ring-mini" style={{ background: insightsData.status_color }}>
              {insightsData.grade}
            </div>
            <div>
              <div className="score-val">{insightsData.health_score} / 100</div>
              <div className="score-lbl" style={{ color: insightsData.status_color }}>{insightsData.status}</div>
            </div>
          </div>
        )}
      </div>

      {/* Tabs Navigation */}
      <div className="ai-tabs-nav">
        <button
          className={`ai-tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          💬 AI Assistant Chat
        </button>
        <button
          className={`ai-tab-btn ${activeTab === 'insights' ? 'active' : ''}`}
          onClick={() => setActiveTab('insights')}
        >
          📊 Health & Insights
        </button>
        <button
          className={`ai-tab-btn ${activeTab === 'nlp' ? 'active' : ''}`}
          onClick={() => setActiveTab('nlp')}
        >
          ⚡ Quick AI Logger
        </button>
        <button
          className={`ai-tab-btn ${activeTab === 'simulate' ? 'active' : ''}`}
          onClick={() => setActiveTab('simulate')}
        >
          🔮 What-If Simulator
        </button>
      </div>

      {/* TAB 1: AI CHAT */}
      {activeTab === 'chat' && (
        <div className="ai-tab-content chat-tab">
          <div className="chat-layout">
            <div className="chat-main-box">
              {/* Quick Prompts Bar */}
              <div className="quick-prompts-bar">
                {quickPrompts.map((qp, idx) => (
                  <button
                    key={idx}
                    className="prompt-chip"
                    onClick={() => handleSendChat(qp)}
                    disabled={isChatLoading}
                  >
                    {qp}
                  </button>
                ))}
              </div>

              {/* Messages Container */}
              <div className="chat-messages-scroll">
                {messages.map((msg) => (
                  <div key={msg.id} className={`chat-bubble-row ${msg.sender === 'user' ? 'user-row' : 'ai-row'}`}>
                    {msg.sender === 'ai' && <div className="chat-avatar">🤖</div>}
                    <div className={`chat-bubble ${msg.sender === 'user' ? 'user-bubble' : 'ai-bubble'} ${msg.isError ? 'error-bubble' : ''}`}>
                      <div className="bubble-text" style={{ whiteSpace: 'pre-line' }}>{msg.text}</div>
                      <div className="bubble-meta">
                        <span>{msg.time}</span>
                        {msg.source && <span className="source-tag">• {msg.source}</span>}
                      </div>
                    </div>
                    {msg.sender === 'user' && <div className="chat-avatar user-avatar">👤</div>}
                  </div>
                ))}
                {isChatLoading && (
                  <div className="chat-bubble-row ai-row">
                    <div className="chat-avatar">🤖</div>
                    <div className="chat-bubble ai-bubble typing-indicator">
                      <span></span><span></span><span></span>
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Chat Input Bar */}
              <div className="chat-input-bar">
                <input
                  type="text"
                  placeholder="Ask AI anything about your expenses, budgets, or savings..."
                  value={inputPrompt}
                  onChange={(e) => setInputPrompt(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
                  disabled={isChatLoading}
                />
                <button
                  className="chat-send-btn"
                  onClick={() => handleSendChat()}
                  disabled={isChatLoading || !inputPrompt.trim()}
                >
                  {isChatLoading ? 'Thinking...' : 'Send 🚀'}
                </button>
                <button
                  className="context-toggle-btn"
                  onClick={() => setShowContextDrawer(!showContextDrawer)}
                  title="Inspect AI Financial Context"
                >
                  🔍 Context
                </button>
              </div>
            </div>

            {/* Context Drawer Panel */}
            {showContextDrawer && rawContext && (
              <div className="context-drawer-panel">
                <h3>🔍 Live Injected AI Context</h3>
                <div className="context-metrics-list">
                  <div><strong>Income:</strong> ₹{rawContext.total_income}</div>
                  <div><strong>Expenses:</strong> ₹{rawContext.total_expense}</div>
                  <div><strong>Net Savings:</strong> ₹{rawContext.net_savings}</div>
                  <div><strong>Savings Rate:</strong> {rawContext.savings_rate}%</div>
                  <div><strong>Over Budget Categories:</strong> {rawContext.over_budget_count}</div>
                </div>
                <h4>Top Categories</h4>
                <pre>{JSON.stringify(rawContext.category_breakdown, null, 2)}</pre>
                <h4>Active Budgets</h4>
                <pre>{JSON.stringify(rawContext.budgets, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: HEALTH & INSIGHTS */}
      {activeTab === 'insights' && (
        <div className="ai-tab-content insights-tab">
          {isInsightsLoading && <div className="loading-spinner">Analyzing financial health...</div>}
          
          {insightsData && (
            <div className="insights-grid">
              {/* Score Gauge Card */}
              <div className="insights-card health-score-card">
                <h3>AI Financial Health Index</h3>
                <div className="score-ring-large" style={{ borderColor: insightsData.status_color }}>
                  <div className="score-number">{insightsData.health_score}</div>
                  <div className="score-grade" style={{ color: insightsData.status_color }}>Grade {insightsData.grade}</div>
                </div>
                <div className="health-status-badge" style={{ background: insightsData.status_color }}>
                  {insightsData.status}
                </div>
                
                <div className="health-metrics-grid">
                  <div className="metric-box">
                    <span className="lbl">Savings Rate</span>
                    <span className="val">{insightsData.metrics.savings_rate}%</span>
                  </div>
                  <div className="metric-box">
                    <span className="lbl">Net Savings</span>
                    <span className="val">₹{insightsData.metrics.net_savings.toFixed(2)}</span>
                  </div>
                  <div className="metric-box">
                    <span className="lbl">Over-Budget</span>
                    <span className="val">{insightsData.metrics.over_budget_count} Category</span>
                  </div>
                </div>
              </div>

              {/* Actionable Insights List */}
              <div className="insights-card recommendations-card">
                <h3>💡 Smart AI Recommendations</h3>
                <div className="insights-feed">
                  {insightsData.insights.map((ins, idx) => (
                    <div key={idx} className={`insight-item-box type-${ins.type}`}>
                      <div className="insight-title-row">
                        <span className="insight-badge">{ins.type.toUpperCase()}</span>
                        <strong>{ins.title}</strong>
                      </div>
                      <p className="insight-desc">{ins.description}</p>
                      <div className="insight-action-box">
                        <strong>🎯 Action Step:</strong> {ins.action}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Month-End Forecast Card */}
              <div className="insights-card forecast-card">
                <h3>🔮 Month-End Expenditure Forecast</h3>
                <div className="forecast-stats">
                  <div className="forecast-row">
                    <span>Days Elapsed:</span>
                    <strong>{insightsData.forecast.days_elapsed} days</strong>
                  </div>
                  <div className="forecast-row">
                    <span>Daily Burn Rate:</span>
                    <strong>₹{insightsData.forecast.daily_burn_rate} / day</strong>
                  </div>
                  <div className="forecast-row highlight-row">
                    <span>Projected Month-End Expense:</span>
                    <strong>₹{insightsData.forecast.projected_total_expense}</strong>
                  </div>
                  <div className="forecast-row highlight-row">
                    <span>Projected Net Balance:</span>
                    <strong style={{ color: insightsData.forecast.projected_net_savings >= 0 ? 'var(--green)' : 'var(--red)' }}>
                      ₹{insightsData.forecast.projected_net_savings}
                    </strong>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: NLP QUICK LOGGING */}
      {activeTab === 'nlp' && (
        <div className="ai-tab-content nlp-tab">
          <div className="nlp-container-card">
            <h2>⚡ Smart Natural Language Expense Logger</h2>
            <p>Type or paste any description of your expense, or click a sample below to automatically extract the amount, category, date, and title!</p>

            {/* Quick NLP Sample Chips */}
            <div className="quick-prompts-bar" style={{ marginBottom: 16 }}>
              {nlpSamplePrompts.map((sample, idx) => (
                <button
                  key={idx}
                  className="prompt-chip"
                  onClick={() => {
                    setNlpText(sample)
                    handleNlpParse(false, sample)
                  }}
                  disabled={isNlpLoading}
                >
                  {sample}
                </button>
              ))}
            </div>

            <div className="nlp-input-wrapper">
              <textarea
                rows={3}
                placeholder="Example: Spent ₹450 on groceries at Supermarket yesterday..."
                value={nlpText}
                onChange={(e) => {
                  setNlpText(e.target.value)
                  if (nlpResult) setNlpResult(null)
                  if (saveSuccessMsg) setSaveSuccessMsg('')
                  if (nlpError) setNlpError('')
                }}
              />
              <div className="nlp-btn-row">
                <button
                  className="nlp-parse-btn secondary"
                  onClick={() => handleNlpParse(false)}
                  disabled={isNlpLoading}
                >
                  {isNlpLoading ? '⏳ Analyzing with AI...' : '🔍 AI Preview Parse'}
                </button>
                <button
                  className="nlp-parse-btn primary"
                  onClick={() => handleNlpParse(true)}
                  disabled={isNlpLoading}
                >
                  {isNlpLoading ? '⏳ Saving...' : '⚡ Auto-Add to Expenses'}
                </button>
              </div>
            </div>

            {nlpError && (
              <div className="error-banner" style={{ marginTop: 12 }}>
                ⚠️ {nlpError}
              </div>
            )}

            {saveSuccessMsg && (
              <div className="toast-success-banner" style={{ marginTop: 12 }}>
                ✅ {saveSuccessMsg}
              </div>
            )}

            {nlpResult && (
              <div className="nlp-parsed-result-card" style={{ marginTop: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
                  <h3 style={{ margin: 0 }}>Extracted Structured Details</h3>
                  {!saveSuccessMsg && (
                    <button
                      className="btn primary"
                      style={{ padding: '6px 16px', fontSize: 13, cursor: 'pointer' }}
                      onClick={() => handleNlpParse(true)}
                      disabled={isNlpLoading}
                    >
                      ✅ Confirm & Save Expense
                    </button>
                  )}
                </div>
                <div className="parsed-grid">
                  <div className="parsed-field">
                    <span className="lbl">Title</span>
                    <span className="val">{nlpResult.title}</span>
                  </div>
                  <div className="parsed-field">
                    <span className="lbl">Amount</span>
                    <span className="val highlight">₹{Number(nlpResult.amount).toFixed(2)}</span>
                  </div>
                  <div className="parsed-field">
                    <span className="lbl">Category</span>
                    <span className="val">{nlpResult.category_name}</span>
                  </div>
                  <div className="parsed-field">
                    <span className="lbl">Date</span>
                    <span className="val">{nlpResult.date_spent}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: WHAT-IF SIMULATOR */}
      {activeTab === 'simulate' && (
        <div className="ai-tab-content simulate-tab">
          <div className="simulator-grid">
            <div className="sim-controls-card">
              <h2>🔮 What-If Financial Scenario Builder</h2>
              <p>Test adjustments to your income, spending, and monthly savings to project real-time outcomes.</p>

              <div className="sim-field-group">
                <label>
                  Monthly Income Change (₹): <strong>{simIncomeChange >= 0 ? `+₹${simIncomeChange}` : `-₹${Math.abs(simIncomeChange)}`}</strong>
                </label>
                <input
                  type="range"
                  min="-20000"
                  max="50000"
                  step="500"
                  value={simIncomeChange}
                  onChange={(e) => setSimIncomeChange(Number(e.target.value))}
                />
              </div>

              <div className="sim-field-group">
                <label>
                  Expense Reduction Target (%): <strong>{simExpenseCut}%</strong>
                </label>
                <input
                  type="range"
                  min="0"
                  max="50"
                  step="5"
                  value={simExpenseCut}
                  onChange={(e) => setSimExpenseCut(Number(e.target.value))}
                />
              </div>

              <div className="sim-field-group">
                <label>
                  Extra Monthly Savings Addition (₹): <strong>+₹{simExtraSavings}</strong>
                </label>
                <input
                  type="range"
                  min="0"
                  max="10000"
                  step="250"
                  value={simExtraSavings}
                  onChange={(e) => setSimExtraSavings(Number(e.target.value))}
                />
              </div>

              <button className="sim-recalc-btn" onClick={handleRunSimulation} disabled={isSimLoading}>
                {isSimLoading ? 'Calculating...' : 'Recalculate AI Simulation 🚀'}
              </button>
            </div>

            {simResults && (
              <div className="sim-results-card">
                <h2>Projected Impact Summary</h2>

                <div className="sim-comparison-boxes">
                  <div className="sim-box baseline">
                    <div className="box-title">Current Baseline</div>
                    <div className="box-val">₹{simResults.baseline.net_savings.toFixed(2)}/mo</div>
                    <div className="box-sub">Savings Rate: {simResults.baseline.savings_rate}%</div>
                  </div>

                  <div className="sim-box simulated">
                    <div className="box-title">Simulated Scenario</div>
                    <div className="box-val" style={{ color: 'var(--green)' }}>₹{simResults.simulated.net_savings.toFixed(2)}/mo</div>
                    <div className="box-sub">Savings Rate: {simResults.simulated.savings_rate}%</div>
                  </div>
                </div>

                <div className="sim-gains-banner">
                  <div className="gain-item">
                    <span>Monthly Savings Lift:</span>
                    <strong>+₹{simResults.diff.monthly_savings_diff.toFixed(2)}</strong>
                  </div>
                  <div className="gain-item">
                    <span>1-Year Projected Wealth Increase:</span>
                    <strong style={{ color: 'var(--gold)' }}>+₹{simResults.diff.yearly_projected_diff.toFixed(2)}</strong>
                  </div>
                </div>

                {simResults.goals_impact.length > 0 && (
                  <div className="sim-goals-impact-list">
                    <h3>Impact on Savings Goals</h3>
                    {simResults.goals_impact.map((gi, idx) => (
                      <div key={idx} className="goal-impact-item">
                        <div>
                          <strong>{gi.name}</strong> (₹{gi.remaining.toFixed(2)} left)
                        </div>
                        <div className="impact-tag">
                          ⚡ {gi.months_faster > 0 ? `${gi.months_faster} months faster!` : 'Target stay'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
