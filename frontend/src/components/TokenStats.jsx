export default function TokenStats({ stats }) {
  const { original_tokens, compressed_tokens, final_tokens, percent_saved } = stats

  const barWidth = Math.max(5, 100 - percent_saved)

  return (
    <div className="glass-card rounded-2xl p-5 glow-teal">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-teal-500/15 flex items-center justify-center">
          <svg className="w-3.5 h-3.5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        </div>
        <h3 className="text-sm font-semibold text-slate-200">Token Compression</h3>
      </div>

      {/* Big stat */}
      <div className="text-center mb-5">
        <span className="text-4xl font-bold bg-gradient-to-r from-teal-400 to-teal-300 bg-clip-text text-transparent">
          {percent_saved.toFixed(1)}%
        </span>
        <p className="text-xs text-slate-400 mt-1">tokens saved</p>
      </div>

      {/* Compression bar */}
      <div className="mb-4">
        <div className="w-full h-3 bg-navy-700/60 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-teal-500 to-teal-400 transition-all duration-700 ease-out"
            style={{ width: `${barWidth}%` }}
          />
        </div>
        <div className="flex justify-between mt-1.5 text-xs text-slate-500">
          <span>Final: {final_tokens.toLocaleString()}</span>
          <span>Original: {original_tokens.toLocaleString()}</span>
        </div>
      </div>

      {/* Breakdown */}
      <div className="grid grid-cols-3 gap-3">
        <div className="text-center p-2.5 rounded-xl bg-navy-800/40">
          <p className="text-lg font-semibold text-slate-200">{original_tokens.toLocaleString()}</p>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mt-0.5">Original</p>
        </div>
        <div className="text-center p-2.5 rounded-xl bg-navy-800/40">
          <p className="text-lg font-semibold text-teal-400">{compressed_tokens.toLocaleString()}</p>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mt-0.5">Compressed</p>
        </div>
        <div className="text-center p-2.5 rounded-xl bg-navy-800/40">
          <p className="text-lg font-semibold text-teal-300">{final_tokens.toLocaleString()}</p>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mt-0.5">Final</p>
        </div>
      </div>
    </div>
  )
}
