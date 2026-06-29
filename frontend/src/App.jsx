import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import SearchBar from './components/SearchBar'
import Home from './pages/Home'
import Results from './pages/Results'
import ProductDetail from './pages/ProductDetail'
import './index.css'

function Navbar() {
  const location = useLocation()
  const isHome = location.pathname === '/'
  const searchParams = new URLSearchParams(location.search)
  const query = searchParams.get('q') || ''

  if (isHome) return null

  return (
    <nav className="navbar">
      <a href="/" className="navbar-logo">OpinionMeter</a>
      <SearchBar compact initialValue={query} />
    </nav>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/results" element={<Results />} />
        <Route path="/product/:productName" element={<ProductDetail />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
