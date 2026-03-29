"""Unified seed command for demo data."""
from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.accounts.services import AccountService
from apps.approvals.models import ApprovalRule
from apps.catalog.models import ServiceTemplate
from apps.catalog.services import CatalogService
from apps.cmdb.models import UserTenantAssignment


class Command(BaseCommand):
    help = "Seed all demo data"

    def handle(self, *args, **options):
        users = AccountService.seed_stub_users()
        templates = CatalogService.seed_templates()
        rules = self._seed_approval_rules()
        tenants = self._seed_tenant_assignments()
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {users} user(s), {templates} template(s), "
            f"{rules} approval rule(s), {tenants} tenant assignment(s)."
        ))

    def _seed_approval_rules(self):
        created = 0
        for template in ServiceTemplate.objects.all():
            _, was_created = ApprovalRule.objects.get_or_create(
                template=template, approver_role="approver",
                defaults={"condition": {}, "is_active": True})
            if was_created:
                created += 1
        return created

    def _seed_tenant_assignments(self):
        created = 0
        for username in [
            "test-requester", "test-approver", "test-admin",
            "test-multi", "test-superadmin",
        ]:
            try:
                user = User.objects.get(username=username)
                _, was_created = UserTenantAssignment.objects.get_or_create(
                    user=user, tenant="tenant-alpha")
                if was_created:
                    created += 1
            except User.DoesNotExist:
                pass
        return created
