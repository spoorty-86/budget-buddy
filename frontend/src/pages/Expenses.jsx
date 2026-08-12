import { useEffect, useState } from 'react'
import api from '../api'
import Money from '../components/Money'
import { formatApiError } from '../utils/errors'

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

  const [editingId, setEditingId] = useState(null)
  const [alertBanner, setAlertBanner] = useState(null)

  function handleEdit(item) {
    setError('')
    setAlertBanner(null)
    setEditingId(item.id)
    setForm({
      title: item.title || '',
      amount: item.amount || '',
      category: item.category || '',
      date_spent: item.date_spent || new Date().toISOString().slice(0, 10),
      notes: item.notes || '',
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
    setAlertBanner(null)

    // Client-side required field validation
    if (!form.title.trim()) {
      setError('Expense Title is required.')
      return
    }
    if (!form.amount || Number(form.amount) <= 0) {
      setError('Amount is required and must be greater than zero.')
      return
    }
    if (!form.date_spent) {
      setError('Date Spent is required.')
      return
    }

    const selectedCatId = form.category
    const selectedCategoryObj = categories.find(c => String(c.id) === String(selectedCatId))
    const selectedCatName = selectedCategoryObj ? selectedCategoryObj.name : null

    try {
      if (editingId) {
        await api.put(`/api/finance/expenses/${editingId}/`, { ...form, category: form.category || null })
      } else {
        await api.post('/api/finance/expenses/', { ...form, category: form.category || null })
      }
      setForm(empty)
      setEditingId(null)
      load()

      const alertsRes = await api.get('/api/finance/budgets/alerts/')
      const catAlert = alertsRes.data.find(a => {
        const isSelectedCat = (selectedCatId && String(a.category) === String(selectedCatId)) ||
          (selectedCatName && (a['Budget Category'] || '').toUpperCase() === selectedCatName.toUpperCase())
        const isAlertState = a['Alert Level'] && a['Alert Level'] !== 'Normal'
        return isSelectedCat && isAlertState
      })

      if (catAlert) {
        setAlertBanner({
          title: catAlert['Alert Level'] || 'Budget Alert',
          message: catAlert['Alert Message'] || `Your ${selectedCatName || 'category'} Budget has been exceeded.`,
          notification_type: catAlert['Alert Level'] === 'Budget Exceeded Alert' ? 'ERROR' : 'WARNING',
        })
      } else {
        const notifsRes = await api.get('/api/notifications/')
        const recentAlert = notifsRes.data.find(n => {
          if (n.is_read || n.title === 'Expense Added') return false
          const isAlert = n.notification_type === 'ERROR' || n.notification_type === 'WARNING' || n.title.includes('Alert') || n.title.includes('Warning') || n.title.includes('Exceeded')
          return isAlert
        })
        if (recentAlert) {
          setAlertBanner(recentAlert)
        }
      }
    } catch (err) {
      const errMsg = formatApiError(err, `Could not ${editingId ? 'update' : 'save'} that expense. Please check your inputs and try again.`)
      setError(errMsg)
    }
  }

  async function remove(id) {
    if (editingId === id) {
      handleCancel()
    }
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

      {alertBanner && (
        <div
          className="alert-banner"
          style={{
            background: alertBanner.notification_type === 'ERROR' ? '#fef2f2' : '#fffbeb',
            border: `1px solid ${alertBanner.notification_type === 'ERROR' ? '#fca5a5' : '#fcd34d'}`,
            color: alertBanner.notification_type === 'ERROR' ? '#991b1b' : '#92400e',
            padding: '12px 16px',
            borderRadius: '8px',
            marginBottom: '16px',
            fontWeight: '500',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            🚨 <strong>{alertBanner.title}</strong>: {alertBanner.message}
          </div>
          <button
            type="button"
            onClick={() => setAlertBanner(null)}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '18px',
              cursor: 'pointer',
              color: 'inherit',
              lineHeight: 1,
              padding: '0 4px',
            }}
            title="Dismiss alert"
          >
            &times;
          </button>
        </div>
      )}

      <form
        className="form-row"
        onSubmit={handleSubmit}
        style={editingId ? { borderColor: 'var(--red)', boxShadow: '0 0 0 2px rgba(196, 69, 59, 0.2)' } : {}}
      >
        <div className="field">
          <label>{editingId ? 'Editing Title' : 'Title'}</label>
          <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Weekly groceries" required />
        </div>
        <div className="field">
          <label>Amount</label>
          <input type="number" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="0.00" required />
        </div>
        <div className="field">
          <label>Category</label>
          <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            <option value="">Select category...</option>
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
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="btn" type="submit">
            {editingId ? '✏️ Update Expense' : '+ Add Expense'}
          </button>
          {editingId && (
            <button className="btn secondary" type="button" onClick={handleCancel}>
              Cancel
            </button>
          )}
        </div>
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
            <thead>
              <tr>
                <th>Title</th>
                <th>Category</th>
                <th>Date</th>
                <th className="num">Amount</th>
                <th className="num">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id} style={editingId === i.id ? { background: 'var(--red-soft)' } : {}}>
                  <td><strong>{i.title}</strong></td>
                  <td>{i.category_name ? <span className="tag">{i.category_name}</span> : '—'}</td>
                  <td>{i.date_spent}</td>
                  <td className="num"><Money value={i.amount} sign="neg" /></td>
                  <td className="num" style={{ whiteSpace: 'nowrap' }}>
                    <button
                      className="btn secondary"
                      style={{ marginRight: 6, padding: '4px 10px', fontSize: 13 }}
                      onClick={() => handleEdit(i)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn secondary"
                      style={{ padding: '4px 10px', fontSize: 13, color: 'var(--red)', borderColor: 'var(--red-soft)' }}
                      onClick={() => remove(i.id)}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
              <tr>
                <td colSpan={3} style={{ fontWeight: 600 }}>Total Expense</td>
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
