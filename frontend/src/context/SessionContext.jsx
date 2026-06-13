import { createContext, useContext, useReducer } from 'react'

const Ctx = createContext(null)

// ── localStorage history helpers ──────────────────────────────────────────────

const HISTORY_KEY = 'arc_session_history'
const MAX_HISTORY = 20

export function saveSessionToHistory(entry) {
  try {
    const existing = loadHistory()
    const next = [entry, ...existing.filter(e => e.session_id !== entry.session_id)]
    localStorage.setItem(HISTORY_KEY, JSON.stringify(next.slice(0, MAX_HISTORY)))
  } catch {}
}

export function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
  } catch {
    return []
  }
}

// ── State shape ───────────────────────────────────────────────────────────────

const INITIAL = {
  sessionId: null,
  status: 'idle',          // idle | running | complete | error
  targetScore: 85,
  error: null,
  config: null,
  // per-group tracking: { [groupIndex]: { iterations, bestScore, currentIteration, status, generator } }
  groups: {},
  groupsTotal: 0,
  overallBestScore: 0,
  overallBestGroupIndex: 0,
}

function groupInitial(generator) {
  return { iterations: [], bestScore: 0, currentIteration: 0, status: 'pending', generator, currentPhase: null }
}

// ── Reducer ───────────────────────────────────────────────────────────────────

function reducer(state, action) {
  switch (action.type) {

    case 'START':
      return {
        ...INITIAL,
        sessionId: action.sessionId,
        status: 'running',
        config: action.config,
        targetScore: action.config?.target_score ?? 85,
      }

    case 'EVENT': {
      const p = action.payload
      const gi = p.group_index ?? 0

      if (p.phase === 'group_start') {
        return {
          ...state,
          groupsTotal: p.groups_total ?? 1,
          groups: {
            ...state.groups,
            [gi]: { ...groupInitial(p.generator), currentPhase: 'generating' },
          },
        }
      }

      // Phase-only events: update currentPhase on the group
      if (p.phase === 'initial_generated' || p.phase === 'reviewing' || p.phase === 'improving') {
        const g = state.groups[gi] || groupInitial('')
        const phaseMap = {
          initial_generated: 'reviewing',
          reviewing: 'reviewing',
          improving: 'improving',
        }
        return {
          ...state,
          groups: {
            ...state.groups,
            [gi]: { ...g, status: 'running', currentPhase: phaseMap[p.phase] },
          },
        }
      }

      if (p.phase === 'iteration_complete') {
        const g = state.groups[gi] || groupInitial('')
        return {
          ...state,
          overallBestScore: Math.max(state.overallBestScore, p.best_score),
          groups: {
            ...state.groups,
            [gi]: {
              ...g,
              currentIteration: p.iteration,
              bestScore: p.best_score,
              status: 'running',
              currentPhase: 'iteration_complete',
              iterations: [...g.iterations, p],
            },
          },
        }
      }

      if (p.phase === 'group_complete') {
        const g = state.groups[gi] || groupInitial('')
        return {
          ...state,
          groups: {
            ...state.groups,
            [gi]: { ...g, status: 'complete', currentPhase: 'complete' },
          },
        }
      }

      if (p.phase === 'done') {
        return {
          ...state,
          status: 'complete',
          overallBestScore: p.overall_best_score ?? state.overallBestScore,
          overallBestGroupIndex: p.overall_best_group_index ?? 0,
        }
      }

      if (p.phase === 'error') {
        return { ...state, status: 'error', error: p.error }
      }

      return state
    }

    case 'RESET':
      return { ...INITIAL }

    default:
      return state
  }
}

// ── Provider ─────────────────────────────────────────────────────────────────

export function SessionProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, INITIAL)
  return <Ctx.Provider value={{ state, dispatch }}>{children}</Ctx.Provider>
}

export function useSession() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useSession must be used inside SessionProvider')
  return ctx
}
