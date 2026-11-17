import type {
  AuthResponse,
  ChangePasswordRequest,
  LoginRequest,
  MessageResponse,
  RegisterRequest,
  TokenResponse,
} from '../types/auth'
import { apiBaseUrl, authenticatedFetch, parseApiError } from './client'

export async function login(payload: LoginRequest): Promise<AuthResponse> {
  const response = await fetch(`${apiBaseUrl}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Invalid email or password.'))
  }

  return response.json() as Promise<AuthResponse>
}

export async function register(payload: RegisterRequest): Promise<AuthResponse> {
  const response = await fetch(`${apiBaseUrl}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Could not create account.'))
  }

  return response.json() as Promise<AuthResponse>
}

export async function refreshTokens(refreshToken: string): Promise<TokenResponse> {
  const response = await fetch(`${apiBaseUrl}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refreshToken }),
  })

  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Session expired. Please log in again.'))
  }

  return response.json() as Promise<TokenResponse>
}

export async function logout(refreshToken: string): Promise<MessageResponse> {
  const response = await fetch(`${apiBaseUrl}/api/v1/auth/logout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refreshToken }),
  })

  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Could not log out cleanly.'))
  }

  return response.json() as Promise<MessageResponse>
}

export async function changePassword(payload: ChangePasswordRequest): Promise<MessageResponse> {
  const response = await authenticatedFetch('/api/v1/auth/change-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Could not change password.'))
  }

  return response.json() as Promise<MessageResponse>
}
