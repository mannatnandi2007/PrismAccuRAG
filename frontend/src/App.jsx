import { useState, useEffect, useCallback } from 'react'
import DocumentInput from './components/DocumentInput'
import QueryInput from './components/QueryInput'
import ResultsPanel from './components/ResultsPanel'
import GuidePanel from './components/GuidePanel'

const API_BASE = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : '/api'

export default function App() {
  const [ingested, setIngested] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [ingesting, setIngesting] = useState(false)
  const [error, setError] = useState(null)

  // Sync with backend status on mount
  const checkBackendHealth = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/health`)
      if (res.ok) {
        const data = await res.json()
        if (data.documents_ingested && data.chunk_count > 0) {
          setIngested({
            chunk_count: data.chunk_count,
            total_tokens: data.total_tokens || (data.chunk_count * 150),
          })
        }
      }
    } catch {
      // Backend might still be starting up
    }
  }, [])

  useEffect(() => {
    checkBackendHealth()
  }, [checkBackendHealth])

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
        const data = await res.json()
        throw new Error(data.detail || 'Ingestion failed')
      }
      const data = await res.json()
      setIngested(data)
      setResults(null)
      setError(null)
    } catch (e) {
      setError(e.message)
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
        const data = await res.json()
        const detail = data.detail || 'Query failed'
        if (detail.includes('No documents ingested')) {
          setIngested(null)
        }
        throw new Error(detail)
      }
      const data = await res.json()
      setResults(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-navy-700/50 bg-navy-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center shadow-lg">
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
