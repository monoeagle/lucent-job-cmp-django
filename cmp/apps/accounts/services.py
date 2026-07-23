"""Account business logic."""
from apps.accounts.models import User
from core.domain.enums import UserRole

ROLE_HIERARCHY = [
    UserRole.REQUESTER,
    UserRole.APPROVER,
    UserRole.ADMIN,
    UserRole.SUPERADMIN,
]

STUB_USERS = [
    {"username": "test-requester", "role": UserRole.REQUESTER},
    {"username": "test-approver", "role": UserRole.APPROVER},
    {"username": "test-admin", "role": UserRole.ADMIN},
    {"username": "test-multi", "role": UserRole.APPROVER},
    {"username": "test-superadmin", "role": UserRole.SUPERADMIN},
]


class AccountService:
    @staticmethod
    def seed_stub_users() -> int:
        """Create stub users for development. Returns count of newly created users."""
        created_count = 0
        for user_data in STUB_USERS:
            _, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "role": user_data["role"],
                    "is_staff": user_data["role"] in (UserRole.ADMIN, UserRole.SUPERADMIN),
                    "is_superuser": user_data["role"] == UserRole.SUPERADMIN,
                },
            )
            if created:
                user = User.objects.get(username=user_data["username"])
                user.set_password("test123")
                user.save()
                created_count += 1
        return created_count

    @staticmethod
    def is_at_least_role(user_role: str, minimum_role: str) -> bool:
        """Check if user_role is at or above minimum_role in the hierarchy."""
        try:
            user_level = ROLE_HIERARCHY.index(user_role)
            min_level = ROLE_HIERARCHY.index(minimum_role)
            return user_level >= min_level
        except ValueError:
            return False

    @staticmethod
    def list_users_with_min_role(minimum_role):
        """Return active users whose role is at or above minimum_role."""
        try:
            min_level = ROLE_HIERARCHY.index(minimum_role)
        except ValueError:
            return []
        eligible = ROLE_HIERARCHY[min_level:]
        return list(User.objects.filter(role__in=eligible, is_active=True))
