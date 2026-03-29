"""Test factories for all models."""
import factory
from apps.accounts.models import User
from core.domain.enums import UserRole


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user-{n}")
    password = factory.PostGenerationMethodCall("set_password", "test123")
    role = UserRole.REQUESTER
