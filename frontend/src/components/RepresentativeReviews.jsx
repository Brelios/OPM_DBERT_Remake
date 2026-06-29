const SENTIMENT_COLORS = {
  'Very Positive': '#10b981',
  'Positive': '#4ade80',
  'Neutral': '#a78bfa',
  'Negative': '#fb923c',
  'Very Negative': '#ef4444',
}

export default function RepresentativeReviews({ reviewsByClass }) {
  if (!reviewsByClass || Object.keys(reviewsByClass).length === 0) return null

  const order = ['Very Positive', 'Positive', 'Neutral', 'Negative', 'Very Negative']
  const sorted = order.filter(label => reviewsByClass[label]?.length > 0)

  return (
    <div className="review-grid">
      {sorted.map(label => (
        reviewsByClass[label].map((review, i) => (
          <div key={`${label}-${i}`} className="review-card">
            <div className="review-text">"{review.text}{review.text.length >= 300 ? '...' : ''}"</div>
            <div className="review-meta">
              <span
                className="sentiment-pill"
                style={{
                  background: `${SENTIMENT_COLORS[label]}18`,
                  color: SENTIMENT_COLORS[label],
                  border: `1px solid ${SENTIMENT_COLORS[label]}33`,
                }}
              >
                {label}
              </span>
              <span className="review-confidence">{(review.confidence * 100).toFixed(0)}% confident</span>
            </div>
          </div>
        ))
      ))}
    </div>
  )
}
