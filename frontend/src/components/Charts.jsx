import { useState } from 'react'

// 1. Line Chart for Monthly Expense Trends
export function ExpenseLineChart({ data }) {
  const [hoveredIdx, setHoveredIdx] = useState(null)

  if (!data || data.length === 0) {
    return <p className="empty-state" style={{ padding: '30px 0' }}>No expense trend data available.</p>
  }

  const validData = data.filter((d) => d && d.month_num >= 1 && d.month_num <= 12)
  const chartData = validData.length > 0 ? validData : data

  const maxVal = Math.max(...chartData.map((d) => Number(d.expense || d.total_expense || d.total || 0)), 100)

  const width = 540
  const height = 200
  const paddingLeft = 45
  const paddingRight = 20
  const paddingTop = 20
  const paddingBottom = 35

  const chartW = width - paddingLeft - paddingRight
  const chartH = height - paddingTop - paddingBottom

  const points = chartData.map((item, idx) => {
    const x = paddingLeft + (idx / Math.max(1, chartData.length - 1)) * chartW
    const expVal = Number(item.expense || item.total_expense || item.total || 0)
    const y = paddingTop + chartH - (expVal / maxVal) * chartH
    return { x, y, val: expVal, label: item.month ? item.month.substring(0, 3) : `M${idx + 1}` }
  })

  // Generate smooth cubic bezier SVG path
  const pathD = points.reduce((acc, point, idx, arr) => {
    if (idx === 0) return `M ${point.x} ${point.y}`
    const prev = arr[idx - 1]
    const controlX = (prev.x + point.x) / 2
    return `${acc} C ${controlX} ${prev.y}, ${controlX} ${point.y}, ${point.x} ${point.y}`
  }, '')

  // Area path for gradient fill under the line
  const areaD = points.length > 0
    ? `${pathD} L ${points[points.length - 1].x} ${height - paddingBottom} L ${points[0].x} ${height - paddingBottom} Z`
    : ''

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="xMinYMin meet">
        <defs>
          <linearGradient id="expenseLineGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#ef4444" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {[0, 0.33, 0.66, 1].map((pct, idx) => {
          const y = paddingTop + chartH - pct * chartH
          const val = Math.round(maxVal * pct)
          return (
            <g key={idx}>
              <line x1={paddingLeft} y1={y} x2={width - paddingRight} y2={y} stroke="#e2e8f0" strokeDasharray="3 3" />
              <text x={paddingLeft - 8} y={y + 4} textAnchor="end" fontSize="10" fill="#64748b">
                ₹{val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val}
              </text>
            </g>
          )
        })}

        {/* Gradient area fill */}
        <path d={areaD} fill="url(#expenseLineGrad)" />

        {/* Smooth line */}
        <path d={pathD} fill="none" stroke="#ef4444" strokeWidth="3" strokeLinecap="round" />

        {/* Data points */}
        {points.map((pt, idx) => (
          <g key={idx} onMouseEnter={() => setHoveredIdx(idx)} onMouseLeave={() => setHoveredIdx(null)}>
            <circle
              cx={pt.x}
              cy={pt.y}
              r={hoveredIdx === idx ? 6 : 4}
              fill="#ffffff"
              stroke="#ef4444"
              strokeWidth="2.5"
              style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
            />
            {/* Month label */}
            <text x={pt.x} y={height - 10} textAnchor="middle" fontSize="11" fontWeight="600" fill="#475569">
              {pt.label}
            </text>

            {/* Hover tooltip */}
            {hoveredIdx === idx && (
              <g>
                <rect
                  x={Math.max(10, Math.min(width - 90, pt.x - 40))}
                  y={Math.max(5, pt.y - 32)}
                  width="80"
                  height="24"
                  rx="6"
                  fill="#1e293b"
                  opacity="0.9"
                />
                <text
                  x={Math.max(50, Math.min(width - 50, pt.x))}
                  y={Math.max(21, pt.y - 16)}
                  textAnchor="middle"
                  fontSize="11"
                  fontWeight="700"
                  fill="#ffffff"
                >
                  ₹{pt.val.toLocaleString()}
                </text>
              </g>
            )}
          </g>
        ))}
      </svg>
    </div>
  )
}


// 2. Pie / Doughnut Chart for Category-wise Expenses
export function CategoryDonutChart({ data }) {
  const [hoveredIdx, setHoveredIdx] = useState(null)

  if (!data || data.length === 0) {
    return <p className="empty-state" style={{ padding: '30px 0' }}>No category expense data available.</p>
  }

  const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#64748b', '#ef4444']

  const totalSum = data.reduce((sum, item) => sum + Number(item.total || item.total_expense || 0), 0)

  if (totalSum <= 0) {
    return <p className="empty-state" style={{ padding: '30px 0' }}>No category expenses recorded for period.</p>
  }

  const size = 180
  const center = size / 2
  const outerRadius = 75
  const innerRadius = 48

  let cumulativeAngle = 0
  const slices = data.map((item, idx) => {
    const name = item.category__name || item.category || 'Uncategorized'
    const value = Number(item.total || item.total_expense || 0)
    const pct = (value / totalSum) * 100
    const angle = (value / totalSum) * 2 * Math.PI

    const startAngle = cumulativeAngle
    const endAngle = cumulativeAngle + angle
    cumulativeAngle = endAngle

    const x1Outer = center + outerRadius * Math.cos(startAngle)
    const y1Outer = center + outerRadius * Math.sin(startAngle)
    const x2Outer = center + outerRadius * Math.cos(endAngle)
    const y2Outer = center + outerRadius * Math.sin(endAngle)

    const x1Inner = center + innerRadius * Math.cos(endAngle)
    const y1Inner = center + innerRadius * Math.sin(endAngle)
    const x2Inner = center + innerRadius * Math.cos(startAngle)
    const y2Inner = center + innerRadius * Math.sin(startAngle)

    const largeArcFlag = angle > Math.PI ? 1 : 0

    const pathD = `
      M ${x1Outer} ${y1Outer}
      A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${x2Outer} ${y2Outer}
      L ${x1Inner} ${y1Inner}
      A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${x2Inner} ${y2Inner}
      Z
    `

    return {
      name,
      value,
      pct: pct.toFixed(1),
      color: COLORS[idx % COLORS.length],
      pathD,
    }
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {slices.map((slice, idx) => (
            <path
              key={idx}
              d={slice.pathD}
              fill={slice.color}
              opacity={hoveredIdx === null || hoveredIdx === idx ? 1 : 0.45}
              style={{
                cursor: 'pointer',
                transition: 'transform 0.15s ease, opacity 0.15s ease',
                transform: hoveredIdx === idx ? 'scale(1.04)' : 'scale(1)',
                transformOrigin: `${center}px ${center}px`
              }}
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              <title>{`${slice.name}: ₹${slice.value.toLocaleString()} (${slice.pct}%)`}</title>
            </path>
          ))}
        </svg>

        {/* Center Total Display */}
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
            pointerEvents: 'none'
          }}
        >
          <div style={{ fontSize: 10, color: 'var(--ink-soft)', textTransform: 'uppercase', fontWeight: 600 }}>Total</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--ink)' }}>
            ₹{totalSum >= 100000 ? `${(totalSum / 1000).toFixed(0)}k` : totalSum.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Category Legend Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 8, width: '100%' }}>
        {slices.map((slice, idx) => (
          <div
            key={idx}
            onMouseEnter={() => setHoveredIdx(idx)}
            onMouseLeave={() => setHoveredIdx(null)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justify: 'space-between',
              padding: '4px 8px',
              borderRadius: 6,
              background: hoveredIdx === idx ? '#f1f5f9' : 'transparent',
              cursor: 'pointer',
              fontSize: 12
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, overflow: 'hidden' }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: slice.color, flexShrink: 0 }} />
              <span style={{ fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{slice.name}</span>
            </div>
            <span style={{ fontWeight: 700, color: 'var(--ink-soft)', marginLeft: 6 }}>{slice.pct}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}


// 3. Bar Chart Comparing Income and Expenses
export function IncomeExpenseBarChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="empty-state" style={{ padding: '30px 0' }}>No comparison data available.</p>
  }

  const validData = data.filter((d) => d && d.month_num >= 1 && d.month_num <= 12)
  const chartData = validData.length > 0 ? validData : data

  const maxVal = Math.max(
    ...chartData.map((d) => Math.max(Number(d.income || 0), Number(d.expense || 0))),
    100
  )

  const height = 180
  const barWidth = 11
  const gap = 3
  const groupGap = 16
  const totalWidth = Math.max(500, chartData.length * (barWidth * 2 + gap + groupGap) + 50)

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <svg width="100%" height={height + 40} viewBox={`0 0 ${totalWidth} ${height + 40}`} preserveAspectRatio="xMinYMin meet">
        {/* Y Grid lines */}
        {[0, 0.33, 0.66, 1].map((pct, idx) => {
          const y = height - pct * (height - 25) + 15
          const val = Math.round(maxVal * pct)
          return (
            <g key={idx}>
              <line x1="45" y1={y} x2={totalWidth - 15} y2={y} stroke="#e2e8f0" strokeDasharray="3 3" />
              <text x="40" y={y + 4} textAnchor="end" fontSize="10" fill="#64748b">
                ₹{val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val}
              </text>
            </g>
          )
        })}

        {/* Dual Bars */}
        {chartData.map((item, idx) => {
          const inc = Number(item.income || 0)
          const exp = Number(item.expense || 0)
          const incH = (inc / maxVal) * (height - 25)
          const expH = (exp / maxVal) * (height - 25)

          const groupX = 55 + idx * (barWidth * 2 + gap + groupGap)
          const incY = height - incH + 15
          const expY = height - expH + 15

          const shortMonth = item.month ? item.month.substring(0, 3) : `M${idx + 1}`

          return (
            <g key={idx}>
              <rect x={groupX} y={incY} width={barWidth} height={Math.max(incH, 2)} fill="#10b981" rx="3">
                <title>{`${item.month}: Income ₹${inc.toLocaleString()}`}</title>
              </rect>
              <rect x={groupX + barWidth + gap} y={expY} width={barWidth} height={Math.max(expH, 2)} fill="#ef4444" rx="3">
                <title>{`${item.month}: Expense ₹${exp.toLocaleString()}`}</title>
              </rect>
              <text x={groupX + barWidth + gap / 2} y={height + 30} textAnchor="middle" fontSize="11" fontWeight="600" fill="#475569">
                {shortMonth}
              </text>
            </g>
          )
        })}
      </svg>

      {/* Legend */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 20, marginTop: 6, fontSize: 12, fontWeight: 600 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 12, height: 12, background: '#10b981', borderRadius: 3 }} />
          Income
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 12, height: 12, background: '#ef4444', borderRadius: 3 }} />
          Expense
        </div>
      </div>
    </div>
  )
}


// 4. Progress Ring Visualization for Savings Goals
export function SavingsRadialProgress({ goal }) {
  const saved = Number(goal?.saved_amount || 0)
  const target = Number(goal?.target_amount || 1)
  const pct = Math.min(100, Math.round((saved / target) * 100))

  const size = 90
  const strokeWidth = 8
  const center = size / 2
  const radius = center - strokeWidth
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (pct / 100) * circumference

  const ringColor = pct >= 100 ? '#10b981' : '#8b5cf6'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: 12, borderRadius: 10, background: '#f8fafc', border: '1px solid var(--line)' }}>
      <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
        <svg width={size} height={size}>
          {/* Background circle */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={ringColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.5s ease', transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
          />
        </svg>
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
            fontSize: 13,
            fontWeight: 700,
            color: ringColor
          }}
        >
          {pct}%
        </div>
      </div>

      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--ink)' }}>🎯 {goal.name}</div>
        <div style={{ fontSize: 12.5, color: 'var(--ink-soft)', marginTop: 2 }}>
          <strong style={{ color: ringColor }}>₹{saved.toLocaleString()}</strong> saved of ₹{target.toLocaleString()}
        </div>
        {goal.target_date && (
          <div style={{ fontSize: 11, color: 'var(--ink-soft)', marginTop: 4, opacity: 0.8 }}>
            Target Date: {goal.target_date}
          </div>
        )}
      </div>
    </div>
  )
}


// 5. Budget Utilization Gauge Meter Visualization
export function BudgetGaugeMeter({ totalBudget, budgetExpensesTotal }) {
  const limit = Number(totalBudget || 0)
  const spent = Number(budgetExpensesTotal || 0)
  const pct = limit > 0 ? Math.min(150, Math.round((spent / limit) * 100)) : 0

  const isOver = pct > 100
  const isWarning = pct >= 80 && pct <= 100

  const gaugeColor = isOver ? '#ef4444' : isWarning ? '#f59e0b' : '#10b981'

  const size = 160
  const strokeWidth = 14
  const center = size / 2
  const radius = center - strokeWidth
  // Semi-circle circumference
  const arcLength = Math.PI * radius
  const dashOffset = arcLength - (Math.min(100, pct) / 100) * arcLength

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '16px 12px' }}>
      <div style={{ position: 'relative', width: size, height: size / 2 + 20 }}>
        <svg width={size} height={size / 2 + 10}>
          {/* Background arc */}
          <path
            d={`M ${strokeWidth} ${center} A ${radius} ${radius} 0 0 1 ${size - strokeWidth} ${center}`}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
          {/* Active utilization arc */}
          <path
            d={`M ${strokeWidth} ${center} A ${radius} ${radius} 0 0 1 ${size - strokeWidth} ${center}`}
            fill="none"
            stroke={gaugeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={arcLength}
            strokeDashoffset={dashOffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.5s ease' }}
          />
        </svg>

        {/* Center Percentage Display */}
        <div
          style={{
            position: 'absolute',
            bottom: 5,
            left: '50%',
            transform: 'translateX(-50%)',
            textAlign: 'center'
          }}
        >
          <div style={{ fontSize: 22, fontWeight: 800, color: gaugeColor, lineHeight: 1 }}>
            {pct}%
          </div>
          <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: 'uppercase', color: 'var(--ink-soft)', marginTop: 2 }}>
            {isOver ? '⚠️ Over Budget' : isWarning ? '⚡ High Usage' : '✅ Within Limit'}
          </div>
        </div>
      </div>

      <div style={{ textAlign: 'center', marginTop: 8, fontSize: 12.5, color: 'var(--ink-soft)' }}>
        <strong>₹{spent.toLocaleString()}</strong> spent of <strong>₹{limit.toLocaleString()}</strong> limit
      </div>
    </div>
  )
}
