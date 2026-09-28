from ..domain.entities import ExternalIdentity, RefreshToken, UserCredentials
from ..domain.value_objects import AuthProvider
from .models import ExternalIdentityModel, RefreshTokenModel, UserCredentialsModel


class AuthMapper:
    """
    Data Mapper converting between Domain Entities in Auth bounded context
    and SQLAlchemy Persistence Models.
    """

    # --- UserCredentials ---

    @staticmethod
    def to_credentials_domain(model: UserCredentialsModel) -> UserCredentials:
        return UserCredentials(
            id=model.id,
            email=model.email,
            passwordHash=model.password_hash,
            createdAt=model.created_at,
        )

    @staticmethod
    def to_credentials_persistence(
        entity: UserCredentials, existing: UserCredentialsModel | None = None
    ) -> UserCredentialsModel:
        if existing is None:
            return UserCredentialsModel(
                id=entity.id,
                email=entity.email,
                password_hash=entity.passwordHash,
                created_at=entity.createdAt,
            )
        existing.email = entity.email
        existing.password_hash = entity.passwordHash
        return existing

    # --- RefreshToken ---

    @staticmethod
    def to_refresh_token_domain(model: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            id=model.id,
            userId=model.user_id,
            token=model.token,
            expiresAt=model.expires_at,
            isRevoked=model.is_revoked,
        )

    @staticmethod
    def to_refresh_token_persistence(
        entity: RefreshToken, existing: RefreshTokenModel | None = None
    ) -> RefreshTokenModel:
        if existing is None:
            return RefreshTokenModel(
                id=entity.id,
                user_id=entity.userId,
                token=entity.token,
                expires_at=entity.expiresAt,
                is_revoked=entity.isRevoked,
            )
        existing.expires_at = entity.expiresAt
        existing.is_revoked = entity.isRevoked
        return existing

    # --- ExternalIdentity ---

    @staticmethod
    def to_external_identity_domain(model: ExternalIdentityModel) -> ExternalIdentity:
        provider_vo = (
            AuthProvider(model.provider)
            if model.provider in AuthProvider._value2member_map_
            else AuthProvider.GOOGLE
        )
        return ExternalIdentity(
            id=model.id,
            provider=provider_vo,
            providerUserId=model.provider_user_id,
            userId=model.user_id,
        )

    @staticmethod
    def to_external_identity_persistence(
        entity: ExternalIdentity, existing: ExternalIdentityModel | None = None
    ) -> ExternalIdentityModel:
        provider_str = (
            entity.provider.value
            if hasattr(entity.provider, "value")
            else str(entity.provider)
        )
        if existing is None:
            return ExternalIdentityModel(
                id=entity.id,
                user_id=entity.userId,
                provider=provider_str,
                provider_user_id=entity.providerUserId,
            )
        existing.user_id = entity.userId
        existing.provider = provider_str
        existing.provider_user_id = entity.providerUserId
        return existing
