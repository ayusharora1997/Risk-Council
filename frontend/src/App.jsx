import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { SessionProvider } from './context/SessionContext'
import AppShell from './components/AppShell'
import Landing from './pages/Landing'
import Configure from './pages/Configure'
import Session from './pages/Session'
import Results from './pages/Results'
import History from './pages/History'

export default function App() {
  return (
    <BrowserRouter>
      <SessionProvider>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<Landing />} />
            <Route path="/configure" element={<Configure />} />
            <Route path="/session/:id" element={<Session />} />
            <Route path="/results/:id" element={<Results />} />
            <Route path="/history" element={<History />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </SessionProvider>
    </BrowserRouter>
  )
}
