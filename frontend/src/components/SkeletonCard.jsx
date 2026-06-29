export default function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton" style={{ height: '18px', width: '85%' }} />
      <div className="skeleton" style={{ height: '14px', width: '60%' }} />
      <div className="skeleton" style={{ height: '22px', width: '90px', borderRadius: '100px' }} />
    </div>
  )
}
