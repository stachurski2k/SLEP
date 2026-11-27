import { type ReactNode, useCallback, useEffect, useState } from 'react'
import { logout as apiLogout } from '../api/auth'
import type { AuthResponse } from '../types/auth'
import { clearStoredSession, getStoredSession, setStoredSession } from './storage'
import { AuthContext } from './useAuth'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthResponse | null>(() => getStoredSession())

  const establishSession = useCallback((nextSession: AuthResponse) => {
    setStoredSession(nextSession)
    setSession(nextSession)
  }, [])

  const logOut = useCallback(async () => {
    const refreshToken = session?.tokens.refreshToken ?? getStoredSession()?.tokens.refreshToken
    clearStoredSession()
    setSession(null)
    if (refreshToken) {
      await apiLogout(refreshToken).catch(() => undefined)
    }
  }, [session])

  useEffect(() => {
    const handleAuthExpired = () => {
      clearStoredSession()
      setSession(null)
    }

    window.addEventListener('slep:auth-expired', handleAuthExpired)
    return () => window.removeEventListener('slep:auth-expired', handleAuthExpired)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        session,
        isAuthenticated: session !== null,
        establishSession,
        logOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
