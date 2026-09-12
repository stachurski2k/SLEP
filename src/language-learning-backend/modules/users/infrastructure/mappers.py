from .domain.entities import Preferences, User, UserProfile
from .domain.value_objects import Theme, UserRole
from .models import UserModel, UserPreferencesModel, UserProfileModel


class UserMapper:
    """
    Data Mapper converting between Domain Entities (User aggregate)
    and SQLAlchemy Persistence Models (UserModel, UserProfileModel, UserPreferencesModel).
    """

    @staticmethod
    def to_domain(model: UserModel) -> User:
        """
        Maps a SQLAlchemy UserModel into a pure domain User aggregate root.
        """
        profile = UserProfile(
            displayName=model.profile.display_name if model.profile else model.username,
            country=model.profile.country if model.profile else None,
        )

        preferences = Preferences(
            notificationsEnabled=(
                model.preferences.notifications_enabled if model.preferences else False
            ),
            theme=Theme(model.preferences.theme) if model.preferences else Theme.LIGHT,
            dailyGoal=model.preferences.daily_goal if model.preferences else 50,
        )

        return User(
            id=model.id,
            email=model.email,
            username=model.username,
            role=UserRole(model.role),
            createdAt=model.created_at,
            profile=profile,
            preferences=preferences,
        )

    @staticmethod
    def to_persistence(entity: User, existing_model: UserModel | None = None) -> UserModel:
        """
        Maps a domain User aggregate root to SQLAlchemy models.
        If existing_model is provided, updates its attributes in-place.
        Otherwise, creates and returns a new UserModel with child models.
        """
        role_str = entity.role.value if hasattr(entity.role, "value") else str(entity.role)
        theme_str = (
            entity.preferences.theme.value
            if hasattr(entity.preferences.theme, "value")
            else str(entity.preferences.theme)
        )

        if existing_model is None:
            return UserModel(
                id=entity.id,
                email=entity.email,
                username=entity.username,
                role=role_str,
                created_at=entity.createdAt,
                profile=UserProfileModel(
                    display_name=entity.profile.displayName,
                    country=entity.profile.country,
                ),
                preferences=UserPreferencesModel(
                    notifications_enabled=entity.preferences.notificationsEnabled,
                    theme=theme_str,
                    daily_goal=entity.preferences.dailyGoal,
                ),
            )

        # entry update
        
        existing_model.email = entity.email
        existing_model.username = entity.username
        existing_model.role = role_str

        if existing_model.profile is not None:
            existing_model.profile.display_name = entity.profile.displayName
            existing_model.profile.country = entity.profile.country
        else:
            existing_model.profile = UserProfileModel(
                user_id=existing_model.id,
                display_name=entity.profile.displayName,
                country=entity.profile.country,
            )

        if existing_model.preferences is not None:
            existing_model.preferences.notifications_enabled = (
                entity.preferences.notificationsEnabled
            )
            existing_model.preferences.theme = theme_str
            existing_model.preferences.daily_goal = entity.preferences.dailyGoal
        else:
            existing_model.preferences = UserPreferencesModel(
                user_id=existing_model.id,
                notifications_enabled=entity.preferences.notificationsEnabled,
                theme=theme_str,
                daily_goal=entity.preferences.dailyGoal,
            )

        return existing_model
