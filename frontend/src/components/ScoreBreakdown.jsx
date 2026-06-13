const DIMS = [
  { key: 'fairness',          label: 'Fairness',          weight: '15%' },
  { key: 'bias_mitigation',   label: 'Bias Mitigation',   weight: '15%' },
  { key: 'ethical_soundness', label: 'Ethical Soundness', weight: '15%' },
  { key: 'governance',        label: 'Governance',        weight: '20%' },
  { key: 'controls',          label: 'Controls',          weight: '20%' },
  { key: 'practicality',      label: 'Practicality',      weight: '15%' },
]

function barColor(v) {
  if (v >= 80) return 'bg-emerald-500'
  if (v >= 60) return 'bg-amber-500'
  return 'bg-brand-500'
}

export default function ScoreBreakdown({ breakdown = {} }) {
  return (
    <div className="space-y-3">
      {DIMS.map(({ key, label, weight }) => {
        const v = breakdown[key] ?? 0
        return (
          <div key={key} className="flex items-center gap-3">
            <div className="w-36 text-xs text-zinc-400 shrink-0 text-right">
              {label} <span className="text-zinc-600">({weight})</span>
            </div>
            <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${barColor(v)}`}
                style={{ width: `${v}%` }}
              />
            </div>
            <span className="text-sm font-mono text-zinc-300 w-10 text-right">{v.toFixed(0)}</span>
          </div>
        )
      })}
    </div>
  )
}
