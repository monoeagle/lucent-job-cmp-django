"""Management command to seed all demo data."""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services import AccountService
from apps.approvals.models import ApprovalRule, ApprovalRequest
from apps.audit.services import AuditService
from apps.catalog.models import ServiceTemplate
from apps.catalog.services import CatalogService
from apps.cmdb.models import UserTenantAssignment
from apps.notifications.models import Notification
from apps.orders.models import Order, OrderItem
from apps.subscriptions.models import Subscription
from core.domain.value_objects import OrderStatus


class Command(BaseCommand):
    help = "Seed all demo data (users, templates, orders, approvals, notifications)"

    def handle(self, *args, **options):
        users_created = AccountService.seed_stub_users()
        templates_created = CatalogService.seed_templates()

        # Only seed demo data if templates were just created (first run)
        if templates_created > 0:
            self._seed_approval_rules()
            self._seed_tenant_assignments()
            self._seed_demo_orders()
            self._seed_audit_logs()
            self.stdout.write(self.style.SUCCESS(
                f"Seeded {users_created} user(s), {templates_created} template(s), "
                f"demo orders, approvals, and notifications."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Seeded {users_created} user(s), {templates_created} template(s). "
                f"Demo data already exists."
            ))

    def _seed_approval_rules(self):
        for template in ServiceTemplate.objects.all():
            ApprovalRule.objects.get_or_create(
                template=template, approver_role="approver",
                defaults={"condition": {}, "is_active": True},
            )

    def _seed_tenant_assignments(self):
        for username in [
            "test-requester", "test-approver", "test-admin",
            "test-multi", "test-superadmin",
        ]:
            try:
                user = User.objects.get(username=username)
                UserTenantAssignment.objects.get_or_create(
                    user=user, tenant="tenant-alpha",
                )
            except User.DoesNotExist:
                pass

    def _seed_demo_orders(self):
        requester = User.objects.get(username="test-requester")
        approver = User.objects.get(username="test-approver")
        admin = User.objects.get(username="test-admin")

        linux = ServiceTemplate.objects.get(name="Linux VM")
        windows = ServiceTemplate.objects.get(name="Windows VM")
        postgres = ServiceTemplate.objects.get(name="PostgreSQL DB")

        # ORD-1: Draft — Web-Cluster
        o1 = Order.objects.create(
            user=requester, status=OrderStatus.DRAFT,
            notes="Neues Kundenprojekt Q3",
        )
        OrderItem.objects.create(
            order=o1, template=linux,
            parameters={
                "cpu": 2, "ram_gb": 4, "disk_gb": 50,
                "os_version": "ubuntu-24.04", "hostname": "web-q3-01",
                "ha": False, "backup": "daily", "extra_disk_gb": 0,
            },
        )

        # ORD-2: Draft — Windows App-Server
        o2 = Order.objects.create(
            user=requester, status=OrderStatus.DRAFT,
            notes="App-Server für Buchhaltung",
        )
        OrderItem.objects.create(
            order=o2, template=windows,
            parameters={
                "cpu": 8, "ram_gb": 16, "disk_gb": 100,
                "os_version": "win-server-2022", "hostname": "app-buch-01",
                "domain_join": True, "backup": "daily", "extra_disk_gb": 0,
            },
        )

        # ORD-3: Pending Approval — Produktions-Webserver (2 Items)
        o3 = Order.objects.create(
            user=requester, status=OrderStatus.PENDING_APPROVAL,
            notes="Erweiterung Webfarm für Black Friday",
        )
        OrderItem.objects.create(
            order=o3, template=linux,
            parameters={
                "cpu": 8, "ram_gb": 16, "disk_gb": 100,
                "os_version": "ubuntu-24.04", "hostname": "nginx-prod-01",
                "ha": True, "backup": "daily", "extra_disk_gb": 0,
            },
        )
        OrderItem.objects.create(
            order=o3, template=linux,
            parameters={
                "cpu": 16, "ram_gb": 32, "disk_gb": 200,
                "os_version": "rhel-9", "hostname": "db-prod-01",
                "ha": True, "backup": "daily", "extra_disk_gb": 500,
            },
        )
        rule3 = ApprovalRule.objects.filter(template=linux).first()
        if rule3:
            ApprovalRequest.objects.create(
                order=o3, rule=rule3, status="pending",
            )
        Notification.objects.create(
            user=requester, title="Bestellung eingereicht",
            message="Ihre Bestellung 'Produktions-Webserver' wurde eingereicht "
                    "und wartet auf Genehmigung.",
            category="order",
        )
        Notification.objects.create(
            user=approver, title="Neue Genehmigungsanfrage",
            message="Bestellung 'Produktions-Webserver' von test-requester "
                    "wartet auf Ihre Genehmigung.",
            category="approval",
        )

        # ORD-4: Validated — Dev-Umgebung
        o4 = Order.objects.create(
            user=requester, status=OrderStatus.VALIDATED,
            notes="Entwicklungsumgebung für Microservices-Projekt",
        )
        OrderItem.objects.create(
            order=o4, template=linux,
            parameters={
                "cpu": 4, "ram_gb": 8, "disk_gb": 80,
                "os_version": "ubuntu-24.04", "hostname": "dev-alpha-01",
                "ha": False, "backup": "weekly", "extra_disk_gb": 100,
            },
        )

        # ORD-5: Done — SAP Application Server
        o5 = Order.objects.create(
            user=requester, status=OrderStatus.DONE,
            notes="SAP S/4HANA Produktionsumgebung",
        )
        item5 = OrderItem.objects.create(
            order=o5, template=windows,
            parameters={
                "cpu": 8, "ram_gb": 16, "disk_gb": 200,
                "os_version": "win-server-2022", "hostname": "sap-prod-01",
                "domain_join": True, "backup": "daily", "extra_disk_gb": 200,
            },
        )
        Subscription.objects.create(
            user=requester, order_item=item5, status="active",
        )
        Notification.objects.create(
            user=requester, title="Bereitstellung abgeschlossen",
            message="SAP Application Server wurde erfolgreich bereitgestellt.",
            category="provisioning", is_read=True,
        )

        # ORD-6: Done — Monitoring Stack
        o6 = Order.objects.create(
            user=requester, status=OrderStatus.DONE,
            notes="Zentrales Monitoring für alle Standorte",
        )
        item6 = OrderItem.objects.create(
            order=o6, template=linux,
            parameters={
                "cpu": 4, "ram_gb": 8, "disk_gb": 100,
                "os_version": "almalinux-10", "hostname": "monitor-01",
                "ha": False, "backup": "daily", "extra_disk_gb": 200,
            },
        )
        Subscription.objects.create(
            user=requester, order_item=item6, status="active",
        )

        # ORD-7: Done — Domain Controller (by admin)
        o7 = Order.objects.create(
            user=admin, status=OrderStatus.DONE,
            notes="Zweiter DC für HA",
        )
        item7 = OrderItem.objects.create(
            order=o7, template=windows,
            parameters={
                "cpu": 4, "ram_gb": 8, "disk_gb": 100,
                "os_version": "win-server-2022", "hostname": "dc-standort2-01",
                "domain_join": True, "backup": "daily", "extra_disk_gb": 0,
            },
        )
        Subscription.objects.create(
            user=admin, order_item=item7, status="active",
        )

        # ORD-8: Pending Approval — Fileserver (by approver)
        o8 = Order.objects.create(
            user=approver, status=OrderStatus.PENDING_APPROVAL,
            notes="Ablösung alter NAS-Appliance",
        )
        OrderItem.objects.create(
            order=o8, template=windows,
            parameters={
                "cpu": 8, "ram_gb": 16, "disk_gb": 200,
                "os_version": "win-server-2022", "hostname": "fs-finance-01",
                "domain_join": True, "backup": "daily", "extra_disk_gb": 1000,
            },
        )
        rule8 = ApprovalRule.objects.filter(template=windows).first()
        if rule8:
            ApprovalRequest.objects.create(
                order=o8, rule=rule8, status="pending",
            )
        Notification.objects.create(
            user=approver, title="Bestellung eingereicht",
            message="Ihre Bestellung 'Fileserver Abteilung Finanzen' "
                    "wurde eingereicht.",
            category="order",
        )

        # Additional notifications
        Notification.objects.create(
            user=admin, title="System-Wartung",
            message="Geplante Wartung am Wochenende. Alle Services werden "
                    "kurzzeitig nicht erreichbar sein.",
            category="system",
        )
        Notification.objects.create(
            user=requester, title="Monitoring Stack bereitgestellt",
            message="Der Monitoring Stack wurde erfolgreich bereitgestellt "
                    "und ist unter monitor-01 erreichbar.",
            category="provisioning", is_read=True,
        )

    def _seed_audit_logs(self):
        requester = User.objects.get(username="test-requester")
        admin = User.objects.get(username="test-admin")

        AuditService.log(
            user=requester, action="order_created",
            resource_type="order", resource_id=1,
            details={"title": "Web-Cluster Q3 Projekt"},
        )
        AuditService.log(
            user=requester, action="order_created",
            resource_type="order", resource_id=2,
            details={"title": "Windows App-Server Buchhaltung"},
        )
        AuditService.log(
            user=requester, action="order_submitted",
            resource_type="order", resource_id=3,
            details={"title": "Produktions-Webserver", "items": 2},
        )
        AuditService.log(
            user=requester, action="order_created",
            resource_type="order", resource_id=5,
            details={"title": "SAP Application Server"},
        )
        AuditService.log(
            user=admin, action="order_created",
            resource_type="order", resource_id=7,
            details={"title": "Domain Controller Standort2"},
        )
        AuditService.log(
            user=admin, action="template_updated",
            resource_type="template", resource_id=1,
            details={"name": "Linux VM", "change": "parameters updated"},
        )
        AuditService.log(
            user=None, action="system_startup",
            resource_type="system", resource_id=0,
            details={"version": "1.0.0"},
        )
