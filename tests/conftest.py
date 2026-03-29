"""Shared test fixtures."""
import pytest


@pytest.fixture(scope="session")
def django_db_setup(django_test_environment, django_db_blocker):
    """Use the existing mpp_test database directly (no CREATE/DROP needed)."""
    from django.conf import settings
    from django.test.utils import setup_databases, teardown_databases

    with django_db_blocker.unblock():
        db_cfg = setup_databases(
            verbosity=0,
            interactive=False,
            keepdb=True,
        )
    yield
    # Do not tear down — we reuse the database between test runs.
