import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import SkeletonCard from '../components/SkeletonCard'

export default function Results() {
  const [searchParams] = useSearchParams()
  const query = searchParams.get('q') || ''
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!query) return
    setLoading(true)
    setError(null)
    setProducts([])
    fetch(`/api/search?q=${encodeURIComponent(query)}&limit=24`)
      .then(r => r.json())
      .then(data => {
        setProducts(data.products || [])
        setLoading(false)
      })
      .catch(() => {
        setError('Failed to fetch results. Is the backend running?')
        setLoading(false)
      })
  }, [query])

  return (
    <div className="page">
      <div className="page-header">
        <h2>Results for "{query}"</h2>
        {!loading && products.length > 0 && (
          <p>{products.length} product{products.length !== 1 ? 's' : ''} found</p>
        )}
      </div>

      {error && (
        <div className="empty-state">
          <h3>⚠️ {error}</h3>
        </div>
      )}

      {loading && (
        <div className="product-grid">
          {Array.from({ length: 12 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {!loading && !error && products.length === 0 && (
        <div className="empty-state">
          <h3>No products found</h3>
          <p>Try a different keyword like "phone", "laptop", or "earphone".</p>
        </div>
      )}

      {!loading && products.length > 0 && (
        <div className="product-grid">
          {products.map((p, i) => <ProductCard key={i} product={p} />)}
        </div>
      )}
    </div>
  )
}
