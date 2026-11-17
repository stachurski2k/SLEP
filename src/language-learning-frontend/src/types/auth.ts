export type UserRole = 'user' | 'admin'

export type TokenResponse = {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
}

export type AuthResponse = {
  userId: string
  email: string
  role: UserRole
  tokens: TokenResponse
}

export type LoginRequest = {
  email: string
  password: string
}

export type RegisterRequest = {
  email: string
  password: string
  passwordConfirmation: string
}

export type GoogleLoginRequest = {
  idToken: string
}

export type ChangePasswordRequest = {
  currentPassword: string
  newPassword: string
  newPasswordConfirmation: string
}

export type MessageResponse = {
  message: string
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string
            callback: (response: { credential?: string }) => void
            auto_select?: boolean
            cancel_on_tap_outside?: boolean
          }) => void
          renderButton: (
            parent: HTMLElement,
            options: Record<string, string | number | boolean>,
          ) => void
          prompt: (notification?: (notification: unknown) => void) => void
        }
      }
    }
  }
}
