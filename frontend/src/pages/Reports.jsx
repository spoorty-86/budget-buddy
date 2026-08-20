import { useEffect, useState } from 'react'
import api from '../api'
import Money from '../components/Money'

export default function Reports() {
  const [reportType, setReportType] = useState('summary') // 'summary' | 'financial' | 'expenses' | 'savings'
  const [period, setPeriod] = useState('current_month') // 'current_month' | 'previous_month' | 'custom'
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [reportData, setReportData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState('')

  const fetchReport = async () => {
    setLoading(true)
    setError('')
    try {
      let endpoint = '/api/reports/summary/'
      if (reportType === 'financial') endpoint = '/api/reports/monthly/'
      if (reportType === 'expenses') endpoint = '/api/reports/expenses/'
      if (reportType === 'savings') endpoint = '/api/reports/savings/'

      const params = {}
      if (period !== 'custom') {
        params.period = period
      } else {
        if (startDate) params.start_date = startDate
        if (endDate) params.end_date = endDate
      }

      const { data } = await api.get(endpoint, { params })
      setReportData(data)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load report data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchReport()
  }, [reportType, period, startDate, endDate])

  const [exportFormat, setExportFormat] = useState('csv') // 'csv' | 'pdf'

  const handleExportReport = async (overrideFormat) => {
    const fmt = overrideFormat || exportFormat
    setDownloading(true)
    try {
      const typeMap = {
        summary: 'financial_summary',
        financial: 'financial_summary',
        expenses: 'expenses',
        savings: 'savings'
      }
      const rType = typeMap[reportType] || 'expenses'

      const params = {
        report_type: rType,
        format: fmt
      }
      if (period !== 'custom') {
        params.period = period
      } else {
        if (startDate) params.start_date = startDate
        if (endDate) params.end_date = endDate
      }

      const response = await api.get('/api/reports/export/', {
        params,
        responseType: 'blob'
      })

      const mimeType = fmt === 'pdf' ? 'application/pdf' : 'text/csv'
      const blob = new Blob([response.data], { type: mimeType })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${rType}_report.${fmt}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      let errMsg = `Failed to download ${fmt.toUpperCase()} report.`
      if (err.response?.data instanceof Blob) {
        try {
          const text = await err.response.data.text()
          const json = JSON.parse(text)
          if (json.detail) errMsg = json.detail
        } catch (_) {}
      } else if (err.response?.data?.detail) {
        errMsg = err.response.data.detail
      }
      setError(errMsg)
    } finally {
      setDownloading(false)
    }
  }

  // Helper values for stat metrics
  const totalIncomeVal = reportData?.['Financial Summary']?.total_income ?? reportData?.['Total Income'] ?? reportData?.['total_income'] ?? 0
  const totalExpenseVal = reportData?.['Financial Summary']?.total_expense ?? reportData?.['Total Expense'] ?? reportData?.['total_expense'] ?? 0
  const currentBalanceVal = reportData?.['Financial Summary']?.current_balance ?? reportData?.['Current Balance'] ?? reportData?.['current_balance'] ?? 0
  const totalSavingsVal = reportData?.['Financial Summary']?.total_savings ?? reportData?.['Total Savings'] ?? reportData?.['total_savings'] ?? reportData?.['total_saved_amount'] ?? 0
  const remainingBudgetVal = reportData?.['Financial Summary']?.remaining_budget ?? reportData?.['Remaining Budget'] ?? reportData?.['remaining_budget'] ?? 0

  return (
    <div className="reports-page">
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div>
          <h1>Financial Reports & Data Export</h1>
          <p className="page-sub">
            Generate, filter, and export comprehensive financial reports in CSV or PDF format.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <button
            className="btn-primary"
            onClick={() => handleExportReport('csv')}
            disabled={downloading || loading}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
          >
            {downloading ? 'Exporting…' : '📥 Export CSV'}
          </button>
          <button
            className="btn"
            onClick={() => handleExportReport('pdf')}
            disabled={downloading || loading}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#c4453b', color: '#fff' }}
          >
            {downloading ? 'Exporting…' : '📄 Export PDF'}
          </button>
        </div>
      </div>

      {/* Control Panel: Filters & Report Types */}
      <div className="card" style={{ marginBottom: 24, padding: 22 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, alignItems: 'end' }}>
          <div className="field">
            <label>Report Type</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="input-field"
            >
              <option value="summary">Combined Financial Summary</option>
              <option value="financial">Monthly Financial Report</option>
              <option value="expenses">Expense Report</option>
              <option value="savings">Savings Goal Report</option>
            </select>
          </div>

          <div className="field">
            <label>Date Range Filter</label>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="input-field"
            >
              <option value="current_month">Current Month</option>
              <option value="previous_month">Previous Month</option>
              <option value="custom">Custom Date Range</option>
            </select>
          </div>

          <div className="field">
            <label>Export Format</label>
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value)}
              className="input-field"
            >
              <option value="csv">CSV Format (.csv)</option>
              <option value="pdf">PDF Format (.pdf)</option>
            </select>
          </div>

          {period === 'custom' && (
            <>
              <div className="field">
                <label>Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="input-field"
                />
              </div>
              <div className="field">
                <label>End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="input-field"
                />
              </div>
            </>
          )}
        </div>
      </div>

      {error && <div className="error-banner" style={{ marginBottom: 20 }}>{error}</div>}

      {loading ? (
        <div className="card empty-state" style={{ padding: 40 }}>Loading report data…</div>
      ) : (
        reportData && (
          <div className="report-content" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* Overview Metric Cards */}
            {(reportData['Financial Summary'] || reportType === 'financial' || reportType === 'summary') && (
              <div className="stat-row" style={{ marginBottom: 0 }}>
                <div className="card metric-card income">
                  <span className="metric-label">Total Income</span>
                  <span className="metric-val text-success">
                    <Money value={totalIncomeVal} sign="pos" />
                  </span>
                </div>
                <div className="card metric-card expense">
                  <span className="metric-label">Total Expense</span>
                  <span className="metric-val text-danger">
                    <Money value={totalExpenseVal} sign="neg" />
                  </span>
                </div>
                <div className="card metric-card balance">
                  <span className="metric-label">Current Balance</span>
                  <span className="metric-val">
                    <Money value={currentBalanceVal} sign={Number(currentBalanceVal) >= 0 ? 'pos' : 'neg'} />
                  </span>
                </div>
                <div className="card metric-card savings">
                  <span className="metric-label">Total Savings</span>
                  <span className="metric-val text-primary">
                    <Money value={totalSavingsVal} sign="pos" />
                  </span>
                </div>
                <div className="card metric-card budget">
                  <span className="metric-label">Remaining Budget</span>
                  <span className="metric-val">
                    <Money value={remainingBudgetVal} sign={Number(remainingBudgetVal) < 0 ? 'neg' : undefined} />
                  </span>
                </div>
              </div>
            )}

            {/* Expense Report Table */}
            {(reportType === 'expenses' || (reportType === 'summary' && reportData['Expense Summary'])) && (
              <div className="card">
                <h3 style={{ marginBottom: 18, fontSize: 18 }}>Expense Report Details</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Expense Title</th>
                        <th>Category</th>
                        <th>Amount</th>
                        <th>Date</th>
                        <th>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(reportData.expenses || reportData['Expense Summary']?.recent_expenses || []).map((exp, idx) => {
                        const amt = exp['Amount'] ?? exp.amount
                        const categoryName = exp['Category'] || exp.category_name || 'UNCATEGORIZED'
                        return (
                          <tr key={idx}>
                            <td><strong>{exp['Expense Title'] || exp.title}</strong></td>
                            <td><span className="tag">{categoryName}</span></td>
                            <td style={{ fontWeight: 600 }}><Money value={amt} sign="neg" /></td>
                            <td>{exp['Date'] || exp.date_spent}</td>
                            <td className="text-muted">{exp['Description'] || exp.notes || '—'}</td>
                          </tr>
                        )
                      })}
                      {(!reportData.expenses || reportData.expenses.length === 0) && (!reportData['Expense Summary']?.recent_expenses?.length) && (
                        <tr>
                          <td colSpan="5" className="empty-state">No expenses found for this date range.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Savings Goal Report Table */}
            {(reportType === 'savings' || (reportType === 'summary' && reportData['Savings Summary'])) && (
              <div className="card">
                <h3 style={{ marginBottom: 18, fontSize: 18 }}>Savings Goal Report</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Goal Name</th>
                        <th>Target Amount</th>
                        <th>Saved Amount</th>
                        <th>Remaining Amount</th>
                        <th>Progress Percentage</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(reportData.goals || reportData['Savings Summary']?.goals || []).map((goal, idx) => {
                        const targetAmt = goal['Target Amount'] ?? goal.target_amount
                        const savedAmt = goal['Saved Amount'] ?? goal.saved_amount
                        const remainingAmt = goal['Remaining Amount'] ?? goal.remaining_amount
                        const progressPct = Number(goal['Progress Percentage'] ?? goal.progress_percentage ?? 0)

                        return (
                          <tr key={idx}>
                            <td><strong>{goal['Goal Name'] || goal.name}</strong></td>
                            <td><Money value={targetAmt} /></td>
                            <td style={{ color: 'var(--green)', fontWeight: 600 }}><Money value={savedAmt} sign="pos" /></td>
                            <td><Money value={remainingAmt} /></td>
                            <td>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 160 }}>
                                <span style={{ fontWeight: 600, fontSize: 13, minWidth: 36 }}>{progressPct}%</span>
                                <div className="progress-track" style={{ flex: 1, marginTop: 0 }}>
                                  <div className="progress-fill" style={{ width: `${Math.min(100, Math.max(0, progressPct))}%` }} />
                                </div>
                              </div>
                            </td>
                          </tr>
                        )
                      })}
                      {(!reportData.goals || reportData.goals.length === 0) && (!reportData['Savings Summary']?.goals?.length) && (
                        <tr>
                          <td colSpan="5" className="empty-state">No savings goals found.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )
      )}
    </div>
  )
}
