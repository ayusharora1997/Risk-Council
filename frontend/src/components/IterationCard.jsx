import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import ScoreBreakdown from './ScoreBreakdown'

function scoreColour(s) {
  if (s >= 80) return 'text-emerald-400'
  if (s >= 60) return 'text-amber-400'
  return 'text-brand-400'
}

export default function IterationCard({ data, index }) {
  const [open, setOpen] = useState(index === 0)
  const { iteration, score, best_score, score_breakdown, reviewer_scores = [] } = data

  return (
    <div className="card overflow-hidden animate-slide-up">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between p-5 hover:bg-zinc-800/40 transition-colors text-left"
      >
        <div className="flex items-center gap-4">
          <div className="w-9 h-9 rounded-full bg-zinc-800 flex items-center justify-center text-sm font-bold text-zinc-400">
            {iteration}
          </div>
          <div>
            <div className="font-semibold text-white">Iteration {iteration}</div>
            <div className="text-xs text-zinc-500">Policy Version {data.policy_version ?? iteration}</div>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className={`text-xl font-bold ${scoreColour(score)}`}>{score?.toFixed(1)}</div>
            <div className="text-xs text-zinc-600">/ 100</div>
          </div>
          {open ? <ChevronUp size={16} className="text-zinc-500" /> : <ChevronDown size={16} className="text-zinc-500" />}
        </div>
      </button>

      {open && (
        <div className="border-t border-zinc-800 p-5 space-y-6">
          <div>
            <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3">Score Breakdown</h4>
            <ScoreBreakdown breakdown={score_breakdown} />
          </div>

          {reviewer_scores.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3">Per-Reviewer Scores</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs text-zinc-600 border-b border-zinc-800">
                      <th className="text-left pb-2 font-medium">Reviewer</th>
                      <th className="text-right pb-2 font-medium">Fair.</th>
                      <th className="text-right pb-2 font-medium">Bias</th>
                      <th className="text-right pb-2 font-medium">Ethics</th>
                      <th className="text-right pb-2 font-medium">Gov.</th>
                      <th className="text-right pb-2 font-medium">Ctrl.</th>
                      <th className="text-right pb-2 font-medium">Pract.</th>
                      <th className="text-right pb-2 font-medium text-white">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reviewer_scores.map((rs, i) => (
                      <tr key={i} className="border-b border-zinc-800/50 last:border-0">
                        <td className="py-2 pr-4 text-zinc-400 font-mono text-xs">{rs.reviewer}</td>
                        <td className="py-2 text-right text-zinc-300">{rs.fairness?.toFixed(0)}</td>
                        <td className="py-2 text-right text-zinc-300">{rs.bias_mitigation?.toFixed(0)}</td>
                        <td className="py-2 text-right text-zinc-300">{rs.ethical_soundness?.toFixed(0)}</td>
                        <td className="py-2 text-right text-zinc-300">{rs.governance?.toFixed(0)}</td>
                        <td className="py-2 text-right text-zinc-300">{rs.controls?.toFixed(0)}</td>
                        <td className="py-2 text-right text-zinc-300">{rs.practicality?.toFixed(0)}</td>
                        <td className={`py-2 text-right font-bold ${scoreColour(rs.total)}`}>{rs.total?.toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
