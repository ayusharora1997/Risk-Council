import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Download, ArrowLeft, Trophy, Clock, Layers, Target, Loader2, Crown } from 'lucide-react'
import { api, exportUrl, groupExportUrl } from '../api/client'
import { useSession } from '../context/SessionContext'
import { saveSessionToHistory } from '../context/SessionContext'
import ScoreGauge from '../components/ScoreGauge'
import ScoreBreakdown from '../components/ScoreBreakdown'
import PolicyViewer from '../components/PolicyViewer'
import IterationCard from '../components/IterationCard'

const DOC_TYPE_LABELS = { policy: '📋 Policy', sop: '📝 SOP', workflow: '🔀 Workflow' }

function scoreColour(s) {
  if (!s) return 'text-zinc-500'
  if (s >= 80) return 'text-emerald-400'
  if (s >= 60) return 'text-amber-400'
  return 'text-brand-400'
}

function StatCard({ icon: Icon, label, value, sub }) {
  return (
    <div className="card p-5 flex items-start gap-4">
      <div className="w-10 h-10 rounded-xl bg-brand-600/15 border border-brand-600/20 flex items-center justify-center flex-shrink-0">
        <Icon size={18} className="text-brand-400" />
      </div>
      <div>
        <div className="text-xl font-bold text-white">{value}</div>
        <div className="text-xs text-zinc-500">{label}</div>
        {sub && <div className="text-xs text-zinc-600 mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

function GroupResultPanel({ group, groupIndex, isBest, targetScore, sessionId }) {
  const cfg = group.config
  const finalPolicy = group.final_policy?.content ?? ''
  const breakdown = group.iterations?.[group.iterations.length - 1]?.score_breakdown ?? {}
  const termLabel = group.termination_reason === 'target_reached' ? 'Target Reached ✓' : 'Max Iterations'

  return (
    <div className="space-y-6">
      {/* Generator identity */}
      <div className="card p-4 flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-brand-600/20 border border-brand-600/30 flex items-center justify-center text-sm font-bold text-brand-400">
          {groupIndex + 1}
        </div>
        <div className="flex-1">
          <div className="font-semibold text-white">Generator {groupIndex + 1}</div>
          <div className="text-xs text-zinc-500 font-mono">{cfg?.generator_provider} / {cfg?.generator_model}</div>
        </div>
        <div className="flex items-center gap-2">
          {isBest && (
            <span className="badge bg-amber-900/30 text-amber-400 border border-amber-800/50">
              <Crown size={10} /> Best
            </span>
          )}
          <span className={`badge ${group.termination_reason === 'target_reached'
            ? 'bg-emerald-900/30 text-emerald-400 border border-emerald-800/50'
            : 'bg-zinc-800 text-zinc-400 border border-zinc-700'}`}>
            {termLabel}
          </span>
        </div>
      </div>

      {/* Score + breakdown */}
      <div className="card p-6 flex flex-col sm:flex-row items-center gap-6">
        <ScoreGauge score={group.best_score} target={targetScore} size={160} />
        <div className="flex-1 w-full">
          <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-4">Score Breakdown</h3>
          <ScoreBreakdown breakdown={breakdown} />
        </div>
      </div>

      {/* Stats */}
      <div className="grid sm:grid-cols-3 gap-4">
        <StatCard icon={Trophy} label="Best Score" value={`${group.best_score?.toFixed(1)} / 100`} />
        <StatCard icon={Layers} label="Iterations" value={group.iterations?.length ?? 0} sub={`of ${cfg?.max_iterations} max`} />
        <StatCard icon={Clock} label="Duration" value={`${group.total_duration_seconds?.toFixed(0)}s`} />
      </div>

      {/* Final policy */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-semibold">Final Document</h3>
          <a
            href={groupExportUrl(sessionId, groupIndex, 'final/docx')}
            download
            className="btn-ghost flex items-center gap-1.5 text-xs"
          >
            <Download size={12} /> Final (.docx)
          </a>
        </div>
        <PolicyViewer content={finalPolicy} />
      </div>

      {/* Iteration history with per-iteration downloads */}
      {group.iterations?.length > 0 && (
        <div>
          <h3 className="text-base font-semibold mb-3">Iteration History</h3>
          <div className="space-y-3">
            {[...group.iterations].reverse().map((iter, i) => (
              <div key={iter.iteration_number} className="space-y-1.5">
                <IterationCard
                  data={{
                    iteration: iter.iteration_number,
                    score: iter.aggregated_score,
                    best_score: group.best_score,
                    score_breakdown: iter.score_breakdown,
                    policy_version: iter.policy_version,
                    reviewer_scores: iter.individual_reviews?.map(r => ({
                      reviewer: `${r.reviewer_provider}/${r.reviewer_model}`,
                      total: r.score?.total_score,
                      fairness: r.score?.fairness,
                      bias_mitigation: r.score?.bias_mitigation,
                      ethical_soundness: r.score?.ethical_soundness,
                      governance: r.score?.governance,
                      controls: r.score?.controls,
                      practicality: r.score?.practicality,
                    })) ?? [],
                  }}
                  index={i}
                />
                {/* Per-iteration downloads */}
                <div className="flex items-center gap-3 pl-3 ml-1 border-l border-zinc-800">
                  <span className="text-xs text-zinc-600 font-mono">Iter {iter.iteration_number}</span>
                  <a
                    href={groupExportUrl(sessionId, groupIndex, `iter/${iter.iteration_number}/draft/docx`)}
                    download
                    className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
                  >
                    <Download size={10} /> Draft (.docx)
                  </a>
                  <a
                    href={groupExportUrl(sessionId, groupIndex, `iter/${iter.iteration_number}/reviews/docx`)}
                    download
                    className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
                  >
                    <Download size={10} /> Reviews (.docx)
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function Results() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { state } = useSession()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeGroup, setActiveGroup] = useState(0)

  useEffect(() => {
    api.getSession(id)
      .then(data => {
        if (data.result) {
          setResult(data.result)
          // Save summary to localStorage history
          const r = data.result
          const bestGroup = r.groups?.[r.overall_best_group_index]
          saveSessionToHistory({
            session_id: id,
            saved_at: new Date().toISOString(),
            scenario: (r.scenario || '').slice(0, 160),
            document_type: r.document_type || 'policy',
            best_score: r.overall_best_score,
            groups_count: r.groups?.length ?? 1,
            groups: r.generator_groups?.map((g, i) => ({
              generator: `${g.generator_provider}/${g.generator_model}`,
              best_score: r.groups?.[i]?.best_score ?? 0,
            })) ?? [],
            termination_reason: bestGroup?.termination_reason ?? '',
          })
          setActiveGroup(r.overall_best_group_index ?? 0)
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return (
    <div className="min-h-[70vh] flex justify-center items-center gap-3 text-zinc-500">
      <Loader2 size={20} className="animate-spin" /> Loading results…
    </div>
  )

  if (!result) return (
    <div className="min-h-[70vh] flex flex-col justify-center items-center text-center">
      <p className="text-zinc-500 mb-4">Results not available. The session may still be running.</p>
      <button onClick={() => navigate(`/session/${id}`)} className="btn-ghost">← Back to session</button>
    </div>
  )

  const groups = result.groups ?? []
  const bestIdx = result.overall_best_group_index ?? 0
  const bestScore = result.overall_best_score ?? 0
  const docTypeLabel = DOC_TYPE_LABELS[result.document_type] ?? result.document_type
  const targetScore = result.target_score ?? 85

  return (
    <div className="px-6 lg:px-10 py-8 lg:py-10 mx-auto w-full max-w-6xl">

      {/* Header */}
      <div className="flex items-start justify-between mb-8 gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1 flex-wrap">
            <h1 className="text-3xl font-extrabold">Results</h1>
            <span className="badge bg-zinc-800 text-zinc-300 border border-zinc-700">{docTypeLabel}</span>
            <span className={`badge ${result.groups?.[bestIdx]?.termination_reason === 'target_reached'
              ? 'bg-emerald-900/30 text-emerald-400 border border-emerald-800/50'
              : 'bg-amber-900/30 text-amber-400 border border-amber-800/50'}`}>
              {result.groups?.[bestIdx]?.termination_reason === 'target_reached' ? 'Target Reached ✓' : 'Max Iterations'}
            </span>
          </div>
          <p className="text-sm font-mono text-zinc-500">{id}</p>
          {result.scenario && (
            <p className="text-sm text-zinc-600 mt-1 max-w-lg">{result.scenario.slice(0, 120)}{result.scenario.length > 120 ? '…' : ''}</p>
          )}
        </div>
        <button onClick={() => navigate('/configure')} className="btn-ghost flex items-center gap-2 text-sm flex-shrink-0">
          <ArrowLeft size={14} /> New Session
        </button>
      </div>

      {/* Overall best score hero */}
      <div className="card p-6 mb-6 bg-gradient-to-br from-zinc-900 to-zinc-900/50 flex items-center gap-6">
        <div className="text-center">
          <div className={`text-5xl font-extrabold ${scoreColour(bestScore)}`}>{bestScore.toFixed(1)}</div>
          <div className="text-xs text-zinc-500 mt-1">Overall Best Score</div>
        </div>
        <div className="flex-1">
          <div className="h-3 bg-zinc-800 rounded-full overflow-hidden mb-2">
            <div
              className="h-full rounded-full bg-gradient-to-r from-brand-600 to-emerald-500 transition-all duration-700"
              style={{ width: `${Math.min((bestScore / targetScore) * 100, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-zinc-600">
            <span>0</span><span>Target: {targetScore}</span><span>100</span>
          </div>
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div><div className="text-lg font-bold text-white">{groups.length}</div><div className="text-xs text-zinc-600">Groups</div></div>
            <div><div className="text-lg font-bold text-white">{targetScore}</div><div className="text-xs text-zinc-600">Target</div></div>
            <div><div className="text-lg font-bold text-white">{result.max_iterations}</div><div className="text-xs text-zinc-600">Max Iters</div></div>
            <div><div className="text-lg font-bold text-white">{result.total_duration_seconds?.toFixed(0)}s</div><div className="text-xs text-zinc-600">Total Time</div></div>
          </div>
        </div>
      </div>

      {/* Exports */}
      <div className="card p-5 mb-6 flex flex-wrap gap-3">
        <h3 className="text-sm font-semibold text-zinc-400 w-full mb-1">Export (Best Group)</h3>
        <a href={exportUrl(id, 'markdown')} download className="btn-ghost flex items-center gap-2 text-sm">
          <Download size={14} /> Full Report (.md)
        </a>
        <a href={exportUrl(id, 'policy')} download className="btn-ghost flex items-center gap-2 text-sm">
          <Download size={14} /> Final Document (.md)
        </a>
        <a href={exportUrl(id, 'json')} download className="btn-ghost flex items-center gap-2 text-sm">
          <Download size={14} /> JSON Data
        </a>
        <a href={exportUrl(id, 'versions')} download className="btn-ghost flex items-center gap-2 text-sm">
          <Download size={14} /> All Versions (.zip)
        </a>
      </div>

      {/* Group tabs */}
      {groups.length > 1 && (
        <div className="flex gap-2 mb-6 flex-wrap">
          {groups.map((g, i) => (
            <button
              key={i}
              onClick={() => setActiveGroup(i)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeGroup === i
                  ? 'bg-brand-600 text-white'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
              }`}
            >
              {i === bestIdx && <Crown size={12} className="text-amber-400" />}
              Generator {i + 1}
              <span className={`font-mono ${i === bestIdx ? 'text-amber-300' : 'text-zinc-500'}`}>
                {g.best_score?.toFixed(1)}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Active group result */}
      {groups[activeGroup] && (
        <GroupResultPanel
          group={groups[activeGroup]}
          groupIndex={activeGroup}
          isBest={activeGroup === bestIdx}
          targetScore={targetScore}
          sessionId={id}
        />
      )}
    </div>
  )
}
