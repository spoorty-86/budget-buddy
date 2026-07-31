import { useEffect, useState } from 'react'
import api from '../api'
import Money from '../components/Money'

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

export default function Dashboard() {
  const now = new Date()
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear] = useState(now.getFullYear())
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    setLoading(true)
    api.get(`/api/finance/dashboard/?month=${month}&year=${year}`).then(({ data }) => {
      if (active) setData(data)
    }).finally(() => active && setLoading(false))
    return () => { active = false }
  }, [month, year])

  const categoryItems = data?.expenses_by_category || []
  const recentTransactions = data?.recent_transactions || []
  const netBalance = Number(data?.current_balance || 0)

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="page-sub">Where your money went this period.</p>
        </div>
        <div className="form-row" style={{ margin: 0, padding: '10px 14px' }}>
          <div className="field">
            <label>Month</label>
            <select value={month} onChange={(e) => setMonth(Number(e.target.value))}>
              {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
            </select>
          </div>
          <div className="field">
            <label>Year</label>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              style={{ width: 90 }}
            />
          </div>
        </div>
      </div>

      {loading && <p className="empty-state">Loading…</p>}

      {!loading && data && (
        <>
          <div className="stat-row">
            <div className="card stat-card income">
              <div className="stat-label">Income</div>
              <div className="stat-value"><Money value={data.total_income} sign="pos" /></div>
            </div>
            <div className="card stat-card expense">
              <div className="stat-label">Expenses</div>
              <div className="stat-value"><Money value={data.total_expense} sign="neg" /></div>
            </div>
            <div className="card stat-card balance">
              <div className="stat-label">Net Balance</div>
              <div className="stat-value">
                <Money value={netBalance} sign={netBalance < 0 ? 'neg' : 'pos'} />
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <div className="card">
              <h3 style={{ marginBottom: 14, fontSize: 16 }}>By category</h3>
              {categoryItems.length === 0 && (
                <p className="empty-state">No expenses logged yet.</p>
              )}
              {categoryItems.length > 0 && (
                <div style={{ display: 'grid', gap: '8px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', fontWeight: '700', padding: '0 6px', color: '#222' }}>
                    <span>Category</span>
                    <span style={{ textAlign: 'right' }}>Spent</span>
                  </div>
                  {categoryItems.map((c) => (
                    <div
                      key={c.category__name || 'uncategorized'}
                      style={{ display: 'grid', gridTemplateColumns: '1fr auto', padding: '4px 6px', color: '#111' }}
                    >
                      <span>{c.category__name || 'Uncategorized'}</span>
                      <span style={{ textAlign: 'right' }}><Money value={c.total} sign="neg" /></span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="card">
              <h3 style={{ marginBottom: 14, fontSize: 16 }}>Recent transactions</h3>
              {recentTransactions.length === 0 && (
                <p className="empty-state">Nothing recorded yet.</p>
              )}
              {recentTransactions.length > 0 && (
                <table className="ledger">
                  <thead><tr><th>Title</th><th>Date</th><th className="num">Amount</th></tr></thead>
                  <tbody>
                    {recentTransactions.map((t) => (
                      <tr key={t.id || `${t.type}-${t.title}-${t.date}`}>
                        <td>{t.title}</td>
                        <td>{t.date || t.date_spent}</td>
                        <td className="num"><Money value={t.amount} sign={t.type === 'expense' ? 'neg' : 'pos'} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </>
      )}

      {!loading && !data && (
        <p className="empty-state">Unable to load dashboard. Please refresh or log in again.</p>
      )}
    </>
  )
}
