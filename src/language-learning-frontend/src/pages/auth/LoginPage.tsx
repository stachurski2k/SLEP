import { type FormEvent, useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { login, loginWithGoogle, register } from '../../api/auth'
import { useAuth } from '../../auth/useAuth'
import { inputClass, panelClass, primaryButtonClass } from '../../components/ui/classes'
import { routes } from '../../router/routes'

type AuthMode = 'login' | 'register'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { establishSession } = useAuth()

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined
  const googleButtonContainerRef = useRef<HTMLDivElement>(null)

  const initialMode: AuthMode = location.pathname === routes.register ? 'register' : 'login'
  const [mode, setMode] = useState<AuthMode>(initialMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirmation, setPasswordConfirmation] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [gsiLoaded, setGsiLoaded] = useState(false)

  const switchMode = (nextMode: AuthMode) => {
    setMode(nextMode)
    navigate(nextMode === 'register' ? routes.register : routes.login, { replace: true })
  }

  useEffect(() => {
    if (!googleClientId) return

    const initGsi = () => {
      if (!window.google?.accounts?.id || !googleButtonContainerRef.current) return

      try {
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: async (response) => {
            if (!response.credential) {
              toast.error('Google did not return an authentication token.')
              return
            }
            setIsSubmitting(true)
            try {
              const res = await loginWithGoogle({ idToken: response.credential })
              establishSession(res)
              toast.success(`Logged in with Google as ${res.email}.`)
              navigate(routes.lessons, { replace: true })
            } catch (error) {
              toast.error(
                error instanceof Error ? error.message : 'Google authentication failed.',
              )
            } finally {
              setIsSubmitting(false)
            }
          },
        })

        googleButtonContainerRef.current.innerHTML = ''
        window.google.accounts.id.renderButton(googleButtonContainerRef.current, {
          theme: 'filled_black',
          size: 'large',
          text: 'continue_with',
          shape: 'rectangular',
          width: '100%',
        })
        setGsiLoaded(true)
      } catch (err) {
        console.error('Failed to initialize Google Sign-In:', err)
      }
    }

    if (window.google?.accounts?.id) {
      initGsi()
    } else {
      const interval = window.setInterval(() => {
        if (window.google?.accounts?.id) {
          window.clearInterval(interval)
          initGsi()
        }
      }, 250)
      return () => window.clearInterval(interval)
    }
  }, [googleClientId, establishSession, navigate])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const trimmedEmail = email.trim()
    if (!trimmedEmail || !password) {
      toast.error('Please enter your email and password.')
      return
    }

    if (mode === 'register') {
      if (password.length < 5) {
        toast.error('Password must be at least 5 characters long.')
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

  const handleManualGoogleClick = () => {
    if (!googleClientId) {
      toast.error('VITE_GOOGLE_CLIENT_ID is not configured in .env. Please set it to enable Google Sign-In.')
      return
    }

    if (window.google?.accounts?.id) {
      window.google.accounts.id.prompt()
    } else {
      toast.error('Google Sign-In SDK is still loading. Please wait a second.')
    }
  }

  const fillAdminCredentials = () => {
    switchMode('login')
    setEmail('admin@admin.pl')
    setPassword('admin')
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
              placeholder="At least 5 characters"
              minLength={mode === 'register' ? 5 : undefined}
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
                minLength={5}
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

        <div className="my-5 flex items-center gap-3">
          <div className="h-px flex-1 bg-slate-400/15" />
          <span className="text-xs text-[#738099] uppercase">or</span>
          <div className="h-px flex-1 bg-slate-400/15" />
        </div>

        {/* Google Identity Services official rendered button */}
        <div
          ref={googleButtonContainerRef}
          className={`w-full flex justify-center ${gsiLoaded ? '' : 'hidden'}`}
        />

        {/* Fallback button if GSI is still loading or client ID not set */}
        {!gsiLoaded && (
          <button
            type="button"
            disabled={isSubmitting}
            onClick={handleManualGoogleClick}
            className="inline-flex min-h-12 w-full cursor-pointer items-center justify-center gap-3 rounded-[14px] border border-slate-400/20 bg-slate-400/5 px-5 text-sm font-medium text-[#dce2ee] transition hover:border-emerald-300/35 hover:bg-slate-400/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
          >
            <svg className="size-4" viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="#EA4335"
                d="M12 10.2v3.9h5.5c-.2 1.3-1.5 3.8-5.5 3.8-3.3 0-6-2.7-6-6s2.7-6 6-6c1.9 0 3.1.8 3.8 1.5l2.6-2.5C16.8 3.4 14.6 2.5 12 2.5 6.8 2.5 2.5 6.8 2.5 12s4.3 9.5 9.5 9.5c5.5 0 9.1-3.8 9.1-9.2 0-.6-.1-1.1-.2-1.6H12Z"
              />
            </svg>
            Continue with Google
          </button>
        )}

        <div className="mt-5 flex items-center justify-between rounded-xl border border-slate-400/10 bg-[#070b12]/60 px-3.5 py-2.5 text-xs text-[#738099]">
          <span>
            Default admin: <strong className="text-[#c7d0e2]">admin@admin.pl</strong> /{' '}
            <strong className="text-[#c7d0e2]">admin</strong>
          </span>
          <button
            type="button"
            onClick={fillAdminCredentials}
            className="cursor-pointer font-medium text-emerald-300 hover:underline"
          >
            Fill
          </button>
        </div>
      </form>
    </div>
  )
}
