import { useEffect, useState } from 'react'
import { NavLink, Link, Outlet, useLocation } from 'react-router-dom'
import { ShieldCheck, Home, Plus, History, Github, KeyRound, Activity } from 'lucide-react'
import { api } from '../api/client'

const NAV = [
  { to: '/',          label: 'Home',        icon: Home,    end: true },
  { to: '/configure', label: 'New Session', icon: Plus },
  { to: '/history',   label: 'History',     icon: History },
]

function HealthDot() {
  const [status, setStatus] = useState('checking') // checking | online | offline
  useEffect(() => {
    let alive = true
    const ping = () => api.health()
      .then(() => alive && setStatus('online'))
      .catch(() => alive && setStatus('offline'))
    ping()
    const t = setInterval(ping, 20000)
    return () => { alive = false; clearInterval(t) }
  }, [])

  const map = {
    checking: { c: 'bg-zinc-500', t: 'Connecting…' },
    online:   { c: 'bg-emerald-500', t: 'Backend online' },
    offline:  { c: 'bg-red-500', t: 'Backend offline' },
  }
  const s = map[status]
  return (
    <div className="flex items-center gap-2 text-xs text-zinc-500">
      <span className={`w-2 h-2 rounded-full ${s.c} ${status === 'online' ? 'animate-pulse-slow' : ''}`} />
      {s.t}
    </div>
  )
}

function SidebarContent() {
  return (
    <>
      {/* Brand */}
      <Link to="/" className="flex items-center gap-2.5 px-2 mb-8 group">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-900/40 group-hover:scale-105 transition-transform">
          <ShieldCheck size={20} className="text-white" />
        </div>
        <div className="leading-tight">
          <div className="font-bold text-white tracking-tight">AI Risk Council</div>
          <div className="text-[10px] text-zinc-500 uppercase tracking-widest">Governance Platform</div>
        </div>
      </Link>

      {/* Nav */}
      <nav className="space-y-1 flex-1">
        <div className="px-3 text-[10px] font-semibold text-zinc-600 uppercase tracking-widest mb-2">Workspace</div>
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
          >
            <Icon size={17} /> {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="space-y-3 pt-4 border-t border-zinc-800/80">
        <div className="card-hover card p-3">
          <div className="flex items-center gap-2 text-xs font-medium text-zinc-300 mb-1">
            <KeyRound size={13} className="text-brand-400" /> Bring your own keys
          </div>
          <p className="text-[11px] text-zinc-500 leading-snug">
            Keys run your session only and are never stored on the server.
          </p>
        </div>
        <a
          href="https://github.com"
          target="_blank"
          rel="noreferrer"
          className="nav-link text-xs"
        >
          <Github size={15} /> Get on GitHub
        </a>
        <div className="px-3">
          <HealthDot />
        </div>
      </div>
    </>
  )
}

export default function AppShell() {
  const { pathname } = useLocation()
  // Scroll content to top on route change
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])

  return (
    <div className="min-h-screen text-zinc-100">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex fixed inset-y-0 left-0 w-64 flex-col p-4 border-r border-zinc-800/70 bg-zinc-950/60 backdrop-blur-xl z-40">
        <SidebarContent />
      </aside>

      {/* Mobile top bar */}
      <header className="lg:hidden sticky top-0 z-40 flex items-center justify-between px-4 h-14 border-b border-zinc-800/70 bg-zinc-950/80 backdrop-blur-xl">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
            <ShieldCheck size={17} className="text-white" />
          </div>
          <span className="font-bold text-white text-sm">AI Risk Council</span>
        </Link>
        <nav className="flex items-center gap-1">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `p-2 rounded-lg ${isActive ? 'bg-brand-600/20 text-brand-300' : 'text-zinc-400 hover:text-white'}`}
              title={label}
            >
              <Icon size={18} />
            </NavLink>
          ))}
        </nav>
      </header>

      {/* Main content */}
      <main className="lg:pl-64 min-h-screen">
        <Outlet />
      </main>
    </div>
  )
}
