import pytest

from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
from tests.factories import UserFactory


@pytest.mark.django_db
class TestNotificationService:
    def test_create(self):
        user = UserFactory()
        n = NotificationService.create(user=user, title="Test", message="Hello")
        assert n.pk is not None and n.is_read is False

    def test_list_unread(self):
        user = UserFactory()
        NotificationService.create(user=user, title="Unread", message="msg")
        NotificationService.create(user=user, title="Read", message="msg")
        Notification.objects.filter(title="Read").update(is_read=True)
        assert len(NotificationService.list_unread(user.pk)) == 1

    def test_mark_read(self):
        user = UserFactory()
        n = NotificationService.create(user=user, title="Test", message="msg")
        NotificationService.mark_read(n.pk)
        n.refresh_from_db()
        assert n.is_read is True

    def test_mark_all_read(self):
        user = UserFactory()
        NotificationService.create(user=user, title="A", message="m")
        NotificationService.create(user=user, title="B", message="m")
        NotificationService.mark_all_read(user.pk)
        assert Notification.objects.filter(user=user, is_read=False).count() == 0

    def test_unread_count(self):
        user = UserFactory()
        NotificationService.create(user=user, title="A", message="m")
        NotificationService.create(user=user, title="B", message="m")
        assert NotificationService.unread_count(user.pk) == 2

    def test_list_all(self):
        user = UserFactory()
        NotificationService.create(user=user, title="A", message="m")
        assert len(NotificationService.list_all(user.pk)) == 1
