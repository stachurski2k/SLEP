import { createContext, useContext } from 'react'
import type { AuthResponse } from '../types/auth'

export type AuthContextValue = {
  session: AuthResponse | null
  isAuthenticated: boolean
  establishSession: (session: AuthResponse) => void
  logOut: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider.')
  }
  return context
}
