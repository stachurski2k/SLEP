import { Outlet } from 'react-router'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function AppLayout() {
  return (
    <div className="grid min-h-screen grid-rows-[auto_1fr] bg-[radial-gradient(circle_at_top_left,rgba(52,211,153,0.12),transparent_28%),radial-gradient(circle_at_top_right,rgba(59,130,246,0.13),transparent_30%),linear-gradient(180deg,#0c121c,#080c12)]">
      <Topbar />
      <div className="grid min-h-0 grid-cols-[236px_minmax(0,1fr)] max-[800px]:grid-cols-1">
        <Sidebar />
        <main className="min-w-0 p-6 max-[800px]:p-5">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
