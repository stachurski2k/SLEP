import { clearStoredSession, getStoredSession, updateStoredTokens } from '../auth/storage'
import type { TokenResponse } from '../types/auth'

export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''
export const modelServiceUrl = import.meta.env.VITE_MODEL_SERVICE_URL ?? '/model-service'

type FastApiErrorBody = {
  detail?: string | Array<{ msg?: string }>
}

export async function parseApiError(response: Response, fallbackMessage: string): Promise<string> {
  const body = (await response.json().catch(() => null)) as FastApiErrorBody | null
  if (!body?.detail) return fallbackMessage
  if (typeof body.detail === 'string') return body.detail
  if (Array.isArray(body.detail) && body.detail.length > 0) {
    return body.detail.map((item) => item.msg ?? fallbackMessage).join(', ')
  }
  return fallbackMessage
}

let refreshPromise: Promise<TokenResponse | null> | null = null

async function performTokenRefresh(refreshToken: string): Promise<TokenResponse | null> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken }),
    })

    if (!response.ok) {
      clearStoredSession()
      window.dispatchEvent(new Event('slep:auth-expired'))
      return null
    }

    const tokens = (await response.json()) as TokenResponse
    updateStoredTokens(tokens)
    return tokens
  } catch {
    return null
  }
}

export async function authenticatedFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const session = getStoredSession()
  const headers = new Headers(init.headers)

  if (session?.tokens.accessToken) {
    headers.set('Authorization', `Bearer ${session.tokens.accessToken}`)
  }

  const url = path.startsWith('http') ? path : `${apiBaseUrl}${path}`
  const response = await fetch(url, { ...init, headers })

  if (response.status !== 401 || !session?.tokens.refreshToken) {
    return response
  }

  if (!refreshPromise) {
    refreshPromise = performTokenRefresh(session.tokens.refreshToken).finally(() => {
      refreshPromise = null
    })
  }

  const newTokens = await refreshPromise
  if (!newTokens) {
    return response
  }

  const retryHeaders = new Headers(init.headers)
  retryHeaders.set('Authorization', `Bearer ${newTokens.accessToken}`)
  return fetch(url, { ...init, headers: retryHeaders })
}
