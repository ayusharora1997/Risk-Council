const API_BASE = import.meta.env.VITE_API_URL || ''

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  health: () => request('/api/health'),
  getProviders: () => request('/api/providers'),
  startSession: (payload) => request('/api/sessions', { method: 'POST', body: JSON.stringify(payload) }),
  getSession: (id) => request(`/api/sessions/${id}`),
}

/** Upload a file to the backend and get back extracted text. */
export async function uploadAttachment(file) {
  const body = new FormData()
  body.append('file', file)
  const res = await fetch(`${API_BASE}/api/attachments/parse`, { method: 'POST', body })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()  // { filename, char_count, word_count, text }
}

export function openSessionWS(sessionId, onEvent, onClose) {
  const wsBase = import.meta.env.VITE_WS_URL ||
    (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host
  const ws = new WebSocket(`${wsBase}/api/sessions/${sessionId}/ws`)
  ws.onmessage = (e) => { try { onEvent(JSON.parse(e.data)) } catch {} }
  ws.onclose = () => onClose?.()
  ws.onerror = () => onClose?.()
  return ws
}

export function exportUrl(sessionId, format) {
  return `${API_BASE}/api/sessions/${sessionId}/export/${format}`
}

/** URL for per-group exports: groupExportUrl(id, 0, 'final/docx'), etc. */
export function groupExportUrl(sessionId, groupIdx, path) {
  return `${API_BASE}/api/sessions/${sessionId}/export/group/${groupIdx}/${path}`
}
