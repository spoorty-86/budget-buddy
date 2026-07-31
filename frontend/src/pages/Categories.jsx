import { useEffect, useState } from 'react'
import api from '../api'

export default function Categories() {
  const [items, setItems] = useState([])
  const [form, setForm] = useState({ name: '', icon: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    api.get('/api/finance/categories/').then(({ data }) => setItems(data)).finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    try {
      await api.post('/api/finance/categories/', form)
      setForm({ name: '', icon: '' })
      load()
    } catch {
      setError('Could not add that category — the name may already exist.')
    }
  }

  async function remove(id) {
    await api.delete(`/api/finance/categories/${id}/`)
    load()
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Categories</h1>
          <p className="page-sub">Group expenses so budgets and reports make sense.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form className="form-row" onSubmit={handleSubmit}>
        <div className="field">
          <label>Name</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Groceries"
            required
          />
        </div>
        <div className="field">
          <label>Icon (optional)</label>
          <input
            value={form.icon}
            onChange={(e) => setForm({ ...form, icon: e.target.value })}
            placeholder="cart"
          />
        </div>
        <button className="btn" type="submit">Add category</button>
      </form>

      <div className="card">
        {loading && <p className="empty-state">Loading…</p>}
        {!loading && items.length === 0 && <p className="empty-state">No categories yet. Add your first one above.</p>}
        {!loading && items.length > 0 && (
          <table className="ledger">
            <thead><tr><th>Name</th><th>Icon</th><th></th></tr></thead>
            <tbody>
              {items.map((c) => (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td><span className="tag">{c.icon || 'tag'}</span></td>
                  <td className="num">
                    <button className="btn secondary" onClick={() => remove(c.id)}>Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
