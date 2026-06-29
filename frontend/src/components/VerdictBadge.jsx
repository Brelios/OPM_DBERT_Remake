const VERDICT_ICONS = {
  'HIGHLY RECOMMENDED': '🏆',
  'RECOMMENDED': '👍',
  'MIXED REVIEWS': '⚖️',
  'AVOID': '⚠️',
}

export default function VerdictBadge({ verdict }) {
  if (!verdict) return null
  const icon = VERDICT_ICONS[verdict.label] || '📊'

  return (
    <div className={`verdict-banner ${verdict.color}`}>
      <span className="verdict-icon">{icon}</span>
      <div>
        <div className="verdict-label">{verdict.label}</div>
        <div className="verdict-description">{verdict.description}</div>
      </div>
    </div>
  )
}
