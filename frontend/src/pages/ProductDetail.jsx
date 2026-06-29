import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import VerdictBadge from '../components/VerdictBadge'
import SentimentPieChart from '../components/SentimentPieChart'
import RatingBarChart from '../components/RatingBarChart'
import RepresentativeReviews from '../components/RepresentativeReviews'
import CompetitorList from '../components/CompetitorList'

export default function ProductDetail() {
  const { productName } = useParams()
  const navigate = useNavigate()
  const decodedName = decodeURIComponent(productName)

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Async Qwen summary state
  const [summary, setSummary] = useState(null)
  const [summaryLoading, setSummaryLoading] = useState(true)

  // Fetch main product data (fast - DistilBERT)
  useEffect(() => {
    setLoading(true)
    setError(null)
    setData(null)
    setSummary(null)
    setSummaryLoading(true)

    fetch(`/api/product?name=${encodeURIComponent(decodedName)}&limit=60`)
      .then(r => {
        if (!r.ok) throw new Error('Product not found')
        return r.json()
      })
      .then(d => {
        setData(d)
        setLoading(false)
      })
      .catch(e => {
        setError(e.message)
        setLoading(false)
        setSummaryLoading(false)
      })
  }, [decodedName])

  // Fetch Qwen summary asynchronously after main data loads
  useEffect(() => {
    if (!data) return
    setSummaryLoading(true)
    fetch(`/api/summary?name=${encodeURIComponent(decodedName)}&limit=30`)
      .then(r => r.json())
      .then(d => {
        setSummary(d)
        setSummaryLoading(false)
      })
      .catch(() => {
        setSummaryLoading(false)
      })
  }, [data])

  if (loading) return (
    <div className="page">
      <div className="loading-spinner"><div className="spinner" /></div>
      <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '-1rem' }}>
        Analyzing reviews with BERT... this may take a moment.
      </p>
    </div>
  )

  if (error) return (
    <div className="page">
      <div className="empty-state">
        <h3>⚠️ {error}</h3>
        <button className="back-btn" style={{ margin: '1rem auto 0' }} onClick={() => navigate(-1)}>← Go Back</button>
      </div>
    </div>
  )

  const avgConfPct = data ? Math.round(data.avg_confidence * 100) : 0

  return (
    <div className="page">
      <button className="back-btn" onClick={() => navigate(-1)}>← Back to Results</button>

      {/* Product Name */}
      <div className="page-header" style={{ marginBottom: '1.2rem' }}>
        <h2 style={{ fontSize: '1.3rem', lineHeight: 1.4 }}>{decodedName}</h2>
        <div className="stats-row" style={{ marginTop: '0.8rem' }}>
          <div className="stat-chip">
            <span className="stat-chip-label">Reviews</span>
            <span className="stat-chip-value">{data.review_count}</span>
          </div>
          {data.avg_rating && (
            <div className="stat-chip">
              <span className="stat-chip-label">Avg Rating</span>
              <span className="stat-chip-value" style={{ color: '#fbbf24' }}>★ {data.avg_rating}</span>
            </div>
          )}
          <div className="stat-chip">
            <span className="stat-chip-label">Model Confidence</span>
            <span className="stat-chip-value" style={{ color: 'var(--accent-light)', fontSize: '1.2rem' }}>{avgConfPct}%</span>
          </div>
        </div>
      </div>

      {/* Verdict */}
      {data.verdict && <VerdictBadge verdict={data.verdict} />}

      <div className="product-detail" style={{ marginTop: '1.2rem' }}>
        {/* Main Column */}
        <div className="detail-main">

          {/* AI Summary */}
          <div className="card">
            <div className="card-title">AI-Generated Summary</div>
            {summaryLoading ? (
              <div className="summary-loading">
                <div className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />
                Qwen is analyzing reviews and generating insights...
              </div>
            ) : summary ? (
              <p className="summary-text">{summary.summary}</p>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Summary unavailable.</p>
            )}
          </div>

          {/* Pros & Cons */}
          <div className="card">
            <div className="card-title">Pros & Cons</div>
            {summaryLoading ? (
              <div className="summary-loading">
                <div className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />
                Extracting key themes...
              </div>
            ) : summary && (summary.pros.length > 0 || summary.cons.length > 0) ? (
              <div className="pros-cons">
                <div>
                  <div className="pros-header">Pros</div>
                  <div className="pros-list">
                    {summary.pros.map((p, i) => <div key={i} className="pros-item">{p}</div>)}
                  </div>
                </div>
                <div>
                  <div className="cons-header">Cons</div>
                  <div className="cons-list">
                    {summary.cons.map((c, i) => <div key={i} className="cons-item">{c}</div>)}
                  </div>
                </div>
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Pros/Cons unavailable.</p>
            )}
          </div>

          {/* Sentiment Pie Chart */}
          <div className="card">
            <div className="card-title">Sentiment Breakdown</div>
            <SentimentPieChart data={data.sentiment_breakdown} />
          </div>

          {/* Representative Reviews */}
          <div className="card">
            <div className="card-title">Highlighted Reviews by Sentiment</div>
            <RepresentativeReviews reviewsByClass={data.representative_reviews} />
          </div>
        </div>

        {/* Sidebar */}
        <div className="detail-sidebar">

          {/* Rating Distribution */}
          <div className="card">
            <div className="card-title">Rating Distribution</div>
            <RatingBarChart data={data.rating_distribution} />
          </div>

          {/* Confidence Meter */}
          <div className="card">
            <div className="card-title">Model Confidence</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              Average confidence across all {data.review_count} predictions
            </div>
            <div className="confidence-meter">
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>0%</span>
                <span style={{ color: 'var(--accent-light)', fontWeight: 700 }}>{avgConfPct}%</span>
                <span style={{ color: 'var(--text-muted)' }}>100%</span>
              </div>
              <div className="confidence-bar-bg">
                <div className="confidence-bar-fill" style={{ width: `${avgConfPct}%` }} />
              </div>
            </div>
          </div>

          {/* Competitors */}
          <div className="card">
            <div className="card-title">Similar Products</div>
            <CompetitorList competitors={data.competitors} />
          </div>
        </div>
      </div>
    </div>
  )
}
