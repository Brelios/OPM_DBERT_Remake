import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const COLORS = ['#ef4444', '#fb923c', '#a78bfa', '#4ade80', '#10b981']
const LABELS = ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const d = payload[0].payload
    return (
      <div style={{
        background: '#16161f', border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '10px', padding: '0.6rem 1rem', fontSize: '0.85rem'
      }}>
        <div style={{ fontWeight: 700, color: payload[0].fill }}>{d.label}</div>
        <div style={{ color: '#8888aa' }}>{d.count} reviews ({d.percentage}%)</div>
      </div>
    )
  }
  return null
}

export default function SentimentPieChart({ data }) {
  const filtered = data.filter(d => d.count > 0)

  if (!filtered.length) {
    return <div className="empty-state"><p>No sentiment data available.</p></div>
  }

  return (
    <div className="chart-container">
      <ResponsiveContainer width={200} height={200}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={90}
            paddingAngle={3}
            dataKey="count"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index]} stroke="transparent" />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      <div className="chart-legend">
        {data.map((entry, i) => (
          <div key={i} className="legend-item">
            <div className="legend-dot" style={{ background: COLORS[i] }} />
            <span className="legend-label">{LABELS[i]}</span>
            <span className="legend-value" style={{ color: COLORS[i] }}>{entry.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}
