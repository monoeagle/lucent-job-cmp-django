import pytest

from apps.audit.models import AuditLog
from apps.audit.services import AuditService
from tests.factories import UserFactory


@pytest.mark.django_db
class TestAuditService:
    def test_log_action(self):
        user = UserFactory()
        AuditService.log(
            user=user, action="order_created", resource_type="order", resource_id=1
        )
        assert AuditLog.objects.count() == 1

    def test_log_with_details(self):
        user = UserFactory()
        AuditService.log(
            user=user,
            action="order_submitted",
            resource_type="order",
            resource_id=1,
            details={"items": 3},
        )
        assert AuditLog.objects.first().details == {"items": 3}

    def test_log_without_user(self):
        AuditService.log(
            user=None, action="system_startup", resource_type="system", resource_id=0
        )
        assert AuditLog.objects.count() == 1

    def test_list_logs(self):
        user = UserFactory()
        AuditService.log(user=user, action="a1", resource_type="order", resource_id=1)
        AuditService.log(user=user, action="a2", resource_type="order", resource_id=2)
        assert len(AuditService.list_logs()) == 2

    def test_list_logs_by_resource_type(self):
        user = UserFactory()
        AuditService.log(user=user, action="a1", resource_type="order", resource_id=1)
        AuditService.log(
            user=user, action="a2", resource_type="template", resource_id=1
        )
        assert len(AuditService.list_logs(resource_type="order")) == 1

    def test_anonymize_user(self):
        user = UserFactory()
        AuditService.log(user=user, action="a1", resource_type="order", resource_id=1)
        AuditService.anonymize_user(user.pk)
        assert AuditLog.objects.first().user is None
