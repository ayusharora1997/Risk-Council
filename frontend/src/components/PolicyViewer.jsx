import { useState } from 'react'
import { Copy, Check } from 'lucide-react'

export default function PolicyViewer({ content = '' }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between px-5 py-3 border-b border-zinc-800">
        <span className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Policy Document</span>
        <button onClick={handleCopy} className="btn-ghost flex items-center gap-1.5 text-xs py-1.5 px-3">
          {copied ? <><Check size={13} className="text-emerald-400" /> Copied!</> : <><Copy size={13} /> Copy</>}
        </button>
      </div>
      <div className="p-6 max-h-[600px] overflow-y-auto">
        <pre className="whitespace-pre-wrap font-mono text-sm text-zinc-300 leading-relaxed">
          {content || 'No policy content available.'}
        </pre>
      </div>
    </div>
  )
}
