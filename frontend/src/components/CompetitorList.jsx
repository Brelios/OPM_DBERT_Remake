import { useNavigate } from 'react-router-dom'

export default function CompetitorList({ competitors }) {
  const navigate = useNavigate()
  if (!competitors || competitors.length === 0) return (
    <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No similar products found.</div>
  )

  return (
    <div className="competitor-list">
      {competitors.map((c, i) => (
        <div
          key={i}
          className="competitor-card"
          onClick={() => navigate(`/product/${encodeURIComponent(c.name)}`)}
        >
          <div className="competitor-name">{c.name}</div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.15rem', flexShrink: 0 }}>
            {c.avg_rating && <div className="competitor-rating">★ {c.avg_rating}</div>}
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{c.review_count} reviews</div>
          </div>
        </div>
      ))}
    </div>
  )
}
