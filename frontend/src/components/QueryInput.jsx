import { useState } from 'react'

export default function QueryInput({ onQuery, loading, disabled }) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!query.trim() || disabled) return
    onQuery(query.trim())
  }

  return (
    <section className="glass-card rounded-2xl p-5 sm:p-6 transition-all duration-300">
      <div className="flex items-center gap-2.5 mb-4">
        <div className="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center">
          <svg className="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-sm font-semibold text-slate-200">Query</h2>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          id="query-input"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={disabled ? "Ingest documents first…" : "Ask a question about your documents…"}
          disabled={disabled}
          className="flex-1 bg-navy-800/60 border border-navy-600/40 rounded-xl px-4 py-3 text-sm text-slate-200
                     placeholder-slate-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
        />
        <button
          id="run-button"
          type="submit"
          disabled={loading || disabled || !query.trim()}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-teal-600 text-white text-sm font-semibold
                     hover:from-teal-400 hover:to-teal-500 disabled:opacity-40 disabled:cursor-not-allowed
                     transition-all duration-200 shadow-lg shadow-teal-500/20 hover:shadow-teal-500/30
                     flex items-center gap-2 whitespace-nowrap"
        >
          {loading ? (
            <>
              <div className="spinner !w-4 !h-4 !border-2" />
              Running…
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Run
            </>
          )}
        </button>
      </form>
    </section>
  )
}
