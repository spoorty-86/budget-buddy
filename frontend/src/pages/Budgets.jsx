import { useEffect, useState } from 'react'
import api from '../api'
import Money from '../components/Money'

const now = new Date()
const empty = { category: '', monthly_limit: '', month: now.getMonth() + 1, year: now.getFullYear() }

export default function Budgets() {
  const [items, setItems] = useState([])
  const [categories, setCategories] = useState([])
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    Promise.all([
      api.get('/api/finance/budgets/'),
      api.get('/api/finance/categories/'),
    ]).then(([b, c]) => {
      setItems(b.data)
      setCategories(c.data)
    }).finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (!form.category) {
      setError('Pick a category first.')
      return
    }
    try {
      await api.post('/api/finance/budgets/', form)
      setForm(empty)
      load()
    } catch {
      setError('Could not save that budget — you may already have one for this category and month.')
    }
  }

  async function remove(id) {
    await api.delete(`/api/finance/budgets/${id}/`)
    load()
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Budgets</h1>
          <p className="page-sub">Set a monthly limit per category and track it live.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form className="form-row" onSubmit={handleSubmit}>
        <div className="field">
          <label>Category</label>
          <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} required>
            <option value="">Choose one</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Monthly limit</label>
          <input type="number" step="0.01" value={form.monthly_limit} onChange={(e) => setForm({ ...form, monthly_limit: e.target.value })} placeholder="0.00" required />
        </div>
        <div className="field">
          <label>Month</label>
          <input type="number" min={1} max={12} value={form.month} onChange={(e) => setForm({ ...form, month: Number(e.target.value) })} style={{ width: 70 }} required />
        </div>
        <div className="field">
          <label>Year</label>
          <input type="number" value={form.year} onChange={(e) => setForm({ ...form, year: Number(e.target.value) })} style={{ width: 90 }} required />
        </div>
        <button className="btn" type="submit">Add budget</button>
      </form>

      {loading && <p className="empty-state">Loading…</p>}
      {!loading && items.length === 0 && <div className="card"><p className="empty-state">No budgets set yet.</p></div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
        {items.map((b) => {
          const pct = Math.min(100, (Number(b.spent) / Number(b.monthly_limit)) * 100 || 0)
          const over = Number(b.spent) > Number(b.monthly_limit)
          return (
            <div className="card" key={b.id}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <strong>{b.category_name}</strong>
                <span style={{ fontSize: 12.5, color: 'var(--ink-soft)' }}>{b.month}/{b.year}</span>
              </div>
              <div style={{ marginTop: 10, fontSize: 14 }}>
                <Money value={b.spent} sign={over ? 'neg' : undefined} /> of <Money value={b.monthly_limit} />
              </div>
              <div className="progress-track">
                <div className={`progress-fill${over ? ' over' : ''}`} style={{ width: `${pct}%` }} />
              </div>
              <button className="btn secondary" style={{ marginTop: 14 }} onClick={() => remove(b.id)}>Remove</button>
            </div>
          )
        })}
      </div>
    </>
  )
}
