import { useEffect, useState } from 'react'
import api from '../api'
import Money from '../components/Money'

const empty = { name: '', target_amount: '', saved_amount: '0', target_date: '' }

export default function SavingsGoals() {
  const [items, setItems] = useState([])
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    api.get('/api/finance/savings-goals/').then(({ data }) => setItems(data)).finally(() => setLoading(false))
  }

  useEffect(load, [])

  function formatApiError(error) {
    const data = error.response?.data
    if (!data) return 'Could not save that goal. Check the fields and try again.'
    if (typeof data === 'string') return data
    if (Array.isArray(data)) return data.join(' ')
    if (data.detail) return data.detail
    return Object.entries(data)
      .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(' ') : value}`)
      .join(' ')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    const payload = {
      name: form.name,
      target_amount: form.target_amount === '' ? null : Number(form.target_amount),
      saved_amount: form.saved_amount === '' ? 0 : Number(form.saved_amount),
      target_date: form.target_date || null,
    }

    if (!payload.name || payload.target_amount === null || Number.isNaN(payload.target_amount)) {
      setError('Goal name and a valid target amount are required.')
      return
    }

    try {
      await api.post('/api/finance/savings-goals/', payload)
      setForm(empty)
      load()
    } catch (error) {
      setError(formatApiError(error))
    }
  }

  async function remove(id) {
    await api.delete(`/api/finance/savings-goals/${id}/`)
    load()
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Savings Goals</h1>
          <p className="page-sub">What you're setting money aside for.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form className="form-row" onSubmit={handleSubmit}>
        <div className="field">
          <label>Name</label>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Emergency fund" required />
        </div>
        <div className="field">
          <label>Target amount</label>
          <input type="number" step="0.01" value={form.target_amount} onChange={(e) => setForm({ ...form, target_amount: e.target.value })} placeholder="0.00" required />
        </div>
        <div className="field">
          <label>Saved so far</label>
          <input type="number" step="0.01" value={form.saved_amount} onChange={(e) => setForm({ ...form, saved_amount: e.target.value })} placeholder="0.00" />
        </div>
        <div className="field">
          <label>Target date</label>
          <input type="date" value={form.target_date} onChange={(e) => setForm({ ...form, target_date: e.target.value })} />
        </div>
        <button className="btn" type="submit">Add goal</button>
      </form>

      {loading && <p className="empty-state">Loading…</p>}
      {!loading && items.length === 0 && <div className="card"><p className="empty-state">No savings goals yet.</p></div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
        {items.map((g) => {
          const progress = Number.isFinite(Number(g.progress_percentage)) ? Number(g.progress_percentage) : Math.min(100, (Number(g.saved_amount) / Number(g.target_amount)) * 100 || 0)
          const remaining = g.remaining_amount != null ? g.remaining_amount : Math.max(0, Number(g.target_amount) - Number(g.saved_amount))
          const status = g.goal_status || g.status || 'active'
          return (
            <div className="card" key={g.id}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <strong>{g.name}</strong>
                {g.target_date && <span style={{ fontSize: 12.5, color: 'var(--ink-soft)' }}>by {g.target_date}</span>}
              </div>
              <div style={{ marginTop: 10, fontSize: 14 }}>
                <Money value={g.saved_amount} sign="pos" /> of <Money value={g.target_amount} />
              </div>
              <div style={{ marginTop: 10, fontSize: 13, color: 'var(--ink-soft)' }}>
                <div>Remaining: <Money value={remaining} /></div>
                <div>Progress: {progress}%</div>
                <div>Status: {status}</div>
              </div>
              <div className="progress-track"><div className="progress-fill" style={{ width: `${Math.min(100, Math.max(0, progress))}%` }} /></div>
              <button className="btn secondary" style={{ marginTop: 14 }} onClick={() => remove(g.id)}>Remove</button>
            </div>
          )
        })}
      </div>
    </>
  )
}
