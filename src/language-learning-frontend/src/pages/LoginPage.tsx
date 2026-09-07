import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { routes } from '../routes'
import { panelClass, primaryButtonClass } from '../ui/classes'

type LoginPageProps = { onLogIn: () => void }

export default function LoginPage({ onLogIn }: LoginPageProps) {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (username !== 'admin' || password !== 'admin') {
      toast.error('Incorrect username or password.')
      return
    }
    onLogIn()
    navigate(routes.lessons, { replace: true })
  }

  return (
    <div className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_20%_15%,rgba(52,211,153,0.16),transparent_27%),radial-gradient(circle_at_80%_80%,rgba(70,101,255,0.14),transparent_30%),#070b12] p-5">
      <form className={`${panelClass} w-full max-w-[430px] p-8`} onSubmit={handleSubmit}>
        <div className="mb-8 flex items-center gap-3"><span className="grid size-11 place-items-center rounded-xl bg-[linear-gradient(135deg,#39d5ab,#4778ff)] text-xl font-bold text-white">S</span><div><p className="m-0 text-xs tracking-[0.14em] text-[#738099] uppercase">SLEP</p><h1 className="m-0 text-xl font-semibold text-white">Sign language learning</h1></div></div>
        <h2 className="m-0 text-3xl font-semibold tracking-tight text-white">Welcome back</h2>
        <p className="mt-2 text-sm leading-6 text-[#a8b0c3]">Log in to continue your sign language practice.</p>
        <div className="mt-7 grid gap-4">
          <label className="grid gap-2 text-sm font-medium text-[#dce2ee]">Username<input className="rounded-xl border border-slate-400/15 bg-[#070b12]/90 px-3.5 py-3 text-white outline-none transition focus:border-emerald-300/50" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" /></label>
          <label className="grid gap-2 text-sm font-medium text-[#dce2ee]">Password<input className="rounded-xl border border-slate-400/15 bg-[#070b12]/90 px-3.5 py-3 text-white outline-none transition focus:border-emerald-300/50" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" /></label>
        </div>
        <button className={`${primaryButtonClass} mt-7 w-full`} type="submit">Log in</button>
        <p className="mt-4 text-center text-xs text-[#738099]">Demo credentials: <span className="text-[#c7d0e2]">admin / admin</span></p>
      </form>
    </div>
  )
}
