export default function GuidePanel() {
  return (
    <section className="glass-card rounded-2xl p-5 sm:p-6 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center">
          <svg className="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-sm font-semibold text-slate-200">How to use</h2>
      </div>
      
      <div className="space-y-4 text-sm text-slate-300">
        <p>
          This app compresses retrieved context while maintaining factual accuracy. Follow these steps:
        </p>
        
        <ol className="list-decimal pl-5 space-y-2 text-slate-400">
          <li><strong className="text-teal-400">Ingest Documents:</strong> Upload `.txt` files or paste text below. Use documents with factual information, entities, and pronouns (e.g., biographies, Wikipedia articles) to see the coreference resolution work. Separate multiple documents with <code className="bg-navy-800 px-1 py-0.5 rounded text-xs">---</code>.</li>
          <li><strong className="text-teal-400">Ask a Question:</strong> Try factual queries (e.g., "When was X born?") or multi-hop queries that require connecting facts across sentences.</li>
          <li><strong className="text-teal-400">Review Compression:</strong> The app will classify your query, prune irrelevant sentences, verify facts using NLI, and repair the context before sending it to the LLM. You can see the detailed breakdown in the results!</li>
        </ol>
      </div>
    </section>
  )
}
