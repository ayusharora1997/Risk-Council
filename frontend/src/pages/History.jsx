import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock, Trophy, FileText, Trash2, ExternalLink } from 'lucide-react'
import { loadHistory, saveSessionToHistory } from '../context/SessionContext'

const DOC_TYPE_LABELS = { policy: '📋 Policy', sop: '📝 SOP', workflow: '🔀 Workflow' }

function scoreColour(s) {
  if (!s) return 'text-zinc-500'
  if (s >= 80) return 'text-emerald-400'
  if (s >= 60) return 'text-amber-400'
  return 'text-brand-400'
}

function relativeDate(iso) {
  try {
    const diff = Date.now() - new Date(iso).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'Just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    const days = Math.floor(hrs / 24)
    if (days < 7) return `${days}d ago`
    return new Date(iso).toLocaleDateString()
  } catch {
    return ''
  }
}

export default function History() {
  const navigate = useNavigate()
  const [entries, setEntries] = useState(() => loadHistory())

  const remove = (sessionId) => {
    try {
      const next = entries.filter(e => e.session_id !== sessionId)
      localStorage.setItem('arc_session_history', JSON.stringify(next))
      setEntries(next)
    } catch {}
  }

  const clearAll = () => {
    try {
      localStorage.removeItem('arc_session_history')
      setEntries([])
    } catch {}
  }

  return (
    <div className="px-6 lg:px-10 py-8 lg:py-10 mx-auto w-full max-w-5xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-extrabold mb-1">Session History</h1>
          <p className="text-zinc-500 text-sm">{entries.length} saved session{entries.length !== 1 ? 's' : ''} in this browser</p>
        </div>
        {entries.length > 0 && (
          <button onClick={clearAll} className="btn-ghost flex items-center gap-2 text-sm text-red-400 hover:text-red-300">
            <Trash2 size={14} /> Clear All
          </button>
        )}
      </div>

      {entries.length === 0 ? (
        <div className="card p-16 text-center">
          <FileText size={40} className="mx-auto text-zinc-700 mb-4" />
          <p className="text-zinc-500 mb-2">No sessions saved yet</p>
          <p className="text-zinc-600 text-sm mb-6">Complete a session and the results will appear here automatically.</p>
          <button onClick={() => navigate('/configure')} className="btn-primary inline-flex items-center gap-2">
            Start a Session
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {entries.map(entry => (
            <div key={entry.session_id} className="card p-5 hover:border-zinc-700 transition-colors">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className="badge bg-zinc-800 text-zinc-300 border border-zinc-700 text-xs">
                      {DOC_TYPE_LABELS[entry.document_type] ?? entry.document_type}
                    </span>
                    {entry.termination_reason === 'target_reached' && (
                      <span className="badge bg-emerald-900/30 text-emerald-400 border border-emerald-800/50 text-xs">
                        Target Reached ✓
                      </span>
                    )}
                    <span className="text-xs text-zinc-600 flex items-center gap-1">
                      <Clock size={10} /> {relativeDate(entry.saved_at)}
                    </span>
                  </div>

                  <p className="text-sm text-zinc-300 leading-relaxed mb-3 line-clamp-2">
                    {entry.scenario || '(no scenario text)'}
                  </p>

                  <div className="flex items-center gap-4 text-xs text-zinc-500">
                    <span className="flex items-center gap-1">
                      <Trophy size={11} className={scoreColour(entry.best_score)} />
                      <span className={`font-bold ${scoreColour(entry.best_score)}`}>{entry.best_score?.toFixed(1)}</span> / 100
                    </span>
                    <span>{entry.groups_count} generator group{entry.groups_count !== 1 ? 's' : ''}</span>
                    <span className="font-mono text-zinc-700">{entry.session_id}</span>
                  </div>

                  {entry.groups?.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {entry.groups.map((g, i) => (
                        <span key={i} className="text-xs bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded font-mono">
                          {g.generator} · <span className={scoreColour(g.best_score)}>{g.best_score?.toFixed(1)}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex flex-col gap-2 flex-shrink-0">
                  <button
                    onClick={() => navigate(`/results/${entry.session_id}`)}
                    className="btn-ghost flex items-center gap-1.5 text-xs"
                  >
                    <ExternalLink size={12} /> View
                  </button>
                  <button
                    onClick={() => remove(entry.session_id)}
                    className="p-2 rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-900/20 transition-colors"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
