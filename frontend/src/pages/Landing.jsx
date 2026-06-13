import { useNavigate } from 'react-router-dom'
import { ArrowRight, Clock, Trophy, History, Github, Zap, Users, FileText, BarChart3 } from 'lucide-react'
import { loadHistory } from '../context/SessionContext'

const DOC_BADGES = { policy: '📋 Policy', sop: '📝 SOP', workflow: '🔀 Workflow' }

function scoreColour(s) {
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
    return `${Math.floor(hrs / 24)}d ago`
  } catch { return '' }
}

const QUICK_FACTS = [
  { icon: Zap,       label: 'Multi-Model Generation',  desc: 'Up to 3 generator groups run simultaneously' },
  { icon: Users,     label: 'Review Council',          desc: 'Up to 3 reviewers per generator' },
  { icon: FileText,  label: 'Three Document Types',    desc: 'Policy · SOP · Workflow Design' },
  { icon: BarChart3, label: 'Full Audit Trail',        desc: 'Export Markdown, JSON, or ZIP' },
]

export default function Landing() {
  const navigate = useNavigate()
  const recentSessions = loadHistory().slice(0, 3)

  return (
    <div className="px-6 lg:px-10 py-8 lg:py-12 mx-auto w-full max-w-5xl space-y-10">

      {/* Workspace header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6">
        <div>
          <h1 className="text-3xl font-extrabold text-white mb-1">Workspace</h1>
          <p className="text-zinc-500 text-sm">
            Generate, review, and refine governance documents with a multi-model AI council.
          </p>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="btn-ghost flex items-center gap-2 text-sm"
          >
            <Github size={15} /> GitHub
          </a>
          <button
            onClick={() => navigate('/configure')}
            className="btn-primary flex items-center gap-2"
          >
            Start a Governance Session <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* Recent sessions */}
      {recentSessions.length > 0 ? (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">Recent Sessions</h2>
            <button
              onClick={() => navigate('/history')}
              className="btn-ghost flex items-center gap-1.5 text-xs"
            >
              <History size={12} /> View All
            </button>
          </div>
          <div className="grid sm:grid-cols-3 gap-4">
            {recentSessions.map(entry => (
              <button
                key={entry.session_id}
                onClick={() => navigate(`/results/${entry.session_id}`)}
                className="card p-5 text-left hover:border-zinc-600 transition-colors group"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-zinc-600 flex items-center gap-1">
                    <Clock size={10} /> {relativeDate(entry.saved_at)}
                  </span>
                  <span className="badge bg-zinc-800 text-zinc-400 border border-zinc-700 text-xs">
                    {DOC_BADGES[entry.document_type] ?? entry.document_type}
                  </span>
                </div>
                <p className="text-sm text-zinc-400 line-clamp-2 mb-3 group-hover:text-zinc-300 transition-colors">
                  {entry.scenario || '(no description)'}
                </p>
                <div className="flex items-center gap-2">
                  <Trophy size={13} className={scoreColour(entry.best_score)} />
                  <span className={`font-bold text-sm ${scoreColour(entry.best_score)}`}>
                    {entry.best_score?.toFixed(1)}
                  </span>
                  <span className="text-zinc-600 text-xs">/ 100</span>
                  <span className="text-zinc-700 text-xs ml-auto">
                    {entry.groups_count} group{entry.groups_count !== 1 ? 's' : ''}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </section>
      ) : (
        /* Empty state — first time */
        <div className="card p-12 text-center border-dashed border-zinc-700">
          <div className="w-14 h-14 rounded-2xl bg-brand-600/15 border border-brand-600/20 flex items-center justify-center mx-auto mb-5">
            <Zap size={26} className="text-brand-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">No sessions yet</h2>
          <p className="text-zinc-500 text-sm mb-6 max-w-sm mx-auto">
            Start your first governance session to generate a Policy, SOP, or Workflow Design
            with a multi-model review council.
          </p>
          <button
            onClick={() => navigate('/configure')}
            className="btn-primary inline-flex items-center gap-2"
          >
            Start a Governance Session <ArrowRight size={16} />
          </button>
        </div>
      )}

      {/* Platform capabilities — compact info row */}
      <section>
        <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest mb-4">Platform</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {QUICK_FACTS.map(({ icon: Icon, label, desc }) => (
            <div key={label} className="card p-4 flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-brand-600/15 border border-brand-600/20 flex items-center justify-center flex-shrink-0">
                <Icon size={16} className="text-brand-400" />
              </div>
              <div>
                <div className="text-xs font-semibold text-white mb-0.5">{label}</div>
                <div className="text-xs text-zinc-500">{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

    </div>
  )
}
