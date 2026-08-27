import { useEffect, useState } from 'react'
import api from '../api'
import Money from '../components/Money'
import { formatApiError } from '../utils/errors'

const now = new Date()
const empty = { category: '', monthly_limit: '', month: now.getMonth() + 1, year: now.getFullYear() }

export default function Budgets() {
  const [items, setItems] = useState([])
  const [categories, setCategories] = useState([])
  const [form, setForm] = useState(empty)
  const [editingId, setEditingId] = useState(null)
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

  function handleEdit(b) {
    setError('')
    setEditingId(b.id)
    setForm({
      category: b.category || '',
      monthly_limit: b.monthly_limit || b.budget_amount || '',
      month: b.month || now.getMonth() + 1,
      year: b.year || now.getFullYear(),
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function handleCancel() {
    setForm(empty)
    setEditingId(null)
    setError('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    // Client-side required field validation
    if (!form.category) {
      setError('Please select a Category for this budget.')
      return
    }
    if (!form.monthly_limit || Number(form.monthly_limit) <= 0) {
      setError('Monthly Budget Limit is required and must be greater than zero.')
      return
    }

    try {
      const payload = {
        ...form,
        budget_amount: form.monthly_limit,
      }

      const existing = items.find(
        (b) => String(b.category) === String(form.category) && Number(b.month) === Number(form.month) && Number(b.year) === Number(form.year)
      )

      if (editingId) {
        await api.put(`/api/finance/budgets/${editingId}/`, payload)
      } else if (existing) {
        await api.put(`/api/finance/budgets/${existing.id}/`, payload)
      } else {
        await api.post('/api/finance/budgets/', payload)
      }
      setForm(empty)
      setEditingId(null)
      load()
    } catch (err) {
      const errMsg = formatApiError(err, `Could not ${editingId ? 'update' : 'save'} that budget. Please check inputs and try again.`)
      setError(errMsg)
    }
  }

  async function remove(id) {
    if (editingId === id) {
      handleCancel()
    }
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

      <form
        className="form-row"
        onSubmit={handleSubmit}
        style={editingId ? { borderColor: 'var(--gold)', boxShadow: '0 0 0 2px rgba(185, 139, 46, 0.2)' } : {}}
      >
        <div className="field">
          <label>{editingId ? 'Editing Category' : 'Category'}</label>
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
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="btn" type="submit">
            {editingId ? '✏️ Update Budget' : '+ Add Budget'}
          </button>
          {editingId && (
            <button className="btn secondary" type="button" onClick={handleCancel}>
              Cancel
            </button>
          )}
        </div>
      </form>

      {loading && <p className="empty-state">Loading…</p>}
      {!loading && items.length === 0 && <div className="card"><p className="empty-state">No budgets set yet.</p></div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
        {items.map((b) => {
          const pct = Math.min(100, (Number(b.spent) / Number(b.monthly_limit)) * 100 || 0)
          const over = Number(b.spent) > Number(b.monthly_limit)
          const isEditing = editingId === b.id

          return (
            <div
              className="card"
              key={b.id}
              style={isEditing ? { borderColor: 'var(--gold)', boxShadow: '0 0 0 2px rgba(185, 139, 46, 0.2)' } : {}}
            >
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
              <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
                <button
                  className="btn secondary"
                  style={{ flex: 1, padding: '6px 12px', fontSize: 13 }}
                  onClick={() => handleEdit(b)}
                >
                  Edit
                </button>
                <button
                  className="btn secondary"
                  style={{ flex: 1, padding: '6px 12px', fontSize: 13, color: 'var(--red)', borderColor: 'var(--red-soft)' }}
                  onClick={() => remove(b.id)}
                >
                  Remove
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </>
  )
}
