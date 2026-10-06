from datetime import datetime, timezone
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from main import app
from modules.auth.application.commands import (
    ChangePasswordCommand,
    LoginCommand,
    LoginWithGoogleCommand,
    LogoutCommand,
    RefreshTokenCommand,
    RegisterCommand,
)
from modules.auth.application.services import AuthApplicationServiceImpl
from modules.auth.domain.entities import ExternalIdentity, RefreshToken, UserCredentials
from modules.auth.domain.exceptions import (
    InvalidCredentialsError,
    PasswordMismatchError,
    UserAlreadyExistsError,
)
from modules.auth.domain.repositories import (
    ExternalIdentityRepository,
    RefreshTokenRepository,
    UserCredentialsRepository,
)
from modules.auth.domain.value_objects import AuthProvider
from modules.auth.infrastructure.security import (
    BcryptPasswordHasher,
    GoogleOAuthProvider,
    JwtTokenService,
)
from modules.auth.presentation.dependencies import get_auth_service, get_token_service


# --- IN-MEMORY REPOSITORIES FOR TESTING ---

class InMemoryUserCredentialsRepository(UserCredentialsRepository):
    def __init__(self) -> None:
        self.users: dict[UUID, UserCredentials] = {}

    async def get_by_id(self, user_id: UUID) -> UserCredentials | None:
        return self.users.get(user_id)

    async def get_by_email(self, email: str) -> UserCredentials | None:
        norm = email.strip().lower()
        for u in self.users.values():
            if u.email.strip().lower() == norm:
                return u
        return None

    async def save(self, credentials: UserCredentials) -> None:
        self.users[credentials.id] = credentials

    async def delete(self, user_id: UUID) -> None:
        self.users.pop(user_id, None)


class InMemoryRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self) -> None:
        self.tokens: dict[str, RefreshToken] = {}

    async def get_by_token(self, token: str) -> RefreshToken | None:
        return self.tokens.get(token)

    async def save(self, refresh_token: RefreshToken) -> None:
        self.tokens[refresh_token.token] = refresh_token

    async def revoke_by_token(self, token: str) -> None:
        if token in self.tokens:
            self.tokens[token].isRevoked = True

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        for t in self.tokens.values():
            if t.userId == user_id:
                t.isRevoked = True


class InMemoryExternalIdentityRepository(ExternalIdentityRepository):
    def __init__(self) -> None:
        self.identities: list[ExternalIdentity] = []

    async def get_by_provider_and_user_id(
        self, provider: str, provider_user_id: str
    ) -> ExternalIdentity | None:
        for i in self.identities:
            p_val = i.provider.value if hasattr(i.provider, "value") else str(i.provider)
            if p_val == provider and i.providerUserId == provider_user_id:
                return i
        return None

    async def get_by_system_user_id(self, user_id: UUID) -> list[ExternalIdentity]:
        return [i for i in self.identities if i.userId == user_id]

    async def save(self, identity: ExternalIdentity) -> None:
        self.identities.append(identity)


# --- UNIT TESTS: SECURITY COMPONENTS ---

def test_bcrypt_password_hasher():
    hasher = BcryptPasswordHasher()
    password = "SuperSecretPassword123!"

    hashed = hasher.hash(password)
    assert hashed != password
    assert hasher.verify(password, hashed) is True
    assert hasher.verify("WrongPassword123!", hashed) is False
    assert hasher.verify(password, "") is False


def test_jwt_token_service():
    service = JwtTokenService(
        secret_key="test-key-for-jwt-signing-minimum-32-chars-long!",
        access_token_expire_minutes=5,
    )
    user_id = uuid4()
    email = "test@example.com"

    access_token = service.create_access_token(user_id=user_id, email=email)
    assert isinstance(access_token, str)

    payload = service.decode_token(access_token)
    assert payload["sub"] == str(user_id)
    assert payload["email"] == email
    assert payload["type"] == "access"

    refresh_entity = service.create_refresh_token(user_id=user_id)
    assert refresh_entity.userId == user_id
    assert len(refresh_entity.token) > 30
    assert refresh_entity.is_valid() is True


@pytest.mark.asyncio
async def test_google_oauth_provider_mock():
    provider = GoogleOAuthProvider()
    result = await provider.verify_id_token("mock_testuser")
    assert result["email"] == "testuser@gmail.com"
    assert result["provider_user_id"] == "google_testuser"


# --- APPLICATION SERVICE TESTS ---

@pytest.mark.asyncio
async def test_auth_service_register_and_login_flow():
    cred_repo = InMemoryUserCredentialsRepository()
    token_repo = InMemoryRefreshTokenRepository()
    ext_repo = InMemoryExternalIdentityRepository()
    hasher = BcryptPasswordHasher()
    token_service = JwtTokenService(secret_key="secret-key-minimum-32-chars-long-for-jwt-signing!")
    oauth = GoogleOAuthProvider()

    service = AuthApplicationServiceImpl(
        credentials_repository=cred_repo,
        refresh_token_repository=token_repo,
        external_identity_repository=ext_repo,
        password_hasher=hasher,
        token_service=token_service,
        oauth_provider=oauth,
    )

    # 1. Registration
    reg_cmd = RegisterCommand(
        email="learner@slep.pl",
        password="ValidPassword123!",
        passwordConfirmation="ValidPassword123!",
    )
    auth_resp = await service.register(reg_cmd)
    assert auth_resp.email == "learner@slep.pl"
    assert auth_resp.tokens.accessToken is not None
    assert auth_resp.tokens.refreshToken is not None

    # Duplicate registration should raise error
    with pytest.raises(UserAlreadyExistsError):
        await service.register(reg_cmd)

    # Password mismatch should raise error
    with pytest.raises(PasswordMismatchError):
        await service.register(
            RegisterCommand(
                email="another@slep.pl",
                password="ValidPassword123!",
                passwordConfirmation="DifferentPassword123!",
            )
        )

    # 2. Login
    login_cmd = LoginCommand(email="learner@slep.pl", password="ValidPassword123!")
    login_resp = await service.login(login_cmd)
    assert login_resp.userId == auth_resp.userId
    assert login_resp.tokens.accessToken is not None

    # Invalid login
    with pytest.raises(InvalidCredentialsError):
        await service.login(LoginCommand(email="learner@slep.pl", password="WrongPassword!"))

    # 3. Refresh token rotation
    rf_cmd = RefreshTokenCommand(refreshToken=login_resp.tokens.refreshToken)
    new_tokens = await service.refreshToken(rf_cmd)
    assert new_tokens.accessToken is not None
    assert new_tokens.refreshToken != login_resp.tokens.refreshToken

    # Old refresh token should now be revoked
    with pytest.raises(Exception):
        await service.refreshToken(rf_cmd)

    # 4. Change password
    cp_cmd = ChangePasswordCommand(
        userId=auth_resp.userId,
        currentPassword="ValidPassword123!",
        newPassword="BrandNewPassword999!",
        newPasswordConfirmation="BrandNewPassword999!",
    )
    await service.changePassword(cp_cmd)

    # Old password no longer works
    with pytest.raises(InvalidCredentialsError):
        await service.login(LoginCommand(email="learner@slep.pl", password="ValidPassword123!"))

    # New password works
    new_login = await service.login(LoginCommand(email="learner@slep.pl", password="BrandNewPassword999!"))
    assert new_login.userId == auth_resp.userId


@pytest.mark.asyncio
async def test_auth_service_google_login():
    cred_repo = InMemoryUserCredentialsRepository()
    token_repo = InMemoryRefreshTokenRepository()
    ext_repo = InMemoryExternalIdentityRepository()
    hasher = BcryptPasswordHasher()
    token_service = JwtTokenService(secret_key="secret-key-minimum-32-chars-long-for-jwt-signing!")
    oauth = GoogleOAuthProvider()

    service = AuthApplicationServiceImpl(
        credentials_repository=cred_repo,
        refresh_token_repository=token_repo,
        external_identity_repository=ext_repo,
        password_hasher=hasher,
        token_service=token_service,
        oauth_provider=oauth,
    )

    google_cmd = LoginWithGoogleCommand(idToken="mock_googleuser123")
    resp = await service.loginWithGoogle(google_cmd)
    assert resp.email == "googleuser123@gmail.com"
    assert resp.tokens.accessToken is not None

    # Check external identity saved
    saved_identity = await ext_repo.get_by_provider_and_user_id(
        provider=AuthProvider.GOOGLE.value,
        provider_user_id="google_googleuser123",
    )
    assert saved_identity is not None
    assert saved_identity.userId == resp.userId


# --- INTEGRATION TESTS: FASTAPI HTTP ENDPOINTS ---

def test_api_auth_endpoints():
    cred_repo = InMemoryUserCredentialsRepository()
    token_repo = InMemoryRefreshTokenRepository()
    ext_repo = InMemoryExternalIdentityRepository()
    hasher = BcryptPasswordHasher()
    token_service = JwtTokenService(secret_key="test-api-secret-key-minimum-32-chars-long-for-jwt!")
    oauth = GoogleOAuthProvider()

    test_service = AuthApplicationServiceImpl(
        credentials_repository=cred_repo,
        refresh_token_repository=token_repo,
        external_identity_repository=ext_repo,
        password_hasher=hasher,
        token_service=token_service,
        oauth_provider=oauth,
    )

    app.dependency_overrides[get_auth_service] = lambda: test_service
    app.dependency_overrides[get_token_service] = lambda: token_service

    client = TestClient(app)

    try:
        # 1. Register endpoint
        reg_payload = {
            "email": "api_user@slep.pl",
            "password": "Password123!",
            "passwordConfirmation": "Password123!",
        }
        res = client.post("/api/v1/auth/register", json=reg_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "api_user@slep.pl"
        assert "accessToken" in data["tokens"]
        access_token = data["tokens"]["accessToken"]
        refresh_token = data["tokens"]["refreshToken"]

        # 2. Login endpoint
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "api_user@slep.pl", "password": "Password123!"},
        )
        assert login_res.status_code == 200

        # 3. Google OAuth endpoint
        google_res = client.post(
            "/api/v1/auth/google",
            json={"idToken": "mock_google_api_user"},
        )
        assert google_res.status_code == 200
        assert "accessToken" in google_res.json()["tokens"]

        # 4. Refresh endpoint
        refresh_res = client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": refresh_token},
        )
        assert refresh_res.status_code == 200
        assert "accessToken" in refresh_res.json()

        # 5. Change password endpoint (authenticated via Bearer)
        headers = {"Authorization": f"Bearer {access_token}"}
        cp_res = client.post(
            "/api/v1/auth/change-password",
            headers=headers,
            json={
                "currentPassword": "Password123!",
                "newPassword": "NewPassword456!",
                "newPasswordConfirmation": "NewPassword456!",
            },
        )
        assert cp_res.status_code == 200
        assert "pomyślnie" in cp_res.json()["message"]

        # 6. Logout endpoint
        logout_res = client.post(
            "/api/v1/auth/logout",
            json={"refreshToken": refresh_token},
        )
        assert logout_res.status_code == 200

    finally:
        app.dependency_overrides.clear()
