import { useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Loader2, CheckCircle2, XCircle, Eye, FileText, Users, Zap } from 'lucide-react'
import { openSessionWS } from '../api/client'
import { useSession } from '../context/SessionContext'
import IterationCard from '../components/IterationCard'
import ScoreGauge from '../components/ScoreGauge'

function scoreColour(s) {
  if (!s) return 'text-zinc-500'
  if (s >= 80) return 'text-emerald-400'
  if (s >= 60) return 'text-amber-400'
  return 'text-brand-400'
}

// ── Stage pipeline ────────────────────────────────────────────────────────────

const STAGES = [
  { key: 'draft',   label: 'Draft',   icon: FileText },
  { key: 'review',  label: 'Review',  icon: Users },
  { key: 'improve', label: 'Improve', icon: Zap },
]

function phaseToStage(currentPhase) {
  switch (currentPhase) {
    case 'generating':       return { active: 'draft',   done: [] }
    case 'reviewing':        return { active: 'review',  done: ['draft'] }
    case 'iteration_complete': return { active: null,    done: ['draft', 'review'] }
    case 'improving':        return { active: 'improve', done: ['draft', 'review'] }
    case 'complete':         return { active: null,      done: ['draft', 'review', 'improve'] }
    default:                 return { active: 'draft',   done: [] }
  }
}

const PHASE_LABEL = {
  generating:          'Generating draft…',
  reviewing:           'Council reviewing…',
  iteration_complete:  'Iteration complete',
  improving:           'Generating improved version…',
  complete:            'Complete',
}

function StagePipeline({ currentPhase, iterationNum }) {
  const { active, done } = phaseToStage(currentPhase)
  const label = PHASE_LABEL[currentPhase] ?? 'Starting…'

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1">
        {STAGES.map((s, i) => {
          const isDone   = done.includes(s.key)
          const isActive = s.key === active
          return (
            <div key={s.key} className="flex items-center gap-1">
              {i > 0 && (
                <div className={`h-px w-4 ${isDone ? 'bg-emerald-600' : isActive ? 'bg-brand-500' : 'bg-zinc-700'}`} />
              )}
              <div className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium transition-all ${
                isActive
                  ? 'bg-brand-600/20 text-brand-300 border border-brand-600/40'
                  : isDone
                  ? 'bg-emerald-900/20 text-emerald-400 border border-emerald-800/40'
                  : 'bg-zinc-900 text-zinc-600 border border-zinc-800'
              }`}>
                {isActive
                  ? <Loader2 size={9} className="animate-spin" />
                  : isDone
                  ? <CheckCircle2 size={9} />
                  : <span className="w-2 h-2 rounded-full bg-zinc-700 inline-block" />}
                {s.label}
              </div>
            </div>
          )
        })}
        {iterationNum > 0 && (
          <span className="ml-2 text-xs text-zinc-600">iter {iterationNum}</span>
        )}
      </div>
      <p className="text-xs text-zinc-500">{label}</p>
    </div>
  )
}

// ── Group panel ───────────────────────────────────────────────────────────────

function GroupPanel({ groupData, groupIndex, targetScore }) {
  const {
    iterations = [],
    bestScore = 0,
    status = 'pending',
    generator = '',
    currentPhase = null,
    currentIteration = 0,
  } = groupData

  const progressPct = targetScore > 0 ? Math.min((bestScore / targetScore) * 100, 100) : 0

  const statusBadge = status === 'complete'
    ? <span className="badge bg-emerald-900/30 text-emerald-400 border border-emerald-800/50 text-xs flex items-center gap-1"><CheckCircle2 size={10} /> Done</span>
    : status === 'running'
    ? <span className="badge bg-brand-900/30 text-brand-400 border border-brand-800/50 text-xs flex items-center gap-1"><Loader2 size={10} className="animate-spin" /> Running</span>
    : <span className="badge bg-zinc-800 text-zinc-500 border border-zinc-700 text-xs">Pending</span>

  return (
    <div className="card overflow-hidden flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-zinc-800 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-6 h-6 rounded-full bg-brand-600/20 border border-brand-600/30 flex items-center justify-center text-xs font-bold text-brand-400 flex-shrink-0">
            {groupIndex + 1}
          </div>
          <div className="min-w-0">
            <span className="font-semibold text-sm text-white">Generator {groupIndex + 1}</span>
            {generator && (
              <span className="ml-2 text-xs text-zinc-500 font-mono truncate hidden sm:inline">{generator}</span>
            )}
          </div>
        </div>
        {statusBadge}
      </div>

      <div className="p-4 space-y-4 flex-1">
        {/* Stage pipeline — shown while running */}
        {status === 'running' && (
          <StagePipeline currentPhase={currentPhase} iterationNum={currentIteration} />
        )}

        {/* Score + progress */}
        <div className="flex items-center gap-3">
          <ScoreGauge score={bestScore} target={targetScore} size={80} />
          <div className="flex-1 min-w-0">
            <div className="flex justify-between text-xs text-zinc-500 mb-1">
              <span>Progress to {targetScore}</span>
              <span className={`font-mono font-bold ${scoreColour(bestScore)}`}>{bestScore.toFixed(1)}</span>
            </div>
            <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-brand-600 to-emerald-500 transition-all duration-700"
                style={{ width: `${progressPct}%` }}
              />
            </div>
            <div className="text-xs text-zinc-600 mt-1">
              {iterations.length} iteration{iterations.length !== 1 ? 's' : ''} complete
            </div>
          </div>
        </div>

        {/* Iterations list */}
        {iterations.length > 0 && (
          <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
            {[...iterations].reverse().map((iter, i) => (
              <IterationCard key={iter.iteration} data={iter} index={i} />
            ))}
          </div>
        )}

        {status === 'pending' && (
          <div className="text-xs text-zinc-600 text-center py-4">
            Waiting for previous group to complete…
          </div>
        )}
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function Session() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { state, dispatch } = useSession()
  const wsRef = useRef(null)

  useEffect(() => {
    if (!id) return
    const ws = openSessionWS(id, (event) => dispatch({ type: 'EVENT', payload: event }), () => {})
    wsRef.current = ws
    return () => { try { ws.close() } catch {} }
  }, [id])

  useEffect(() => {
    if (state.status === 'complete') {
      setTimeout(() => navigate(`/results/${id}`), 1500)
    }
  }, [state.status, id, navigate])

  const { groups, groupsTotal, overallBestScore, targetScore, status } = state
  const groupEntries = Object.entries(groups).sort(([a], [b]) => Number(a) - Number(b))
  const completedCount = groupEntries.filter(([, g]) => g.status === 'complete').length

  const gridCols =
    groupEntries.length >= 3 ? 'lg:grid-cols-3' :
    groupEntries.length === 2 ? 'lg:grid-cols-2' :
    ''

  return (
    <div className="px-6 lg:px-10 py-8 lg:py-10 mx-auto w-full max-w-6xl">

      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold">Live Session</h1>
            {status === 'complete' ? (
              <span className="badge bg-emerald-900/30 text-emerald-400 border border-emerald-800/50 flex items-center gap-1">
                <CheckCircle2 size={12} /> Complete
              </span>
            ) : status === 'error' ? (
              <span className="badge bg-red-900/30 text-red-400 border border-red-800/50 flex items-center gap-1">
                <XCircle size={12} /> Error
              </span>
            ) : (
              <span className="badge bg-brand-900/30 text-brand-400 border border-brand-800/50 flex items-center gap-1">
                <Loader2 size={12} className="animate-spin" /> Running
              </span>
            )}
          </div>
          <p className="text-sm font-mono text-zinc-500">{id}</p>
        </div>
        {status === 'complete' && (
          <button onClick={() => navigate(`/results/${id}`)} className="btn-primary flex items-center gap-2">
            <Eye size={16} /> View Results
          </button>
        )}
      </div>

      {/* Overall progress bar */}
      <div className="card p-5 mb-6 flex items-center gap-5">
        <div className="text-center flex-shrink-0">
          <div className={`text-3xl font-extrabold ${scoreColour(overallBestScore)}`}>
            {overallBestScore.toFixed(1)}
          </div>
          <div className="text-xs text-zinc-600 mt-0.5">Overall Best</div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex justify-between text-xs text-zinc-500 mb-1.5">
            <span>Best score across all groups</span>
            <span>Target: {targetScore}</span>
          </div>
          <div className="h-2.5 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-brand-600 to-emerald-500 transition-all duration-700"
              style={{ width: `${targetScore > 0 ? Math.min((overallBestScore / targetScore) * 100, 100) : 0}%` }}
            />
          </div>
        </div>
        {groupsTotal > 0 && (
          <div className="text-sm text-zinc-500 flex-shrink-0 text-right">
            <div className="font-bold text-white">{completedCount}/{groupsTotal}</div>
            <div className="text-xs text-zinc-600">groups done</div>
          </div>
        )}
      </div>

      {/* Error banner */}
      {status === 'error' && state.error && (
        <div className="card p-5 border-red-800/50 bg-red-950/20 text-red-400 text-sm mb-6">
          <strong>Error:</strong> {state.error}
        </div>
      )}

      {/* Starting spinner */}
      {status === 'running' && groupEntries.length === 0 && (
        <div className="card p-8 text-center text-zinc-600 mb-6">
          <Loader2 size={24} className="animate-spin mx-auto mb-3 text-brand-500" />
          Starting session…
        </div>
      )}

      {/* Complete banner */}
      {status === 'complete' && (
        <div className="card p-4 border-emerald-800/40 bg-emerald-950/20 text-emerald-400 text-sm mb-6 flex items-center gap-3">
          <CheckCircle2 size={16} /> Session complete — redirecting to results…
        </div>
      )}

      {/* Per-group panels — side by side */}
      {groupEntries.length > 0 && (
        <div className={`grid gap-5 ${gridCols}`}>
          {groupEntries.map(([idx, groupData]) => (
            <GroupPanel
              key={idx}
              groupIndex={Number(idx)}
              groupData={groupData}
              targetScore={targetScore}
            />
          ))}
        </div>
      )}
    </div>
  )
}
