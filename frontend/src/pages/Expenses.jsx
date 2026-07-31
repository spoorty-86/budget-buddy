import { useEffect, useState } from 'react'
import api from '../api'
import Money from '../components/Money'

const empty = { title: '', amount: '', category: '', date_spent: new Date().toISOString().slice(0, 10), notes: '' }

export default function Expenses() {
  const [items, setItems] = useState([])
  const [categories, setCategories] = useState([])
  const [form, setForm] = useState(empty)
  const [filter, setFilter] = useState({ category: '', sort: 'latest' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)

  function buildQuery(params) {
    const search = new URLSearchParams()
    if (params.category) search.set('category', params.category)
    if (params.sort) search.set('sort', params.sort)
    return search.toString() ? `?${search.toString()}` : ''
  }

  async function load() {
    setLoading(true)
    const query = buildQuery(filter)

    try {
      const [e, c, t] = await Promise.all([
        api.get(`/api/finance/expenses/${query}`),
        api.get('/api/finance/categories/'),
        api.get(`/api/finance/expenses/total/${query}`),
      ])
      setItems(e.data)
      setCategories(c.data)
      setTotal(t.data.total)
    } catch {
      setError('Could not load expenses. Please refresh.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [filter])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    try {
      await api.post('/api/finance/expenses/', { ...form, category: form.category || null })
      setForm(empty)
      load()
    } catch {
      setError('Could not save that expense. Check the fields and try again.')
    }
  }

  async function remove(id) {
    await api.delete(`/api/finance/expenses/${id}/`)
    load()
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Expenses</h1>
          <p className="page-sub">Everything that left your pocket.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form className="form-row" onSubmit={handleSubmit}>
        <div className="field">
          <label>Title</label>
          <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Weekly groceries" required />
        </div>
        <div className="field">
          <label>Amount</label>
          <input type="number" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="0.00" required />
        </div>
        <div className="field">
          <label>Category</label>
          <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Date spent</label>
          <input type="date" value={form.date_spent} onChange={(e) => setForm({ ...form, date_spent: e.target.value })} required />
        </div>
        <div className="field">
          <label>Notes</label>
          <input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Optional" />
        </div>
        <button className="btn" type="submit">Add expense</button>
      </form>

      <div className="filter-row">
        <div className="field">
          <label>Filter by category</label>
          <select value={filter.category} onChange={(e) => setFilter({ ...filter, category: e.target.value })}>
            <option value="">All categories</option>
            <option value="UNCATEGORIZED">Uncategorized</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Sort by</label>
          <select value={filter.sort} onChange={(e) => setFilter({ ...filter, sort: e.target.value })}>
            <option value="latest">Latest expenses first</option>
            <option value="oldest">Oldest expenses first</option>
            <option value="highest">Highest amount first</option>
            <option value="lowest">Lowest amount first</option>
          </select>
        </div>
      </div>

      <div className="card">
        {loading && <p className="empty-state">Loading…</p>}
        {!loading && items.length === 0 && <p className="empty-state">No expenses logged yet.</p>}
        {!loading && items.length > 0 && (
          <table className="ledger">
            <thead><tr><th>Title</th><th>Category</th><th>Date</th><th className="num">Amount</th><th></th></tr></thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id}>
                  <td>{i.title}</td>
                  <td>{i.category_name ? <span className="tag">{i.category_name}</span> : '—'}</td>
                  <td>{i.date_spent}</td>
                  <td className="num"><Money value={i.amount} sign="neg" /></td>
                  <td className="num">
                    <button className="btn secondary" onClick={() => remove(i.id)}>Remove</button>
                  </td>
                </tr>
              ))}
              <tr>
                <td colSpan={3} style={{ fontWeight: 600 }}>Total</td>
                <td className="num"><Money value={total} sign="neg" /></td>
                <td></td>
              </tr>
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
