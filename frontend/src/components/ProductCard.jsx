import { useNavigate } from 'react-router-dom'

const SENTIMENT_COLORS = {
  positive: 'positive',
  negative: 'negative',
  neutral: 'neutral',
}

export default function ProductCard({ product }) {
  const navigate = useNavigate()

  const handleClick = () => {
    navigate(`/product/${encodeURIComponent(product.name)}`)
  }

  return (
    <div className="product-card" onClick={handleClick}>
      <div className="product-card-name">{product.name}</div>
      <div className="product-card-meta">
        {product.avg_rating && (
          <span className="star-badge">
            ★ {product.avg_rating}
          </span>
        )}
        <span className="review-count">{product.review_count.toLocaleString()} reviews</span>
      </div>
      {product.dominant_sentiment && (
        <span className={`sentiment-pill ${SENTIMENT_COLORS[product.dominant_sentiment] || 'neutral'}`}>
          {product.dominant_sentiment}
        </span>
      )}
    </div>
  )
}
