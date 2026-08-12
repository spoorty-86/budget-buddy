import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import Money from '../components/Money'
import {
  ExpenseLineChart,
  CategoryDonutChart,
  IncomeExpenseBarChart,
  SavingsRadialProgress,
  BudgetGaugeMeter
} from '../components/Charts'

const MONTH_NAMES = [
  'All Months', 'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [goals, setGoals] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [trendView, setTrendView] = useState('line') // 'line' | 'bar'

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
      console.error('Failed to load dashboard analytics:', err)
      setError('Failed to load dashboard analytics data. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [month, year])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  // Extract key metrics
  const totalIncome = Number(data?.total_income || 0)
  const totalExpense = Number(data?.total_expense || 0)
  const currentBalance = Number(data?.current_balance || 0)
  const totalSavings = Number(data?.total_savings || 0)
  const totalBudget = Number(data?.total_budget || 0)
  const budgetExpensesTotal = Number(data?.budget_expenses_total ?? totalExpense)
  const remainingBudget = Number(data?.remaining_budget || 0)

  const budgetUsedPct = totalBudget > 0
    ? Math.min(100, Math.round((budgetExpensesTotal / totalBudget) * 100))
    : 0

  const expenseRatio = totalIncome > 0
    ? Math.min(100, Math.round((totalExpense / totalIncome) * 100))
    : 0

  const savingsRate = totalIncome > 0
    ? Math.max(0, Math.round(((totalIncome - totalExpense) / totalIncome) * 100))
    : 0

  const extremes = data?.expense_extremes || data?.['Highest & Lowest Expenses'] || {}
  const notifications = data?.latest_notifications || data?.['Latest Notifications'] || []
  const monthlyComparisonData = data?.monthly_comparison || data?.['Monthly Comparison'] || []
  const categoryVariances = data?.category_variances || data?.budget_variances || []
  const expensesByCategory = data?.expenses_by_category || []
  const recentTxs = data?.recent_transactions || []

  return (
    <div className="dashboard-container">
      {/* Top Header & Filters */}
      <div className="page-header" style={{ alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1>Analytics Dashboard</h1>
          <p className="page-sub">Comprehensive overview of income, expenses, budgets, savings, and financial visualizations.</p>
        </div>

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            style={{
              height: 38,
              padding: '0 14px',
              borderRadius: 8,
              border: '1px solid var(--line)',
              background: '#fff',
              color: 'var(--ink)',
              fontSize: 13.5,
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
              outline: 'none',
            }}
          >
            {MONTH_NAMES.map((name, idx) => (
              <option key={idx} value={idx}>{name}</option>
            ))}
          </select>

          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            placeholder="Year"
            style={{
              height: 38,
              width: 85,
              padding: '0 12px',
              borderRadius: 8,
              border: '1px solid var(--line)',
              background: '#fff',
              color: 'var(--ink)',
              fontSize: 13.5,
              fontWeight: 600,
              boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
              outline: 'none',
            }}
          />

          <Link
            to="/expenses"
            style={{
              height: 38,
              padding: '0 14px',
              borderRadius: 8,
              border: '1px solid var(--line)',
              background: '#fff',
              color: 'var(--ink)',
              fontSize: 13.5,
              fontWeight: 600,
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
            }}
          >
            + Expense
          </Link>

          <Link
            to="/incomes"
            style={{
              height: 38,
              padding: '0 14px',
              borderRadius: 8,
              border: '1px solid var(--line)',
              background: '#fff',
              color: 'var(--ink)',
              fontSize: 13.5,
              fontWeight: 600,
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
            }}
          >
            + Income
          </Link>

          <Link
            to="/reports"
            className="btn-primary"
            style={{
              height: 38,
              padding: '0 16px',
              borderRadius: 8,
              fontSize: 13.5,
              fontWeight: 600,
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6
            }}
          >
            📊 Reports & Export
          </Link>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="card" style={{ textAlign: 'center', padding: 50 }}>
          <p className="empty-state">Loading financial analytics and chart visualizations...</p>
        </div>
      ) : (
        <>
          {/* Module 1: Top Core Metric Cards Grid */}
          <div className="stat-row-5">
            {/* Total Income */}
            <div className="card stat-card income">
              <div className="stat-label">Total Income</div>
              <div className="stat-value">
                <Money value={totalIncome} sign="pos" />
              </div>
              <div style={{ fontSize: 12, color: 'var(--ink-soft)', marginTop: 6 }}>
                Recorded period revenue
              </div>
            </div>

            {/* Total Expenses */}
            <div className="card stat-card expense">
              <div className="stat-label">Total Expenses</div>
              <div className="stat-value">
                <Money value={totalExpense} sign="neg" />
              </div>
              <div style={{ fontSize: 12, color: 'var(--ink-soft)', marginTop: 6 }}>
                {totalIncome > 0 ? `${expenseRatio}% of income spent` : 'No income recorded'}
              </div>
            </div>

            {/* Current Balance */}
            <div className="card stat-card balance">
              <div className="stat-label">Current Balance</div>
              <div className="stat-value">
                <Money value={currentBalance} sign={currentBalance >= 0 ? 'pos' : 'neg'} />
              </div>
              <div style={{ fontSize: 12, color: currentBalance >= 0 ? 'var(--green)' : 'var(--red)', marginTop: 6, fontWeight: 500 }}>
                {currentBalance >= 0 ? 'Surplus / Net positive' : 'Deficit / Overspent'}
              </div>
            </div>

            {/* Total Savings */}
            <div className="card stat-card savings">
              <div className="stat-label">Total Savings</div>
              <div className="stat-value">
                <Money value={totalSavings} sign="pos" />
              </div>
              <div style={{ fontSize: 12, color: '#6d28d9', marginTop: 6, fontWeight: 500 }}>
                {goals.length} active savings {goals.length === 1 ? 'goal' : 'goals'}
              </div>
            </div>

            {/* Budget Variance */}
            <div className="card stat-card" style={{ borderLeft: `4px solid ${remainingBudget < 0 ? 'var(--red)' : 'var(--gold)'}` }}>
              <div className="stat-label">Budget Variance</div>
              <div className="stat-value">
                <Money value={remainingBudget} sign={remainingBudget < 0 ? 'neg' : 'pos'} />
              </div>
              <div style={{ fontSize: 12, color: remainingBudget >= 0 ? 'var(--green)' : 'var(--red)', marginTop: 6, fontWeight: 500 }}>
                {totalBudget > 0
                  ? (remainingBudget >= 0
                      ? `₹${remainingBudget.toLocaleString()} under limit`
                      : `₹${Math.abs(remainingBudget).toLocaleString()} over limit`)
                  : 'No budget set'}
              </div>
            </div>
          </div>

          {/* Module 2: Financial Health Diagnostic & Budget Gauge Meter */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20, marginBottom: 24 }}>
            {/* Financial Health Banner */}
            <div className="health-banner" style={{ margin: 0, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <h3 style={{ fontSize: 18, color: '#fff', marginBottom: 4 }}>
                    Financial Health Diagnostics
                  </h3>
                  <span style={{ fontSize: 11, background: 'rgba(255,255,255,0.15)', color: '#fff', padding: '2px 8px', borderRadius: 12, fontWeight: 700 }}>
                    {currentBalance >= 0 ? '✅ Healthy' : '⚠️ Deficit'}
                  </span>
                </div>
                <p style={{ fontSize: 13, opacity: 0.9, marginTop: 4, margin: '4px 0 0 0' }}>
                  {currentBalance >= 0
                    ? `Great job! You retained ${savingsRate}% of total income for this period.`
                    : `Alert: Total expenses exceed income by ₹${Math.abs(currentBalance).toLocaleString()}.`}
                </p>
              </div>

              <div className="health-metrics-grid" style={{ marginTop: 16 }}>
                <div className="health-metric-box">
                  <div style={{ fontSize: 11, opacity: 0.8, textTransform: 'uppercase' }}>Savings Rate</div>
                  <div style={{ fontSize: 19, fontWeight: 700, color: '#6ee7b7' }}>{savingsRate}%</div>
                </div>
                <div className="health-metric-box">
                  <div style={{ fontSize: 11, opacity: 0.8, textTransform: 'uppercase' }}>Expense Ratio</div>
                  <div style={{ fontSize: 19, fontWeight: 700, color: expenseRatio > 90 ? '#fca5a5' : '#93c5fd' }}>{expenseRatio}%</div>
                </div>
                <div className="health-metric-box">
                  <div style={{ fontSize: 11, opacity: 0.8, textTransform: 'uppercase' }}>Active Goals</div>
                  <div style={{ fontSize: 19, fontWeight: 700, color: '#c4b5fd' }}>{goals.length} Goals</div>
                </div>
              </div>
            </div>

            {/* Chart Visualization 5: Overall Budget Utilization Gauge Meter */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ fontSize: 16 }}>Budget Utilization Gauge</h3>
                <Link to="/budgets" style={{ fontSize: 12.5, color: 'var(--green)', textDecoration: 'none', fontWeight: 600 }}>Budgets &rarr;</Link>
              </div>

              {totalBudget <= 0 ? (
                <div style={{ textAlign: 'center', padding: '30px 0' }}>
                  <p style={{ fontSize: 13, color: 'var(--ink-soft)', marginBottom: 10 }}>No budget limit configured.</p>
                  <Link to="/budgets" className="btn secondary" style={{ fontSize: 12, textDecoration: 'none', padding: '6px 12px' }}>
                    + Set Up Budget
                  </Link>
                </div>
              ) : (
                <BudgetGaugeMeter totalBudget={totalBudget} budgetExpensesTotal={budgetExpensesTotal} />
              )}
            </div>
          </div>

          {/* Module 3 & 4: Two-Column Section for Interactive Line/Bar Charts & Category Donut Chart */}
          <div className="dashboard-2col">
            {/* Chart Visualizations 1 & 3: Line Chart & Bar Chart (with view switcher) */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 8 }}>
                <div>
                  <h3 style={{ fontSize: 16 }}>
                    {trendView === 'line' ? 'Monthly Expense Trend Line Chart' : 'Income vs Expense Bar Chart'}
                  </h3>
                  <p style={{ fontSize: 12, color: 'var(--ink-soft)', margin: '2px 0 0 0' }}>
                    {trendView === 'line' ? 'Smooth monthly expense trend trajectory' : 'Side-by-side comparison of inflow vs outflow'}
                  </p>
                </div>

                {/* Switcher Tabs */}
                <div style={{ display: 'inline-flex', background: '#f1f5f9', borderRadius: 8, padding: 3 }}>
                  <button
                    onClick={() => setTrendView('line')}
                    style={{
                      border: 'none',
                      background: trendView === 'line' ? '#ffffff' : 'transparent',
                      color: trendView === 'line' ? 'var(--ink)' : 'var(--ink-soft)',
                      fontWeight: 600,
                      fontSize: 12,
                      padding: '4px 10px',
                      borderRadius: 6,
                      boxShadow: trendView === 'line' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none'
                    }}
                  >
                    📈 Line Chart
                  </button>
                  <button
                    onClick={() => setTrendView('bar')}
                    style={{
                      border: 'none',
                      background: trendView === 'bar' ? '#ffffff' : 'transparent',
                      color: trendView === 'bar' ? 'var(--ink)' : 'var(--ink-soft)',
                      fontWeight: 600,
                      fontSize: 12,
                      padding: '4px 10px',
                      borderRadius: 6,
                      boxShadow: trendView === 'bar' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none'
                    }}
                  >
                    📊 Bar Chart
                  </button>
                </div>
              </div>

              {trendView === 'line' ? (
                <ExpenseLineChart data={monthlyComparisonData} />
              ) : (
                <IncomeExpenseBarChart data={monthlyComparisonData} />
              )}
            </div>

            {/* Chart Visualization 2: Category-wise Expense Donut Chart */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <div>
                  <h3 style={{ fontSize: 16 }}>Category Expense Donut Chart</h3>
                  <p style={{ fontSize: 12, color: 'var(--ink-soft)', margin: '2px 0 0 0' }}>Proportional breakdown of category spending</p>
                </div>
                <Link to="/expenses" style={{ fontSize: 12.5, color: 'var(--green)', textDecoration: 'none', fontWeight: 600 }}>All Expenses</Link>
              </div>

              <CategoryDonutChart data={expensesByCategory} />
            </div>
          </div>

          {/* Module 5: Budget Status & Category Utilization Visual Meters */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <h3 style={{ fontSize: 16 }}>Budget Status & Category Utilization</h3>
                <p style={{ fontSize: 12, color: 'var(--ink-soft)', margin: '2px 0 0 0' }}>
                  Visual breakdown of budget limits vs. actual spent with variance status
                </p>
              </div>
              <Link to="/budgets" style={{ fontSize: 13, color: 'var(--green)', textDecoration: 'none', fontWeight: 600 }}>
                Manage Budgets &rarr;
              </Link>
            </div>

            {categoryVariances.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '20px 0' }}>
                <p style={{ fontSize: 13, color: 'var(--ink-soft)', marginBottom: 10 }}>
                  No category budgets configured for this period.
                </p>
                <Link to="/budgets" className="btn secondary" style={{ fontSize: 12, textDecoration: 'none', padding: '6px 14px' }}>
                  + Create Category Budget
                </Link>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {categoryVariances.map((bv) => {
                  const limit = Number(bv.budget_limit || 0)
                  const spent = Number(bv.spent || 0)
                  const variance = Number(bv.variance || 0)
                  const isOver = variance < 0 || bv.status === 'OVER_BUDGET'
                  const pctUsed = bv.pct_used || (limit > 0 ? Math.round((spent / limit) * 100) : 0)

                  return (
                    <div key={bv.id} style={{ padding: '12px 14px', borderRadius: 8, background: '#f8fafc', border: '1px solid var(--line)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <span className="tag" style={{ fontSize: 13, fontWeight: 700 }}>{bv.category_name}</span>
                          <span
                            style={{
                              fontSize: 11.5,
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: 12,
                              background: isOver ? '#fee2e2' : '#dcfce7',
                              color: isOver ? '#dc2626' : '#15803d'
                            }}
                          >
                            {isOver ? `⚠️ Over Budget (-₹${Math.abs(variance).toLocaleString()})` : `✅ Under Budget (+₹${variance.toLocaleString()})`}
                          </span>
                        </div>

                        <div style={{ fontSize: 13, fontWeight: 600 }}>
                          Limit: <Money value={limit} /> | Spent: <Money value={spent} sign={spent > 0 ? 'neg' : undefined} /> | <span style={{ color: isOver ? 'var(--red)' : 'var(--green)' }}>Variance: {variance >= 0 ? '+' : ''}<Money value={variance} /></span>
                        </div>
                      </div>

                      {/* Utilization Bar */}
                      <div className="progress-track" style={{ height: 8 }}>
                        <div
                          className={`progress-fill${isOver ? ' over' : ''}`}
                          style={{
                            width: `${Math.min(100, pctUsed)}%`,
                            background: isOver ? 'var(--red)' : pctUsed >= 80 ? 'var(--gold)' : 'var(--green)'
                          }}
                        />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11.5, color: 'var(--ink-soft)', marginTop: 4 }}>
                        <span>{pctUsed}% of limit used</span>
                        <span>{isOver ? '0% limit remaining' : `${Math.max(0, 100 - pctUsed).toFixed(1)}% variance remaining`}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Module 6 & 7: Two-Column Section for Savings Goals Progress Rings & Notifications */}
          <div className="dashboard-2col">
            {/* Chart Visualization 4: Progress Visualization for Savings Goals */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <div>
                  <h3 style={{ fontSize: 16 }}>Savings Goal Radial Progress</h3>
                  <p style={{ fontSize: 12, color: 'var(--ink-soft)', margin: '2px 0 0 0' }}>Circular progress rings for target completion</p>
                </div>
                <Link to="/savings" style={{ fontSize: 12.5, color: 'var(--green)', textDecoration: 'none', fontWeight: 600 }}>Manage Goals &rarr;</Link>
              </div>

              {goals.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px 0' }}>
                  <p style={{ fontSize: 13, color: 'var(--ink-soft)', marginBottom: 10 }}>No active savings goals set.</p>
                  <Link to="/savings" className="btn secondary" style={{ fontSize: 12, textDecoration: 'none', padding: '6px 12px' }}>
                    + Add Savings Goal
                  </Link>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {goals.map((g) => (
                    <SavingsRadialProgress key={g.id} goal={g} />
                  ))}
                </div>
              )}
            </div>

            {/* Notifications & Financial Alerts Widget */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <div>
                  <h3 style={{ fontSize: 16 }}>Notifications & Financial Alerts</h3>
                  <p style={{ fontSize: 12, color: 'var(--ink-soft)', margin: '2px 0 0 0' }}>Recent activity warnings and priority alerts</p>
                </div>
                <Link to="/notifications" style={{ fontSize: 12.5, color: 'var(--green)', textDecoration: 'none', fontWeight: 600 }}>All Alerts &rarr;</Link>
              </div>

              {notifications.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px 0' }}>
                  <p style={{ fontSize: 13, color: 'var(--ink-soft)' }}>No new notifications or alerts.</p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {notifications.slice(0, 4).map((n) => {
                    const priorityClass = n.priority === 'HIGH' ? 'high' : n.priority === 'MEDIUM' ? 'warning' : 'info'
                    return (
                      <div key={n.id} className={`notif-item priority-${priorityClass}`}>
                        <div style={{ fontSize: 16, marginTop: 2 }}>
                          {n.priority === 'HIGH' ? '🚨' : n.priority === 'MEDIUM' ? '⚠️' : 'ℹ️'}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                            <span style={{ fontSize: 13, fontWeight: 700 }}>{n.title}</span>
                            <span className={`badge-priority ${priorityClass}`}>{n.priority || 'INFO'}</span>
                          </div>
                          <p style={{ fontSize: 12, color: 'var(--ink-soft)', margin: 0 }}>{n.message}</p>
                          <div style={{ fontSize: 11, color: 'var(--ink-soft)', opacity: 0.7, marginTop: 4 }}>
                            {new Date(n.created_at).toLocaleDateString()} {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Module 8: Recent Activity Ledger Stream */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <h3 style={{ fontSize: 16 }}>Recent Activity Ledger</h3>
                <p style={{ fontSize: 12, color: 'var(--ink-soft)', margin: '2px 0 0 0' }}>Latest recorded income and expense transactions</p>
              </div>
              <div style={{ display: 'flex', gap: 12 }}>
                <Link to="/expenses" style={{ fontSize: 13, color: 'var(--ink-soft)', textDecoration: 'none', fontWeight: 500 }}>Expenses &rarr;</Link>
                <Link to="/incomes" style={{ fontSize: 13, color: 'var(--ink-soft)', textDecoration: 'none', fontWeight: 500 }}>Incomes &rarr;</Link>
              </div>
            </div>

            {recentTxs.length === 0 ? (
              <p className="empty-state" style={{ padding: '24px 0' }}>No recent activity recorded for this period.</p>
            ) : (
              <table className="ledger">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Title</th>
                    <th>Category</th>
                    <th>Date</th>
                    <th className="num">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {recentTxs.map((tx) => {
                    const isIncome = tx.type === 'income'
                    return (
                      <tr key={tx.id}>
                        <td>
                          <span
                            className="tag"
                            style={{
                              background: isIncome ? 'var(--green-soft)' : 'var(--red-soft)',
                              color: isIncome ? 'var(--green)' : 'var(--red)',
                              fontWeight: 700
                            }}
                          >
                            {isIncome ? 'Income' : 'Expense'}
                          </span>
                        </td>
                        <td style={{ fontWeight: 600 }}>{tx.title}</td>
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

          {/* Module 9: Expense Extremes & Financial Reports Summary Highlights */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <h3 style={{ fontSize: 16 }}>Expense Extremes & Financial Highlights</h3>
                <p style={{ fontSize: 12, color: 'var(--ink-soft)', margin: '2px 0 0 0' }}>Notable expense bounds for period analysis</p>
              </div>
              <Link to="/reports" className="btn secondary" style={{ fontSize: 12.5, textDecoration: 'none', padding: '6px 12px' }}>
                Generate Full PDF/CSV Report &rarr;
              </Link>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
              {/* Highest Expense */}
              <div className="extreme-card">
                <div>
                  <div style={{ fontSize: 12, color: 'var(--red)', fontWeight: 700, textTransform: 'uppercase' }}>Highest Expense</div>
                  <div style={{ fontSize: 14, fontWeight: 700, marginTop: 4 }}>
                    {extremes.highest_expense ? extremes.highest_expense.title : 'None recorded'}
                  </div>
                  {extremes.highest_expense && (
                    <div style={{ fontSize: 12, color: 'var(--ink-soft)' }}>{extremes.highest_expense.category} &bull; {extremes.highest_expense.date_spent}</div>
                  )}
                </div>
                <div style={{ textAlign: 'right' }}>
                  {extremes.highest_expense ? (
                    <Money value={extremes.highest_expense.amount} sign="neg" />
                  ) : '—'}
                </div>
              </div>

              {/* Lowest Expense */}
              <div className="extreme-card">
                <div>
                  <div style={{ fontSize: 12, color: 'var(--green)', fontWeight: 700, textTransform: 'uppercase' }}>Lowest Expense</div>
                  <div style={{ fontSize: 14, fontWeight: 700, marginTop: 4 }}>
                    {extremes.lowest_expense ? extremes.lowest_expense.title : 'None recorded'}
                  </div>
                  {extremes.lowest_expense && (
                    <div style={{ fontSize: 12, color: 'var(--ink-soft)' }}>{extremes.lowest_expense.category} &bull; {extremes.lowest_expense.date_spent}</div>
                  )}
                </div>
                <div style={{ textAlign: 'right' }}>
                  {extremes.lowest_expense ? (
                    <Money value={extremes.lowest_expense.amount} sign="neg" />
                  ) : '—'}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}