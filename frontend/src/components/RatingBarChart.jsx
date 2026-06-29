export default function RatingBarChart({ data }) {
  const maxCount = Math.max(...data.map(d => d.count), 1)

  return (
    <div className="rating-bars">
      {[...data].reverse().map((row) => (
        <div key={row.stars} className="rating-row">
          <div className="rating-label">
            <span>★</span>{row.stars}
          </div>
          <div className="rating-bar-bg">
            <div
              className="rating-bar-fill"
              style={{ width: `${(row.count / maxCount) * 100}%` }}
            />
          </div>
          <div className="rating-count">{row.count}</div>
        </div>
      ))}
    </div>
  )
}
