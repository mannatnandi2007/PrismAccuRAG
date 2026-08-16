import TokenStats from './TokenStats'
import EntailmentBadge from './EntailmentBadge'
import ClaimsExplainer from './ClaimsExplainer'

export default function ResultsPanel({ results, loading }) {
  if (loading) {
    return (
      <section className="space-y-4">
        {/* Skeleton answer */}
        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-7 h-7 rounded-lg bg-teal-500/15 flex items-center justify-center">
              <div className="spinner !w-4 !h-4 !border-2" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200">Processing Pipeline…</h3>
          </div>
          <div className="space-y-2.5">
            <div className="h-4 skeleton rounded-lg w-full" />
            <div className="h-4 skeleton rounded-lg w-5/6" />
            <div className="h-4 skeleton rounded-lg w-4/6" />
            <div className="h-4 skeleton rounded-lg w-3/4" />
          </div>
          <div className="flex items-center gap-2 mt-4 text-xs text-slate-500">
            <div className="spinner !w-3 !h-3 !border-[2px]" />
            <span>Running retrieval → coref → pruning → NLI → generation…</span>
          </div>
        </div>

        {/* Skeleton stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="glass-card rounded-2xl p-5">
            <div className="space-y-3">
              <div className="h-3 skeleton rounded w-1/3" />
              <div className="h-10 skeleton rounded-lg w-1/2 mx-auto" />
              <div className="h-3 skeleton rounded-full w-full" />
            </div>
          </div>
          <div className="glass-card rounded-2xl p-5">
            <div className="space-y-3">
              <div className="h-3 skeleton rounded w-1/3" />
              <div className="h-10 skeleton rounded-lg w-1/3 mx-auto" />
            </div>
          </div>
        </div>
      </section>
    )
  }

  if (!results) return null

  return (
    <section className="space-y-4">
      {/* Answer Card */}
      <div className="glass-card rounded-2xl p-5 sm:p-6 glow-teal">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-7 h-7 rounded-lg bg-teal-500/15 flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 className="text-sm font-semibold text-slate-200">Answer</h3>
        </div>
        <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
          {results.answer}
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <TokenStats stats={results.token_stats} />
        <EntailmentBadge passRate={results.entailment_pass_rate} queryType={results.query_type} />
      </div>

      {/* Claims Explainer */}
      <ClaimsExplainer claims={results.claims} latency={results.latency} />
    </section>
  )
}
