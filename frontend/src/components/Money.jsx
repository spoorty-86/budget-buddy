export default function Money({ value, sign }) {
  const n = Number(value || 0)
  const formatted = n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  const cls = sign === 'pos' ? 'pos' : sign === 'neg' ? 'neg' : ''
  const prefix = sign === 'pos' ? '+' : sign === 'neg' ? '-' : ''
  return <span className={`amount ${cls}`}>{prefix}₹{formatted}</span>
}
