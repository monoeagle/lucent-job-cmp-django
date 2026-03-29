from .base import *  # noqa: F401,F403
DEBUG = False
SECRET_KEY = "test-secret-key"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "mpp_django_test",
        "USER": "mpp",
        "PASSWORD": "mpp",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {
            "NAME": "mpp_django_test",
        },
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Celery: run tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
