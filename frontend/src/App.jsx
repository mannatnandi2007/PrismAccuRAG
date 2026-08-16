import { useState, useEffect, useCallback } from 'react'
import DocumentInput from './components/DocumentInput'
import QueryInput from './components/QueryInput'
import ResultsPanel from './components/ResultsPanel'
import GuidePanel from './components/GuidePanel'

const defaultApiUrl = (import.meta.env.VITE_API_URL || '').trim().replace(/\/+$/, '')

export default function App() {
  const [customApiUrl, setCustomApiUrl] = useState(() => localStorage.getItem('prism_api_url') || defaultApiUrl)
  const [showConfig, setShowConfig] = useState(false)
  const [backendStatus, setBackendStatus] = useState('checking') // 'online' | 'offline' | 'checking'
  const [ingested, setIngested] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [ingesting, setIngesting] = useState(false)
  const [error, setError] = useState(null)

  const cleanBase = customApiUrl ? (customApiUrl.startsWith('http') ? customApiUrl : `https://${customApiUrl}`) : ''
  const API_BASE = cleanBase ? `${cleanBase}/api` : '/api'

  // Sync with backend status
  const checkBackendHealth = useCallback(async () => {
    setBackendStatus('checking')
    try {
      const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(6000) })
      if (res.ok) {
        const data = await res.json()
        setBackendStatus('online')
        if (data.documents_ingested && data.chunk_count > 0) {
          setIngested({
            chunk_count: data.chunk_count,
            total_tokens: data.total_tokens || (data.chunk_count * 150),
          })
        }
      } else {
        setBackendStatus('offline')
      }
    } catch {
      setBackendStatus('offline')
    }
  }, [API_BASE])

  useEffect(() => {
    checkBackendHealth()
  }, [checkBackendHealth])

  const handleSaveApiUrl = (url) => {
    const sanitized = url.trim().replace(/\/+$/, '')
    setCustomApiUrl(sanitized)
    localStorage.setItem('prism_api_url', sanitized)
    setShowConfig(false)
    setError(null)
  }

  const handleIngest = async (documents) => {
    setIngesting(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documents }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || `Ingestion failed with status ${res.status}`)
      }
      const data = await res.json()
      setIngested(data)
      setResults(null)
      setError(null)
      setBackendStatus('online')
    } catch (e) {
      const msg = e.message.includes('Failed to fetch') || e.message.includes('NetworkError')
        ? `Could not connect to backend at ${API_BASE}. If Render is waking up from sleep, please wait 20s and try again, or check your Backend URL in Settings (top right).`
        : e.message
      setError(msg)
      setIngested(null)
    } finally {
      setIngesting(false)
    }
  }

  const handleQuery = async (query) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        const detail = data.detail || `Query failed with status ${res.status}`
        if (detail.includes('No documents ingested')) {
          setIngested(null)
        }
        throw new Error(detail)
      }
      const data = await res.json()
      setResults(data)
    } catch (e) {
      const msg = e.message === 'Failed to fetch' 
        ? 'Could not connect to backend. Please check your connection or wait for Render to wake up.'
        : e.message
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-navy-700/50 bg-navy-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-tight text-slate-100">
                PrismAccuRAG
              </h1>
              <p className="text-xs text-slate-400">Accuracy-Preserving Adaptive RAG Compressor</p>
            </div>
          </div>

          {/* Backend Status & Config Button */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => checkBackendHealth()}
              title="Click to re-check connection"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                backendStatus === 'online'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20'
                  : backendStatus === 'checking'
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-300 animate-pulse'
                  : 'bg-red-500/10 border-red-500/30 text-red-300 hover:bg-red-500/20'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${
                backendStatus === 'online' ? 'bg-emerald-400' : backendStatus === 'checking' ? 'bg-amber-400' : 'bg-red-400'
              }`} />
              <span>{backendStatus === 'online' ? 'Backend Live' : backendStatus === 'checking' ? 'Connecting...' : 'Backend Offline'}</span>
            </button>

            <button
              onClick={() => setShowConfig(!showConfig)}
              className="p-2 rounded-lg border border-navy-700 bg-navy-800/80 text-slate-300 hover:text-white hover:border-navy-600 transition-colors"
              title="Backend URL Settings"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
        </div>

        {/* Backend URL Config Popover */}
        {showConfig && (
          <div className="border-t border-navy-700/60 bg-navy-800/95 px-4 sm:px-6 py-3.5 backdrop-blur-md">
            <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <label className="text-xs font-semibold text-slate-300 shrink-0">
                Backend API URL:
              </label>
              <input
                type="text"
                defaultValue={customApiUrl}
                placeholder="https://prismaccurag-backend.onrender.com"
                id="backend-url-input"
                className="flex-1 bg-navy-900/80 border border-navy-600 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500 w-full"
              />
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    const val = document.getElementById('backend-url-input')?.value || ''
                    handleSaveApiUrl(val)
                  }}
                  className="px-3.5 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-white text-xs font-medium transition-colors"
                >
                  Save & Connect
                </button>
                <button
                  onClick={() => setShowConfig(false)}
                  className="px-3 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 text-xs transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Error Banner */}
        {error && (
          <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 flex items-start gap-3">
            <svg className="w-5 h-5 text-red-400 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <div className="flex-1">
              <p className="text-sm text-red-300">{error}</p>
            </div>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300 transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Guide Panel */}
        <GuidePanel />

        {/* Document Input */}
        <DocumentInput onIngest={handleIngest} ingesting={ingesting} ingested={ingested} />

        {/* Query Input */}
        <QueryInput onQuery={handleQuery} loading={loading} disabled={!ingested} />

        {/* Results */}
        {(results || loading) && (
          <ResultsPanel results={results} loading={loading} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-navy-700/30 py-6 mt-12">
        <p className="text-center text-xs text-slate-500">
          PrismAccuRAG • Powered by FAISS, spaCy, DeBERTa NLI & Groq
        </p>
      </footer>
    </div>
  )
}
