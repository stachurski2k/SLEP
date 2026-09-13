import { useNavigate } from 'react-router'
import { routes } from '../routes'

type TopbarProps = { onLogOut: () => void }

export default function Topbar({ onLogOut }: TopbarProps) {
  const navigate = useNavigate()
  const handleLogOut = () => {
    onLogOut()
    navigate(routes.login, { replace: true })
  }

  return (
    <header className="flex min-h-[76px] items-center justify-between border-b border-slate-400/15 bg-[#070b12]/70 px-7 backdrop-blur-[18px] max-[640px]:px-5">
      <div className="flex items-center gap-3.5">
        <span className="grid size-10 place-items-center rounded-xl bg-[linear-gradient(135deg,#39d5ab,#4778ff)] text-lg font-bold text-white shadow-[0_0_24px_rgba(75,123,255,0.4)]">S</span>
        <div><p className="m-0 text-[0.72rem] tracking-[0.14em] text-[#738099] uppercase">SLEP</p><h1 className="m-0 text-xl font-semibold text-[#f5f7fb]">Sign language learning</h1></div>
      </div>
      <button type="button" className="cursor-pointer rounded-xl border border-slate-400/15 bg-slate-400/5 px-3.5 py-2 text-sm text-[#a8b0c3] transition hover:border-emerald-300/35 hover:text-white" onClick={handleLogOut}>Log out</button>
    </header>
  )
}
