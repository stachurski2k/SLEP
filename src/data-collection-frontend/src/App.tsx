import { Toaster } from 'sonner'
import AppRoutes from './AppRoutes'
import Navbar from './ui/Navbar'
import Topbar from './ui/Topbar'

function App() {
  return (
    <div className="grid min-h-screen grid-rows-[auto_1fr] bg-[radial-gradient(circle_at_top_left,rgba(52,211,153,0.12),transparent_28%),radial-gradient(circle_at_top_right,rgba(59,130,246,0.14),transparent_30%),linear-gradient(180deg,rgba(12,18,28,0.96),rgba(8,12,18,1))]">
      <Topbar />
      <div className="grid min-h-0 grid-cols-[240px_minmax(0,1fr)] max-[900px]:grid-cols-1">
        <Navbar />
        <main className="min-w-0 p-6 max-[900px]:p-5">
          <AppRoutes />
        </main>
      </div>
      <Toaster richColors theme="dark" position="top-right" />
    </div>
  )
}

export default App
