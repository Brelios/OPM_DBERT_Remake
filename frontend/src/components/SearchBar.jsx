import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

export default function SearchBar({ initialValue = '', compact = false, autofocus = false }) {
  const [query, setQuery] = useState(initialValue)
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const debounceRef = useRef(null)
  const inputRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    setQuery(initialValue)
  }, [initialValue])

  useEffect(() => {
    if (autofocus && inputRef.current) inputRef.current.focus()
  }, [autofocus])

  const fetchSuggestions = (value) => {
    if (!value.trim() || value.length < 2) {
      setSuggestions([])
      return
    }
    fetch(`/api/suggest?q=${encodeURIComponent(value)}&limit=8`)
      .then(r => r.json())
      .then(data => setSuggestions(data.suggestions || []))
      .catch(() => setSuggestions([]))
  }

  const handleChange = (e) => {
    const val = e.target.value
    setQuery(val)
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => fetchSuggestions(val), 300)
    setShowSuggestions(true)
  }

  const handleSubmit = (value) => {
    const q = (value || query).trim()
    if (!q) return
    setShowSuggestions(false)
    setSuggestions([])
    navigate(`/results?q=${encodeURIComponent(q)}`)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSubmit()
  }

  return (
    <div className={`search-wrapper ${compact ? 'navbar-search-bar' : 'hero-search-bar'}`}>
      <span className="search-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
        </svg>
      </span>
      <input
        ref={inputRef}
        className="search-input"
        type="text"
        placeholder="Search for a product..."
        value={query}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
        onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
      />
      {showSuggestions && suggestions.length > 0 && (
        <div className="suggestions-dropdown">
          {suggestions.map((s, i) => (
            <div
              key={i}
              className="suggestion-item"
              onMouseDown={() => handleSubmit(s)}
            >
              {s}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
