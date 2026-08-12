import { useEffect, useState } from 'react'
import api from '../api'
import Money from '../components/Money'
import { formatApiError } from '../utils/errors'

const empty = {
  title: '',
  source: 'SALARY',
  amount: '',
  income_date: new Date().toISOString().slice(0, 10),
  description: '',
}

export default function Incomes() {
  const [items, setItems] = useState([])
  const [form, setForm] = useState(empty)
  const [editingId, setEditingId] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    api.get('/api/finance/incomes/').then(({ data }) => setItems(data)).finally(() => setLoading(false))
  }

  useEffect(load, [])

  function handleEdit(item) {
    setError('')
    setEditingId(item.id)
    setForm({
      title: item.title || '',
      source: item.source || 'SALARY',
      amount: item.amount || '',
      income_date: item.income_date || new Date().toISOString().slice(0, 10),
      description: item.description || '',
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
    if (!form.title.trim()) {
      setError('Income Title is required.')
      return
    }
    if (!form.amount || Number(form.amount) <= 0) {
      setError('Amount is required and must be greater than zero.')
      return
    }
    if (!form.income_date) {
      setError('Income Date is required.')
      return
    }

    try {
      if (editingId) {
        await api.put(`/api/finance/incomes/${editingId}/`, form)
      } else {
        await api.post('/api/finance/incomes/', form)
      }
      setForm(empty)
      setEditingId(null)
      load()
    } catch (err) {
      const errMsg = formatApiError(err, `Could not ${editingId ? 'update' : 'save'} that income entry. Please check your inputs and try again.`)
      setError(errMsg)
    }
  }

  async function remove(id) {
    if (editingId === id) {
      handleCancel()
    }
    await api.delete(`/api/finance/incomes/${id}/`)
    load()
  }

  const total = items.reduce((sum, i) => sum + Number(i.amount), 0)

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Incomes</h1>
          <p className="page-sub">Every rupee coming in.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form
        className="form-row"
        onSubmit={handleSubmit}
        style={editingId ? { borderColor: 'var(--green)', boxShadow: '0 0 0 2px rgba(23, 121, 91, 0.2)' } : {}}
      >
        <div className="field">
          <label>{editingId ? 'Editing Title' : 'Title'}</label>
          <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Salary payment" required />
        </div>
        <div className="field">
          <label>Source</label>
          <select value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} required>
            <option value="SALARY">Salary</option>
            <option value="POCKET_MONEY">Pocket Money</option>
            <option value="SCHOLARSHIP">Scholarship</option>
            <option value="FREELANCING">Freelancing</option>
            <option value="BUSINESS">Business</option>
            <option value="OTHER">Other</option>
          </select>
        </div>
        <div className="field">
          <label>Amount</label>
          <input type="number" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="0.00" required />
        </div>
        <div className="field">
          <label>Income date</label>
          <input type="date" value={form.income_date} onChange={(e) => setForm({ ...form, income_date: e.target.value })} required />
        </div>
        <div className="field">
          <label>Description</label>
          <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Optional" />
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="btn" type="submit">
            {editingId ? '✏️ Update Income' : '+ Add Income'}
          </button>
          {editingId && (
            <button className="btn secondary" type="button" onClick={handleCancel}>
              Cancel
            </button>
          )}
        </div>
      </form>

      <div className="card">
        {loading && <p className="empty-state">Loading…</p>}
        {!loading && items.length === 0 && <p className="empty-state">No income logged yet.</p>}
        {!loading && items.length > 0 && (
          <table className="ledger">
            <thead>
              <tr>
                <th>Title</th>
                <th>Source</th>
                <th>Date</th>
                <th>Description</th>
                <th className="num">Amount</th>
                <th className="num">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id} style={editingId === i.id ? { background: 'var(--green-soft)' } : {}}>
                  <td><strong>{i.title}</strong></td>
                  <td><span className="tag">{i.source}</span></td>
                  <td>{i.income_date}</td>
                  <td>{i.description || '—'}</td>
                  <td className="num"><Money value={i.amount} sign="pos" /></td>
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
                <td colSpan={4} style={{ fontWeight: 600 }}>Total Income</td>
                <td className="num"><Money value={total} sign="pos" /></td>
                <td></td>
              </tr>
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
