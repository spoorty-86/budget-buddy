import { useEffect, useState } from 'react'
import api from '../api'
import Money from '../components/Money'

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
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    api.get('/api/finance/incomes/').then(({ data }) => setItems(data)).finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    try {
      await api.post('/api/finance/incomes/', form)
      setForm(empty)
      load()
    } catch {
      setError('Could not save that income entry. Check the fields and try again.')
    }
  }

  async function remove(id) {
    await api.delete(`/api/finance/incomes/${id}/`)
    load()
  }

  const total = items.reduce((sum, i) => sum + Number(i.amount), 0)

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Incomes</h1>
          <p className="page-sub">Every dollar coming in.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form className="form-row" onSubmit={handleSubmit}>
        <div className="field">
          <label>Title</label>
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
        <button className="btn" type="submit">Add income</button>
      </form>

      <div className="card">
        {loading && <p className="empty-state">Loading…</p>}
        {!loading && items.length === 0 && <p className="empty-state">No income logged yet.</p>}
        {!loading && items.length > 0 && (
          <table className="ledger">
            <thead><tr><th>Title</th><th>Source</th><th>Date</th><th>Description</th><th className="num">Amount</th><th></th></tr></thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id}>
                  <td>{i.title}</td>
                  <td>{i.source}</td>
                  <td>{i.income_date}</td>
                  <td>{i.description}</td>
                  <td className="num"><Money value={i.amount} sign="pos" /></td>
                  <td className="num">
                    <button className="btn secondary" onClick={() => remove(i.id)}>Remove</button>
                  </td>
                </tr>
              ))}
              <tr>
                <td colSpan={4} style={{ fontWeight: 600 }}>Total</td>
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
