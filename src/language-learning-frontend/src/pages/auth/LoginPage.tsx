import { type FormEvent, useState } from 'react'
import { useLocation, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { login, register } from '../../api/auth'
import { useAuth } from '../../auth/useAuth'
import { inputClass, panelClass, primaryButtonClass } from '../../components/ui/classes'
import { routes } from '../../router/routes'

type AuthMode = 'login' | 'register'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { establishSession } = useAuth()

  const initialMode: AuthMode = location.pathname === routes.register ? 'register' : 'login'
  const [mode, setMode] = useState<AuthMode>(initialMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirmation, setPasswordConfirmation] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const switchMode = (nextMode: AuthMode) => {
    setMode(nextMode)
    navigate(nextMode === 'register' ? routes.register : routes.login, { replace: true })
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const trimmedEmail = email.trim()
    if (!trimmedEmail || !password) {
      toast.error('Please enter your email and password.')
      return
    }

    if (mode === 'register') {
      if (password.length < 8) {
        toast.error('Password must be at least 8 characters long.')
        return
      }
      if (password !== passwordConfirmation) {
        toast.error('Passwords do not match.')
        return
      }
    }

    setIsSubmitting(true)
    try {
      const response =
        mode === 'login'
          ? await login({ email: trimmedEmail, password })
          : await register({
              email: trimmedEmail,
              password,
              passwordConfirmation,
            })

      establishSession(response)
      toast.success(mode === 'login' ? 'Logged in successfully.' : 'Account created successfully.')
      navigate(routes.lessons, { replace: true })
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : 'Authentication failed. Please check your credentials.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_20%_15%,rgba(52,211,153,0.16),transparent_27%),radial-gradient(circle_at_80%_80%,rgba(70,101,255,0.14),transparent_30%),#070b12] p-5">
      <form className={`${panelClass} w-full max-w-[440px] p-8`} onSubmit={(event) => void handleSubmit(event)}>
        <div className="mb-7 flex items-center gap-3">
          <span className="grid size-11 place-items-center rounded-xl bg-[linear-gradient(135deg,#39d5ab,#4778ff)] text-xl font-bold text-white">
            S
          </span>
          <div>
            <p className="m-0 text-xs tracking-[0.14em] text-[#738099] uppercase">SLEP</p>
            <h1 className="m-0 text-xl font-semibold text-white">Sign language learning</h1>
          </div>
        </div>

        <div className="mb-6 grid grid-cols-2 gap-1.5 rounded-xl border border-slate-400/15 bg-[#070b12]/80 p-1">
          <button
            type="button"
            onClick={() => switchMode('login')}
            className={`cursor-pointer rounded-lg py-2 text-sm font-medium transition ${
              mode === 'login'
                ? 'bg-slate-400/15 text-white shadow-sm'
                : 'text-[#738099] hover:text-white'
            }`}
          >
            Log in
          </button>
          <button
            type="button"
            onClick={() => switchMode('register')}
            className={`cursor-pointer rounded-lg py-2 text-sm font-medium transition ${
              mode === 'register'
                ? 'bg-slate-400/15 text-white shadow-sm'
                : 'text-[#738099] hover:text-white'
            }`}
          >
            Create account
          </button>
        </div>

        <h2 className="m-0 text-3xl font-semibold tracking-tight text-white">
          {mode === 'login' ? 'Welcome back' : 'Create your account'}
        </h2>
        <p className="mt-2 text-sm leading-6 text-[#a8b0c3]">
          {mode === 'login'
            ? 'Log in to continue your sign language practice.'
            : 'Sign up with your email to start learning sign language.'}
        </p>

        <div className="mt-6 grid gap-4">
          <label className="grid gap-2 text-sm font-medium text-[#dce2ee]">
            Email
            <input
              className={inputClass}
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              placeholder="you@example.com"
              required
            />
          </label>
          <label className="grid gap-2 text-sm font-medium text-[#dce2ee]">
            Password
            <input
              className={inputClass}
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              placeholder="At least 8 characters"
              minLength={mode === 'register' ? 8 : undefined}
              required
            />
          </label>
          {mode === 'register' && (
            <label className="grid gap-2 text-sm font-medium text-[#dce2ee]">
              Confirm password
              <input
                className={inputClass}
                type="password"
                value={passwordConfirmation}
                onChange={(event) => setPasswordConfirmation(event.target.value)}
                autoComplete="new-password"
                placeholder="Repeat your password"
                minLength={8}
                required
              />
            </label>
          )}
        </div>

        <button className={`${primaryButtonClass} mt-7 w-full`} type="submit" disabled={isSubmitting}>
          {isSubmitting
            ? mode === 'login'
              ? 'Logging in…'
              : 'Creating account…'
            : mode === 'login'
              ? 'Log in'
              : 'Create account'}
        </button>
      </form>
    </div>
  )
}
