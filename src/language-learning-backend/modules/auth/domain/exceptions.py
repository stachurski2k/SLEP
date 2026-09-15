class AuthDomainError(Exception):
    """Base exception for authentication domain errors."""
    pass


class InvalidCredentialsError(AuthDomainError):
    """Raised when provided credentials (email or password) are incorrect."""
    pass


class UserAlreadyExistsError(AuthDomainError):
    """Raised when attempting to register an account with an email that is already in use."""
    pass


class UserNotFoundError(AuthDomainError):
    """Raised when the requested user is not found."""
    pass


class InvalidTokenError(AuthDomainError):
    """Raised when a token is invalid or malformed."""
    pass


class TokenExpiredError(AuthDomainError):
    """Raised when a token has expired."""
    pass


class TokenRevokedError(AuthDomainError):
    """Raised when a token has been revoked."""
    pass


class InvalidPasswordError(AuthDomainError):
    """Raised when a password does not meet security requirements."""
    pass


class PasswordMismatchError(AuthDomainError):
    """Raised when password and password confirmation do not match."""
    pass


class InvalidEmailError(AuthDomainError):
    """Raised when an email address has an invalid format."""
    pass


class ExternalAuthError(AuthDomainError):
    """Raised when external authentication (e.g. Google OAuth2) fails."""
    pass