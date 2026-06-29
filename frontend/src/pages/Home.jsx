import SearchBar from '../components/SearchBar'
import { useNavigate } from 'react-router-dom'

export default function Home() {
  return (
    <div className="hero">
      <div className="hero-badge">
        <span>⚡</span> Powered by DistilBERT + Qwen 2.5
      </div>
      <h1>Understand What<br />Customers Really Feel</h1>
      <p>
        Deep sentiment analysis across 5 emotional levels. Search any product to uncover the real story behind its reviews.
      </p>
      <SearchBar autofocus />
    </div>
  )
}
