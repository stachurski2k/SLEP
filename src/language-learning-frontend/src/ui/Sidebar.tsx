import { NavLink } from 'react-router'
import { routes } from '../routes'

export default function Sidebar() {
  return (
    <aside className="border-r border-slate-400/15 bg-[#080c12]/85 px-[18px] py-6 max-[800px]:border-r-0 max-[800px]:border-b max-[800px]:px-5 max-[800px]:py-3" aria-label="Primary navigation">
      <nav><NavLink to={routes.lessons} className={({ isActive }) => ['flex items-center gap-3 rounded-[14px] border px-4 py-3.5 text-sm font-medium no-underline transition-colors', isActive ? 'border-emerald-300/30 bg-[linear-gradient(180deg,rgba(61,217,179,0.18),rgba(75,123,255,0.12))] text-white' : 'border-transparent text-[#738099] hover:border-slate-400/20 hover:bg-slate-400/5 hover:text-white'].join(' ')}><span className="grid size-6 place-items-center rounded-lg bg-white/8 text-xs" aria-hidden="true">▣</span>Lessons</NavLink></nav>
    </aside>
  )
}
