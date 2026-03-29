"""Test Django configuration loads correctly."""
from django.conf import settings


class TestConfig:
    def test_secret_key_is_set(self):
        assert settings.SECRET_KEY == "test-secret-key"

    def test_debug_is_false_in_testing(self):
        assert settings.DEBUG is False

    def test_database_is_test_db(self):
        assert settings.DATABASES["default"]["NAME"] == "mpp_django_test"

    def test_allauth_signup_disabled(self):
        assert settings.ACCOUNT_SIGNUP_ENABLED is False

    def test_password_hasher_is_fast(self):
        assert "MD5PasswordHasher" in settings.PASSWORD_HASHERS[0]
