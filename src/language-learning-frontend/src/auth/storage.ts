import type { AuthResponse, TokenResponse } from '../types/auth'

const AUTH_STORAGE_KEY = 'slep-learning-auth'
const LEGACY_AUTH_KEY = 'slep-learning-authenticated'

export function getStoredSession(): AuthResponse | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as AuthResponse
    if (
      !parsed?.userId ||
      !parsed?.email ||
      !parsed?.tokens?.accessToken ||
      !parsed?.tokens?.refreshToken
    ) {
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function setStoredSession(session: AuthResponse): void {
  localStorage.removeItem(LEGACY_AUTH_KEY)
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
}

export function updateStoredTokens(tokens: TokenResponse): AuthResponse | null {
  const current = getStoredSession()
  if (!current) return null
  const updated: AuthResponse = {
    ...current,
    tokens,
  }
  setStoredSession(updated)
  return updated
}

export function clearStoredSession(): void {
  localStorage.removeItem(LEGACY_AUTH_KEY)
  localStorage.removeItem(AUTH_STORAGE_KEY)
}
