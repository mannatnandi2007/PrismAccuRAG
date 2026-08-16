import { useState } from 'react'

const STATUS_CONFIG = {
  preserved: {
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/20',
    text: 'text-emerald-400',
    label: 'Preserved',
    icon: '✓',
  },
  repaired: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
    text: 'text-amber-400',
    label: 'Repaired',
    icon: '⟲',
  },
  dropped: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
    text: 'text-red-400',
    label: 'Dropped',
    icon: '✕',
  },
}

export default function ClaimsExplainer({ claims, latency }) {
  const [expanded, setExpanded] = useState(false)

  const preserved = claims.filter((c) => c.status === 'preserved').length
  const repaired = claims.filter((c) => c.status === 'repaired').length
  const dropped = claims.filter((c) => c.status === 'dropped').length

  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      {/* Toggle Header */}
      <button
        id="explainability-toggle"
        onClick={() => setExpanded(!expanded)}
        className="w-full px-5 py-4 flex items-center justify-between hover:bg-navy-700/20 transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-teal-500/15 flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <h3 className="text-sm font-semibold text-slate-200">Explainability</h3>

          {/* Summary badges */}
          <div className="flex items-center gap-2 ml-2">
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              {preserved} preserved
            </span>
            {repaired > 0 && (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                {repaired} repaired
              </span>
            )}
            {dropped > 0 && (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">
                {dropped} dropped
              </span>
            )}
          </div>
        </div>

        <svg
          className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expandable Content */}
      {expanded && (
        <div className="px-5 pb-5 space-y-4">
          {/* Claims List */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Claims ({claims.length})
            </h4>
            <div className="max-h-80 overflow-y-auto space-y-2 pr-1">
              {claims.map((claim, i) => {
                const cfg = STATUS_CONFIG[claim.status] || STATUS_CONFIG.dropped
                return (
                  <div
                    key={i}
                    className={`flex items-start gap-3 p-3 rounded-xl ${cfg.bg} border ${cfg.border} transition-all duration-200`}
                  >
                    <span className={`text-sm font-bold ${cfg.text} mt-0.5 shrink-0 w-5 text-center`}>
                      {cfg.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-200 leading-relaxed">{claim.claim_text}</p>
                      <div className="flex items-center gap-3 mt-1.5">
                        <span className={`text-[10px] font-semibold uppercase tracking-wider ${cfg.text}`}>
                          {cfg.label}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          Score: {(claim.entailment_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Latency Breakdown */}
          {latency && (
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Latency Breakdown
              </h4>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                {[
                  ['Retrieval', latency.retrieval_ms],
                  ['Coref', latency.coref_ms],
                  ['Graph', latency.graph_build_ms],
                  ['Classify', latency.classification_ms],
                  ['Prune', latency.pruning_ms],
                  ['Claims', latency.claim_extraction_ms],
                  ['NLI', latency.entailment_ms],
                  ['Repair', latency.repair_ms],
                  ['LLM', latency.generation_ms],
                  ['Total', latency.total_ms],
                ].map(([label, ms]) => (
                  <div
                    key={label}
                    className={`text-center p-2 rounded-lg ${
                      label === 'Total' ? 'bg-teal-500/10 border border-teal-500/20' : 'bg-navy-800/40'
                    }`}
                  >
                    <p className={`text-sm font-semibold ${label === 'Total' ? 'text-teal-400' : 'text-slate-200'}`}>
                      {ms < 1000 ? `${ms.toFixed(0)}ms` : `${(ms / 1000).toFixed(1)}s`}
                    </p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{label}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
