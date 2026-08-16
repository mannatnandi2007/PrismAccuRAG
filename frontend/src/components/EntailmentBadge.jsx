export default function EntailmentBadge({ passRate, queryType }) {
  const getColor = (rate) => {
    if (rate >= 90) return { bg: 'bg-emerald-500/15', border: 'border-emerald-500/30', text: 'text-emerald-400', dot: 'bg-emerald-400' }
    if (rate >= 70) return { bg: 'bg-amber-500/15', border: 'border-amber-500/30', text: 'text-amber-400', dot: 'bg-amber-400' }
    return { bg: 'bg-red-500/15', border: 'border-red-500/30', text: 'text-red-400', dot: 'bg-red-400' }
  }

  const colors = getColor(passRate)

  return (
    <div className="glass-card rounded-2xl p-5">
      {/* Entailment */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-teal-500/15 flex items-center justify-center">
          <svg className="w-3.5 h-3.5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-sm font-semibold text-slate-200">Accuracy Check</h3>
      </div>

      <div className="text-center mb-4">
        <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl ${colors.bg} border ${colors.border}`}>
          <div className={`w-2 h-2 rounded-full ${colors.dot} animate-pulse-dot`} />
          <span className={`text-2xl font-bold ${colors.text}`}>{passRate.toFixed(1)}%</span>
        </div>
        <p className="text-xs text-slate-400 mt-2">entailment pass rate</p>
      </div>

      {/* Query Type */}
      <div className="flex items-center justify-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-800/50 border border-navy-600/30">
          <svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z" />
          </svg>
          <span className="text-xs font-medium text-slate-300 capitalize">{queryType}</span>
        </div>
      </div>
    </div>
  )
}
