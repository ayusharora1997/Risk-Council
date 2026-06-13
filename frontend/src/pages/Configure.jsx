import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ChevronRight, ChevronLeft, Plus, Trash2, Eye, EyeOff,
  Loader2, Upload, X, FileText, FileSpreadsheet, File,
} from 'lucide-react'
import { api, uploadAttachment } from '../api/client'
import { useSession } from '../context/SessionContext'

// ── Static data ───────────────────────────────────────────────────────────────

const PROVIDERS = {
  openai:     { label: 'OpenAI',          models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'], keyLabel: 'OPENAI_API_KEY' },
  anthropic:  { label: 'Anthropic',       models: ['claude-opus-4-8', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001'], keyLabel: 'ANTHROPIC_API_KEY' },
  gemini:     { label: 'Gemini',          models: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'], keyLabel: 'GOOGLE_API_KEY' },
  openrouter: { label: 'OpenRouter',      models: ['meta-llama/llama-3.3-70b-instruct', 'mistralai/mistral-7b-instruct', 'deepseek/deepseek-r1'], keyLabel: 'OPENROUTER_API_KEY' },
  ollama:     { label: 'Ollama (local)',  models: ['llama3.2', 'mistral', 'gemma2', 'phi3'], keyLabel: null },
}

const DOC_TYPES = [
  {
    id: 'policy',
    label: 'Policy',
    desc: 'Enterprise governance policies — controls, compliance, RACI, enforcement.',
    icon: '📋',
  },
  {
    id: 'sop',
    label: 'SOP',
    desc: 'Standard Operating Procedures — numbered steps, decision points, quality checks.',
    icon: '📝',
  },
  {
    id: 'workflow',
    label: 'Workflow Design',
    desc: 'Process flow design — swim lanes, decision gates, SLAs, integration points.',
    icon: '🔀',
  },
]

const STEPS = ['Scenario', 'Attachments', 'API Keys', 'Generators', 'Launch']

const ACCEPTED_TYPES = '.pdf,.docx,.doc,.xlsx,.xls,.txt,.md,.csv'

const FILE_ICONS = {
  pdf: FileText,
  docx: FileText, doc: FileText,
  xlsx: FileSpreadsheet, xls: FileSpreadsheet,
  txt: File, md: File, csv: File,
}

function fileExt(name) { return name.split('.').pop().toLowerCase() }

function defaultGroup(i) {
  const providers = ['openai', 'anthropic', 'gemini']
  const p = providers[i % providers.length]
  return {
    provider: p,
    model: PROVIDERS[p].models[0],
    reviewers: [{ provider: 'openai', model: 'gpt-4o-mini' }],
  }
}

const DEFAULT_FORM = {
  scenario: '',
  documentType: 'policy',
  attachment: null,       // { filename, text, word_count, char_count }
  apiKeys: { openai: '', anthropic: '', gemini: '', openrouter: '' },
  generatorGroups: [defaultGroup(0)],
  targetScore: 85,
  maxIterations: 5,
}

// ── Small reusable components ─────────────────────────────────────────────────

const STEP_HINTS = [
  'What you want and which document type',
  'Optional reference file',
  'Your provider API keys',
  'Models & reviewers',
  'Confirm & run',
]

/** Vertical, clickable step rail. Any step up to `maxStep` can be jumped to. */
function StepRail({ current, maxStep, labels, onSelect }) {
  return (
    <nav className="space-y-1">
      {labels.map((label, i) => {
        const done = i < current
        const active = i === current
        const reachable = i <= maxStep
        return (
          <button
            key={i}
            type="button"
            disabled={!reachable}
            onClick={() => reachable && onSelect(i)}
            className={`w-full flex items-start gap-3 rounded-xl px-3 py-2.5 text-left transition-all
              ${active ? 'bg-brand-600/10 ring-1 ring-brand-500/40' : reachable ? 'hover:bg-zinc-800/60 cursor-pointer' : 'opacity-50 cursor-not-allowed'}`}
          >
            <div className={`mt-0.5 w-7 h-7 flex-shrink-0 rounded-full flex items-center justify-center text-xs font-bold transition-all
              ${done ? 'bg-brand-600 text-white' : active ? 'bg-brand-600 text-white ring-4 ring-brand-600/20' : 'bg-zinc-800 text-zinc-500'}`}>
              {done ? '✓' : i + 1}
            </div>
            <div className="min-w-0">
              <div className={`text-sm font-medium leading-tight ${active ? 'text-brand-300' : done ? 'text-zinc-300' : 'text-zinc-500'}`}>
                {label}
              </div>
              <div className="text-xs text-zinc-600 mt-0.5 leading-snug">{STEP_HINTS[i]}</div>
            </div>
          </button>
        )
      })}
    </nav>
  )
}

/** Compact horizontal rail for narrow / mobile viewports. */
function StepRailMobile({ current, maxStep, total, labels, onSelect }) {
  return (
    <div className="flex items-center gap-0 lg:hidden mb-8">
      {labels.map((label, i) => {
        const reachable = i <= maxStep
        return (
          <div key={i} className="flex items-center">
            <button
              type="button"
              disabled={!reachable}
              onClick={() => reachable && onSelect(i)}
              className="flex flex-col items-center disabled:cursor-not-allowed"
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all
                ${i < current ? 'bg-brand-600 text-white' : i === current ? 'bg-brand-600 text-white ring-4 ring-brand-600/20' : 'bg-zinc-800 text-zinc-500'}`}>
                {i < current ? '✓' : i + 1}
              </div>
              <span className={`text-xs mt-1.5 hidden sm:block ${i === current ? 'text-brand-400' : 'text-zinc-600'}`}>{label}</span>
            </button>
            {i < total - 1 && (
              <div className={`h-px w-8 sm:w-12 mx-1 mb-4 ${i < current ? 'bg-brand-600' : 'bg-zinc-800'}`} />
            )}
          </div>
        )
      })}
    </div>
  )
}

function KeyInput({ value, onChange, placeholder }) {
  const [show, setShow] = useState(false)
  return (
    <div className="relative">
      <input
        type={show ? 'text' : 'password'}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="input pr-12 font-mono text-sm"
      />
      <button type="button" onClick={() => setShow(s => !s)}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300">
        {show ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </div>
  )
}

function ProviderModelSelect({ value, onChange, label }) {
  return (
    <div className="grid grid-cols-2 gap-3">
      <div>
        <label className="label">{label} Provider</label>
        <select
          value={value.provider}
          onChange={e => onChange({ provider: e.target.value, model: PROVIDERS[e.target.value].models[0] })}
          className="input"
        >
          {Object.entries(PROVIDERS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
      </div>
      <div>
        <label className="label">Model</label>
        <select
          value={value.model}
          onChange={e => onChange({ ...value, model: e.target.value })}
          className="input"
        >
          {PROVIDERS[value.provider].models.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>
    </div>
  )
}

// ── Generator Group Card ──────────────────────────────────────────────────────

function GeneratorGroupCard({ group, index, onChange, onRemove, canRemove }) {
  const updateGenerator = (val) => onChange({ ...group, provider: val.provider, model: val.model })
  const addReviewer = () => {
    if (group.reviewers.length >= 3) return
    onChange({ ...group, reviewers: [...group.reviewers, { provider: 'openai', model: 'gpt-4o-mini' }] })
  }
  const removeReviewer = (i) => onChange({ ...group, reviewers: group.reviewers.filter((_, j) => j !== i) })
  const updateReviewer = (i, val) => onChange({
    ...group,
    reviewers: group.reviewers.map((r, j) => j === i ? val : r),
  })

  return (
    <div className="card p-5 space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-brand-600/20 border border-brand-600/30 flex items-center justify-center text-xs font-bold text-brand-400">
            {index + 1}
          </div>
          <span className="font-semibold text-white">Generator {index + 1}</span>
        </div>
        {canRemove && (
          <button onClick={onRemove} className="p-1.5 rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-900/20 transition-colors">
            <Trash2 size={14} />
          </button>
        )}
      </div>

      <ProviderModelSelect
        label="Generator"
        value={{ provider: group.provider, model: group.model }}
        onChange={updateGenerator}
      />

      <div className="border-t border-zinc-800 pt-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
            Reviewers ({group.reviewers.length}/3)
          </span>
          {group.reviewers.length < 3 && (
            <button onClick={addReviewer} className="flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300 transition-colors">
              <Plus size={12} /> Add Reviewer
            </button>
          )}
        </div>

        {group.reviewers.map((r, i) => (
          <div key={i} className="flex gap-2 items-end">
            <div className="flex-1">
              <ProviderModelSelect
                label={`Reviewer ${i + 1}`}
                value={r}
                onChange={(val) => updateReviewer(i, val)}
              />
            </div>
            {group.reviewers.length > 1 && (
              <button
                onClick={() => removeReviewer(i)}
                className="mb-0.5 p-2.5 rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-900/20 transition-colors"
              >
                <Trash2 size={14} />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function Configure() {
  const navigate = useNavigate()
  const { dispatch } = useSession()
  const [step, setStep] = useState(0)
  const [maxStep, setMaxStep] = useState(0)   // furthest step reached → controls which steps are clickable
  const [form, setForm] = useState(DEFAULT_FORM)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef()

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  // Move to a step and remember the furthest one we've reached
  const goToStep = (target) => {
    setStep(target)
    setMaxStep(m => Math.max(m, target))
    setError(null)
  }

  // ── Step 0: Scenario + Document Type ──────────────────────────────────

  const Step0 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-1">Describe your scenario</h2>
        <p className="text-zinc-500 text-sm">The more context you provide, the better the generated document.</p>
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* Scenario — takes the larger share */}
        <div className="lg:col-span-3 flex flex-col">
          <label className="label">Scenario</label>
          <textarea
            value={form.scenario}
            onChange={e => set('scenario', e.target.value)}
            placeholder="e.g. We need an AI hiring algorithm policy for a global bank covering fairness, bias prevention, GDPR compliance, and audit requirements…"
            className="input resize-none flex-1 min-h-[260px]"
          />
          <div className="text-xs text-zinc-600 text-right mt-1.5">{form.scenario.length} chars</div>
        </div>

        {/* Document type — stacked cards on the side */}
        <div className="lg:col-span-2">
          <label className="label mb-3">Document Type</label>
          <div className="space-y-3">
            {DOC_TYPES.map(dt => (
              <button
                key={dt.id}
                type="button"
                onClick={() => set('documentType', dt.id)}
                className={`w-full p-4 rounded-xl border text-left transition-all flex gap-3 items-start ${
                  form.documentType === dt.id
                    ? 'border-brand-500 bg-brand-600/10 ring-1 ring-brand-500/40'
                    : 'border-zinc-700 bg-zinc-800/50 hover:border-zinc-600'
                }`}
              >
                <div className="text-2xl">{dt.icon}</div>
                <div>
                  <div className="font-semibold text-white text-sm mb-0.5">{dt.label}</div>
                  <div className="text-xs text-zinc-500 leading-relaxed">{dt.desc}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )

  // ── Step 1: Attachments ────────────────────────────────────────────────

  const handleFileSelect = async (file) => {
    if (!file) return
    setUploadError(null)
    setUploading(true)
    try {
      const result = await uploadAttachment(file)
      set('attachment', result)
    } catch (e) {
      setUploadError(e.message)
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) handleFileSelect(file)
  }

  const Step1 = () => {
    const att = form.attachment
    const IconComp = att ? (FILE_ICONS[fileExt(att.filename)] || File) : null

    return (
      <div className="space-y-5">
        <div>
          <h2 className="text-2xl font-bold mb-1">Reference Document</h2>
          <p className="text-zinc-500 text-sm">
            Optional — upload an existing SOP, policy, or process document. The AI will use it as a
            reference when building your new document.
          </p>
        </div>

        <p className="text-xs text-zinc-600">
          Accepted: PDF, Word (.docx), Excel (.xlsx), Plain text (.txt, .md, .csv) · Max 10 MB
        </p>

        {!att ? (
          <div
            onDrop={handleDrop}
            onDragOver={e => e.preventDefault()}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-zinc-700 hover:border-brand-600 rounded-xl p-10 flex flex-col items-center gap-3 cursor-pointer transition-colors group"
          >
            {uploading ? (
              <Loader2 size={32} className="text-brand-400 animate-spin" />
            ) : (
              <Upload size={32} className="text-zinc-600 group-hover:text-brand-400 transition-colors" />
            )}
            <div className="text-center">
              <p className="text-sm text-zinc-400 group-hover:text-zinc-300 transition-colors">
                {uploading ? 'Extracting text…' : 'Drag & drop a file here, or click to browse'}
              </p>
            </div>
          </div>
        ) : (
          <div className="card p-5 flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-brand-600/15 border border-brand-600/20 flex items-center justify-center flex-shrink-0">
              <IconComp size={18} className="text-brand-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-white truncate">{att.filename}</div>
              <div className="text-xs text-zinc-500 mt-0.5">
                {att.word_count.toLocaleString()} words · {att.char_count.toLocaleString()} chars extracted
              </div>
              <div className="mt-3 bg-zinc-800 rounded-lg p-3 text-xs text-zinc-400 font-mono max-h-28 overflow-y-auto leading-relaxed">
                {att.text.slice(0, 600)}{att.text.length > 600 ? '…' : ''}
              </div>
            </div>
            <button
              onClick={() => set('attachment', null)}
              className="p-1.5 rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-900/20 transition-colors flex-shrink-0"
            >
              <X size={14} />
            </button>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_TYPES}
          className="hidden"
          onChange={e => handleFileSelect(e.target.files?.[0])}
        />

        {uploadError && (
          <div className="card p-3 border-red-800/50 bg-red-950/20 text-red-400 text-sm">{uploadError}</div>
        )}

        <p className="text-xs text-zinc-600 italic">
          You can skip this step — it is completely optional.
        </p>
      </div>
    )
  }

  // ── Step 2: API Keys ───────────────────────────────────────────────────

  const Step2 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-1">API Keys</h2>
        <p className="text-zinc-500 text-sm">Keys are sent to the backend for this session only — never persisted.</p>
      </div>
      {error && (
        <div className="card p-4 border-red-800/50 bg-red-950/20 text-red-400 text-sm">{error}</div>
      )}
      {Object.entries(PROVIDERS).filter(([, v]) => v.keyLabel).map(([k, v]) => (
        <div key={k}>
          <label className="label">{v.label} <span className="text-zinc-600 font-normal">— {v.keyLabel}</span></label>
          <KeyInput
            value={form.apiKeys[k] || ''}
            onChange={val => set('apiKeys', { ...form.apiKeys, [k]: val })}
            placeholder={`Enter your ${v.label} API key…`}
          />
        </div>
      ))}
      <p className="text-xs text-zinc-600">This is an open platform — keys are sent only to run your session and are never stored.</p>
    </div>
  )

  // ── Step 3: Generator Groups ───────────────────────────────────────────

  const Step3 = () => (
    <div className="space-y-5">
      <div>
        <h2 className="text-2xl font-bold mb-1">Generator Groups</h2>
        <p className="text-zinc-500 text-sm">
          Each group runs the full generate → review → improve cycle independently.
          Add up to 3 groups to compare outputs from different models.
        </p>
      </div>

      <div className={`grid gap-4 ${form.generatorGroups.length > 1 ? 'xl:grid-cols-2' : ''}`}>
        {form.generatorGroups.map((grp, i) => (
          <GeneratorGroupCard
            key={i}
            group={grp}
            index={i}
            canRemove={form.generatorGroups.length > 1}
            onChange={val => set('generatorGroups', form.generatorGroups.map((g, j) => j === i ? val : g))}
            onRemove={() => set('generatorGroups', form.generatorGroups.filter((_, j) => j !== i))}
          />
        ))}
      </div>

      {form.generatorGroups.length < 3 && (
        <button
          onClick={() => set('generatorGroups', [...form.generatorGroups, defaultGroup(form.generatorGroups.length)])}
          className="btn-ghost flex items-center gap-2 text-sm w-full justify-center border border-dashed border-zinc-700 hover:border-brand-600"
        >
          <Plus size={15} /> Add Generator Group ({form.generatorGroups.length}/3)
        </button>
      )}
    </div>
  )

  // ── Step 4: Launch ─────────────────────────────────────────────────────

  const Step4 = () => {
    const docType = DOC_TYPES.find(d => d.id === form.documentType)
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Review & Launch</h2>

        <div className="grid sm:grid-cols-2 gap-4">
          <div className="card p-4">
            <div className="label mb-2">Target Score</div>
            <input type="number" min={50} max={100} value={form.targetScore}
              onChange={e => set('targetScore', Number(e.target.value))}
              className="input" />
            <p className="text-xs text-zinc-600 mt-1.5">Session stops when this score is reached.</p>
          </div>
          <div className="card p-4">
            <div className="label mb-2">Max Iterations</div>
            <input type="number" min={1} max={10} value={form.maxIterations}
              onChange={e => set('maxIterations', Number(e.target.value))}
              className="input" />
            <p className="text-xs text-zinc-600 mt-1.5">Hard cap on generate-review cycles.</p>
          </div>
        </div>

        <div className="card p-5 space-y-4 text-sm">
          <div className="flex justify-between items-center">
            <span className="text-zinc-500">Document Type</span>
            <span className="text-zinc-300">{docType?.icon} {docType?.label}</span>
          </div>
          {form.attachment && (
            <div className="flex justify-between items-center">
              <span className="text-zinc-500">Reference File</span>
              <span className="text-zinc-300 font-mono text-xs">{form.attachment.filename} ({form.attachment.word_count.toLocaleString()} words)</span>
            </div>
          )}
          {form.generatorGroups.map((g, i) => (
            <div key={i} className="border-t border-zinc-800 pt-3">
              <div className="flex justify-between mb-1.5">
                <span className="text-zinc-500">Generator {i + 1}</span>
                <span className="font-mono text-zinc-300">{g.provider} / {g.model}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-600 text-xs">Reviewers</span>
                <div className="text-right space-y-0.5">
                  {g.reviewers.map((r, j) => (
                    <div key={j} className="font-mono text-zinc-500 text-xs">{r.provider} / {r.model}</div>
                  ))}
                </div>
              </div>
            </div>
          ))}
          <div className="flex justify-between border-t border-zinc-800 pt-3">
            <span className="text-zinc-500">Target / Max</span>
            <span className="text-zinc-300">{form.targetScore} pts / {form.maxIterations} iterations</span>
          </div>
        </div>

        {error && (
          <div className="card p-4 border-red-800/50 bg-red-950/20 text-red-400 text-sm">{error}</div>
        )}
      </div>
    )
  }

  // ── Navigation ─────────────────────────────────────────────────────────

  const canNext = () => {
    if (step === 0) return form.scenario.trim().length >= 20
    return true
  }

  const handleLaunch = async () => {
    // ── API-key guard: this is an open, bring-your-own-key platform ──────
    const providersInUse = new Set()
    form.generatorGroups.forEach(g => {
      providersInUse.add(g.provider)
      g.reviewers.forEach(r => providersInUse.add(r.provider))
    })
    // Ollama runs locally and needs no key
    const keyRequired = [...providersInUse].filter(p => p !== 'ollama')
    const anyKeyProvided = Object.values(form.apiKeys).some(v => v && v.trim())

    if (keyRequired.length > 0 && !anyKeyProvided) {
      setStep(2)  // jump back to the API Keys step
      setError('This is an open, bring-your-own-key platform — no keys are stored on the server. Please provide at least one API key to run a session.')
      return
    }

    const missing = keyRequired.filter(p => !(form.apiKeys[p] && form.apiKeys[p].trim()))
    if (missing.length > 0) {
      const labels = missing.map(p => PROVIDERS[p]?.label ?? p).join(', ')
      setStep(2)  // jump back to the API Keys step
      setError(`This is an open platform and requires API keys for every provider you use. Missing key${missing.length > 1 ? 's' : ''} for: ${labels}.`)
      return
    }

    setLoading(true)
    setError(null)
    try {
      const payload = {
        scenario: form.scenario,
        document_type: form.documentType,
        reference_content: form.attachment?.text ?? null,
        target_score: form.targetScore,
        max_iterations: form.maxIterations,
        generator_groups: form.generatorGroups.map(g => ({
          generator: { provider: g.provider, model: g.model },
          reviewers: g.reviewers,
        })),
        api_keys: form.apiKeys,
      }
      const { session_id } = await api.startSession(payload)
      dispatch({ type: 'START', sessionId: session_id, config: payload })
      navigate(`/session/${session_id}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const STEP_RENDERERS = [Step0, Step1, Step2, Step3, Step4]

  return (
    <div className="px-6 lg:px-10 py-8 lg:py-10 mx-auto w-full max-w-6xl">
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-2xl lg:text-3xl font-extrabold tracking-tight">New Governance Session</h1>
        <p className="text-zinc-500 text-sm mt-1">Configure your generators, reviewers, and target — then launch.</p>
      </div>

      {/* Mobile / narrow: horizontal rail on top */}
      <StepRailMobile
        current={step}
        maxStep={maxStep}
        total={STEPS.length}
        labels={STEPS}
        onSelect={goToStep}
      />

      <div className="lg:grid lg:grid-cols-[260px_1fr] lg:gap-8">
        {/* Sidebar rail (desktop) */}
        <aside className="hidden lg:block">
          <div className="sticky top-8 card p-4">
            <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest px-3 mb-3">Setup</h3>
            <StepRail current={step} maxStep={maxStep} labels={STEPS} onSelect={goToStep} />
          </div>
        </aside>

        {/* Content column */}
        <div>
          <div className="card p-8 animate-slide-up min-h-[420px]">
            {STEP_RENDERERS[step]()}
          </div>

          <div className="flex justify-between mt-6">
            <button
              onClick={() => goToStep(step - 1)}
              disabled={step === 0}
              className="btn-ghost flex items-center gap-2 disabled:opacity-0"
            >
              <ChevronLeft size={16} /> Back
            </button>

            {step < STEPS.length - 1 ? (
              <button
                onClick={() => goToStep(step + 1)}
                disabled={!canNext()}
                className="btn-primary flex items-center gap-2"
              >
                Next <ChevronRight size={16} />
              </button>
            ) : (
              <button
                onClick={handleLaunch}
                disabled={loading}
                className="btn-primary flex items-center gap-2 min-w-[160px] justify-center"
              >
                {loading ? <><Loader2 size={16} className="animate-spin" /> Starting…</> : '🚀 Launch Session'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
