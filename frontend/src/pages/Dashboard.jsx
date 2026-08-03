import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import Money from '../components/Money'

const MONTH_NAMES = [
  'All Months', 'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [goals, setGoals] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const currentDate = new Date()
  const [month, setMonth] = useState(currentDate.getMonth() + 1)
  const [year, setYear] = useState(currentDate.getFullYear())

  const loadDashboard = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams()
      if (month > 0) params.set('month', month)
      if (year > 0) params.set('year', year)

      const dashRes = await api.get(`/api/analytics/dashboard/?${params.toString()}`)
      setData(dashRes.data)
      setGoals(dashRes.data.active_savings_goals || [])
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
      setError('Failed to load dashboard data. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [month, year])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  const totalIncome = Number(data?.total_income || 0)
  const totalExpense = Number(data?.total_expense || 0)
  const currentBalance = Number(data?.current_balance || 0)
  const totalBudget = Number(data?.total_budget || 0)
  const remainingBudget = Number(data?.remaining_budget || 0)

  const budgetUsedPct = totalBudget > 0
    ? Math.min(100, Math.round((totalExpense / totalBudget) * 100))
    : 0

  const expenseRatio = totalIncome > 0
    ? Math.min(100, Math.round((totalExpense / totalIncome) * 100))
    : 0

  return (
    <div className="dashboard-container">
      <div className="page-header" style={{ alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1>Dashboard</h1>
          <p className="page-sub">Track your financial status, monthly overview, and spending habits.</p>
        </div>

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="field" style={{ minWidth: 120 }}>
            <select value={month} onChange={(e) => setMonth(Number(e.target.value))}>
              {MONTH_NAMES.map((name, idx) => (
                <option key={idx} value={idx}>{name}</option>
              ))}
            </select>
          </div>
          <div className="field" style={{ minWidth: 100 }}>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              placeholder="Year"
              style={{ width: 90 }}
            />
          </div>
          <Link to="/expenses" className="btn" style={{ fontSize: 13, textDecoration: 'none' }}>+ Expense</Link>
          <Link to="/incomes" className="btn secondary" style={{ fontSize: 13, textDecoration: 'none' }}>+ Income</Link>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="card" style={{ textAlign: 'center', padding: 50 }}>
          <p className="empty-state">Loading dashboard financial overview...</p>
        </div>
      ) : (
        <>
          {/* Key Stat Cards */}
          <div className="stat-row">
            <div className="card stat-card income">
              <div className="stat-label">Total Income</div>
              <div className="stat-value">
                <Money value={totalIncome} sign="pos" />
              </div>
              <div style={{ fontSize: 12, color: 'var(--ink-soft)', marginTop: 6 }}>
                For selected period
              </div>
            </div>

            <div className="card stat-card expense">
              <div className="stat-label">Total Expenses</div>
              <div className="stat-value">
                <Money value={totalExpense} sign="neg" />
              </div>
              <div style={{ fontSize: 12, color: 'var(--ink-soft)', marginTop: 6 }}>
                {totalIncome > 0 ? `${expenseRatio}% of total income` : 'No income recorded'}
              </div>
            </div>

            <div className="card stat-card balance">
              <div className="stat-label">Net Balance</div>
              <div className="stat-value">
                <Money value={currentBalance} sign={currentBalance >= 0 ? 'pos' : 'neg'} />
              </div>
              <div style={{ fontSize: 12, color: currentBalance >= 0 ? 'var(--green)' : 'var(--red)', marginTop: 6, fontWeight: 500 }}>
                {currentBalance >= 0 ? 'Positive balance' : 'Deficit / Overspent'}
              </div>
            </div>

            <div className="card stat-card" style={{ borderLeftColor: budgetUsedPct > 100 ? 'var(--red)' : 'var(--gold)' }}>
              <div className="stat-label">Budget Remaining</div>
              <div className="stat-value">
                <Money value={remainingBudget} sign={remainingBudget < 0 ? 'neg' : undefined} />
              </div>
              <div style={{ fontSize: 12, color: 'var(--ink-soft)', marginTop: 6 }}>
                {totalBudget > 0 ? `${budgetUsedPct}% of ₹${totalBudget.toLocaleString()} spent` : 'No budget configured'}
              </div>
            </div>
          </div>

          {/* Welcome Banner for empty accounts */}
          {!data?.has_any_data && (
            <div className="card" style={{ marginBottom: 24, padding: 24, background: 'var(--gold-soft)', borderColor: 'var(--gold)' }}>
              <h3 style={{ marginBottom: 8, color: 'var(--ink)' }}>Welcome to BudgetBuddy! 🚀</h3>
              <p style={{ fontSize: 14, color: 'var(--ink-soft)', margin: '0 0 16px 0' }}>
                You haven't added any income or expenses yet. Start building your financial overview by logging your first transaction or setting up a budget limit.
              </p>
              <div style={{ display: 'flex', gap: 12 }}>
                <Link to="/incomes" className="btn" style={{ textDecoration: 'none' }}>Add Income</Link>
                <Link to="/expenses" className="btn secondary" style={{ textDecoration: 'none' }}>Record Expense</Link>
                <Link to="/budgets" className="btn secondary" style={{ textDecoration: 'none' }}>Create Budget</Link>
              </div>
            </div>
          )}

          {/* Two-Column Analytics Layout */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20, marginBottom: 24 }}>
            {/* Category Expense Breakdown */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ fontSize: 16 }}>Expense by Category</h3>
                <Link to="/expenses" style={{ fontSize: 13, color: 'var(--green)', textDecoration: 'none', fontWeight: 600 }}>View All</Link>
              </div>

              {(!data?.expenses_by_category || data.expenses_by_category.length === 0) ? (
                <p className="empty-state" style={{ padding: '20px 0' }}>No category spending data for this period.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  {data.expenses_by_category.map((item, idx) => {
                    const catName = item.category__name || 'Uncategorized'
                    const catTotal = Number(item.total || 0)
                    const pct = totalExpense > 0 ? Math.round((catTotal / totalExpense) * 100) : 0

                    return (
                      <div key={idx}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                          <span style={{ fontWeight: 600 }}>{catName}</span>
                          <span className="amount neg">-₹{catTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ({pct}%)</span>
                        </div>
                        <div className="progress-track" style={{ height: 8 }}>
                          <div
                            className="progress-fill"
                            style={{
                              width: `${pct}%`,
                              background: idx % 3 === 0 ? 'var(--red)' : idx % 3 === 1 ? 'var(--gold)' : 'var(--ink)'
                            }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Savings Goals & Budget Overview */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ fontSize: 16 }}>Savings Goals & Budget Progress</h3>
                <Link to="/savings" style={{ fontSize: 13, color: 'var(--green)', textDecoration: 'none', fontWeight: 600 }}>Manage Goals</Link>
              </div>

              {/* Overall Budget Progress */}
              {totalBudget > 0 && (
                <div style={{ paddingBottom: 16, marginBottom: 16, borderBottom: '1px solid var(--line)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 6 }}>
                    <span style={{ fontWeight: 600 }}>Monthly Budget Used</span>
                    <span><strong>₹{totalExpense.toLocaleString()}</strong> of ₹{totalBudget.toLocaleString()}</span>
                  </div>
                  <div className="progress-track" style={{ height: 10 }}>
                    <div
                      className={`progress-fill${budgetUsedPct > 100 ? ' over' : ''}`}
                      style={{ width: `${budgetUsedPct}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Top Savings Goals */}
              {goals.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '16px 0' }}>
                  <p style={{ fontSize: 13, color: 'var(--ink-soft)', marginBottom: 10 }}>No active savings goals.</p>
                  <Link to="/savings" className="btn secondary" style={{ fontSize: 12, textDecoration: 'none', padding: '6px 12px' }}>+ Create Savings Goal</Link>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  {goals.slice(0, 3).map((g) => {
                    const saved = Number(g.saved_amount || 0)
                    const target = Number(g.target_amount || 1)
                    const progress = Math.min(100, Math.round((saved / target) * 100))

                    return (
                      <div key={g.id}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                          <span style={{ fontWeight: 600 }}>🎯 {g.name}</span>
                          <span style={{ color: 'var(--green)', fontWeight: 600 }}>{progress}%</span>
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--ink-soft)', marginBottom: 4 }}>
                          <Money value={saved} sign="pos" /> saved of <Money value={target} />
                        </div>
                        <div className="progress-track">
                          <div className="progress-fill" style={{ width: `${progress}%` }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Recent Transactions Feed */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ fontSize: 16 }}>Recent Activity</h3>
              <div style={{ display: 'flex', gap: 12 }}>
                <Link to="/expenses" style={{ fontSize: 13, color: 'var(--ink-soft)', textDecoration: 'none' }}>Expenses &rarr;</Link>
                <Link to="/incomes" style={{ fontSize: 13, color: 'var(--ink-soft)', textDecoration: 'none' }}>Incomes &rarr;</Link>
              </div>
            </div>

            {(!data?.recent_transactions || data.recent_transactions.length === 0) ? (
              <p className="empty-state">No recent activity recorded for this period.</p>
            ) : (
              <table className="ledger">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Title</th>
                    <th>Category / Notes</th>
                    <th>Date</th>
                    <th className="num">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_transactions.map((tx) => {
                    const isIncome = tx.type === 'income'
                    return (
                      <tr key={tx.id}>
                        <td>
                          <span
                            className="tag"
                            style={{
                              background: isIncome ? 'var(--green-soft)' : 'var(--red-soft)',
                              color: isIncome ? 'var(--green)' : 'var(--red)'
                            }}
                          >
                            {isIncome ? 'Income' : 'Expense'}
                          </span>
                        </td>
                        <td style={{ fontWeight: 500 }}>{tx.title}</td>
                        <td>
                          {tx.category ? <span className="tag">{tx.category}</span> : '—'}
                        </td>
                        <td style={{ fontSize: 13, color: 'var(--ink-soft)' }}>{tx.date}</td>
                        <td className="num">
                          <Money value={tx.amount} sign={isIncome ? 'pos' : 'neg'} />
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  )
}