import { useState, useRef } from 'react'

export default function DocumentInput({ onIngest, ingesting, ingested }) {
  const [text, setText] = useState('')
  const fileInputRef = useRef(null)

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files)
    const texts = await Promise.all(
      files.map((f) => f.text())
    )
    const combined = texts.join('\n\n---\n\n')
    setText((prev) => (prev ? prev + '\n\n---\n\n' + combined : combined))
  }

  const handleSubmit = () => {
    if (!text.trim()) return
    // Split on --- separator for multiple documents
    const docs = text.split(/\n---\n/).map((d) => d.trim()).filter(Boolean)
    onIngest(docs)
  }

  return (
    <section className="glass-card rounded-2xl p-5 sm:p-6 transition-all duration-300">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center">
            <svg className="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h2 className="text-sm font-semibold text-slate-200">Documents</h2>
        </div>
        {ingested && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-teal-500/10 border border-teal-500/20">
            <div className="w-2 h-2 rounded-full bg-teal-400 animate-pulse-dot" />
            <span className="text-xs font-medium text-teal-300">
              {ingested.chunk_count} chunks • {ingested.total_tokens.toLocaleString()} tokens
            </span>
          </div>
        )}
      </div>

      {ingested && (
        <div className="mb-4 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-between animate-fadeIn">
          <div className="flex items-center gap-2.5">
            <span className="text-emerald-400 font-bold text-base">✓</span>
            <div>
              <p className="text-xs font-semibold text-emerald-300">
                Documents ingested and indexed successfully!
              </p>
              <p className="text-[11px] text-slate-400">
                Ready for queries. You can ask questions in the Query box below.
              </p>
            </div>
          </div>
        </div>
      )}

      <textarea
        id="document-input"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste your documents here... Separate multiple documents with ---"
        rows={6}
        className="w-full bg-navy-800/60 border border-navy-600/40 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 resize-y transition-all duration-200"
      />

      <div className="flex items-center gap-3 mt-3">
        <button
          onClick={handleSubmit}
          disabled={ingesting || !text.trim()}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-teal-600 text-white text-sm font-medium
                     hover:from-teal-400 hover:to-teal-500 disabled:opacity-40 disabled:cursor-not-allowed
                     transition-all duration-200 shadow-lg shadow-teal-500/20 hover:shadow-teal-500/30
                     flex items-center gap-2"
        >
          {ingesting ? (
            <>
              <div className="spinner !w-4 !h-4 !border-2" />
              Ingesting…
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Ingest Documents
            </>
          )}
        </button>

        <button
          onClick={() => fileInputRef.current?.click()}
          className="px-4 py-2.5 rounded-xl border border-navy-600/50 text-sm text-slate-300
                     hover:border-teal-500/30 hover:text-teal-300 transition-all duration-200
                     flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
          Upload .txt
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.md,.text"
          multiple
          onChange={handleFileUpload}
          className="hidden"
        />
      </div>
    </section>
  )
}
