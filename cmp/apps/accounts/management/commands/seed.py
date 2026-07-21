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

        # ORD-1: Draft — Web-Cluster Q3 Projekt (1x Linux VM)
        o1 = Order.objects.create(
            user=requester, status=OrderStatus.DRAFT,
            notes="Neues Kundenprojekt Q3",
        )
        OrderItem.objects.create(
            order=o1, template=linux,
            parameters={
                "system_type": "web", "mandant": "a1",
                "security_area": "sec1", "org_area": "ou1",
                "location": "standort1", "dns_server": "10.1.0.10",
                "lb_subnet": "10.1.100.0/24",
                "ad_tier": "tier2", "network_layer": "frontend",
                "network_vlan": "vlan100", "ad_assignment": "app",
                "vmware_cluster": "single-site",
                "tshirt_size": "s", "cpu_cores": 2, "ram_gb": 4,
                "os_disk_gb": 60, "extra_disk_1": 0, "extra_disk_2": 0,
                "extra_disk_3": 0, "extra_disk_4": 0,
                "description_text": "Nginx Reverse Proxy fuer Kundenprojekt Q3",
                "orderer_email": "requester@test.local",
                "responsible_email": "ops-team@test.local",
                "contact_group_email": "web-team@test.local",
                "ticket_id": "JIRA-4711",
                "maintenance_window": "wed-02-06", "patch_wave": "wave1",
                "backup_enabled": True, "site_replication": False,
                "os_template": "ubuntu-2404",
            },
        )

        # ORD-2: Draft — Windows App-Server Buchhaltung (1x Windows VM)
        o2 = Order.objects.create(
            user=requester, status=OrderStatus.DRAFT,
            notes="App-Server fuer Buchhaltung",
        )
        OrderItem.objects.create(
            order=o2, template=windows,
            parameters={
                "system_type": "app", "mandant": "b1",
                "security_area": "sec2", "org_area": "ou2",
                "location": "standort2", "dns_server": "10.3.0.10",
                "ad_tier": "tier1", "network_layer": "backend",
                "network_vlan": "vlan110", "ad_assignment": "prod",
                "vmware_cluster": "dual-site",
                "tshirt_size": "l", "cpu_cores": 8, "ram_gb": 16,
                "os_disk_gb": 120, "extra_disk_1": 100, "extra_disk_2": 0,
                "extra_disk_3": 0, "extra_disk_4": 0,
                "description_text": "Buchhaltungs-Applikationsserver",
                "orderer_email": "requester@test.local",
                "responsible_email": "finance-ops@test.local",
                "contact_group_email": "finance-team@test.local",
                "ticket_id": "JIRA-4712",
                "maintenance_window": "sun-02-06", "patch_wave": "wave3",
                "backup_enabled": True, "site_replication": True,
                "os_template": "win2022",
            },
        )

        # ORD-3: Pending Approval — Produktions-Webserver (2 Items)
        o3 = Order.objects.create(
            user=requester, status=OrderStatus.PENDING_APPROVAL,
            notes="Erweiterung Webfarm fuer Black Friday",
        )
        OrderItem.objects.create(
            order=o3, template=linux,
            parameters={
                "system_type": "web", "mandant": "a1",
                "security_area": "sec1", "org_area": "ou1",
                "location": "standort1", "dns_server": "10.1.0.10",
                "lb_subnet": "10.1.100.0/24",
                "ad_tier": "tier2", "network_layer": "frontend",
                "network_vlan": "vlan100", "ad_assignment": "prod",
                "vmware_cluster": "dual-site",
                "tshirt_size": "l", "cpu_cores": 8, "ram_gb": 16,
                "os_disk_gb": 120, "extra_disk_1": 0, "extra_disk_2": 0,
                "extra_disk_3": 0, "extra_disk_4": 0,
                "description_text": "Nginx Reverse Proxy Produktion",
                "orderer_email": "requester@test.local",
                "responsible_email": "ops-team@test.local",
                "contact_group_email": "web-team@test.local",
                "ticket_id": "JIRA-5001",
                "maintenance_window": "sun-02-06", "patch_wave": "wave3",
                "backup_enabled": True, "site_replication": True,
                "os_template": "ubuntu-2404",
            },
        )
        OrderItem.objects.create(
            order=o3, template=linux,
            parameters={
                "system_type": "db", "mandant": "a1",
                "security_area": "sec1", "org_area": "ou1",
                "location": "standort1", "dns_server": "10.1.0.10",
                "ad_tier": "tier1", "network_layer": "backend",
                "network_vlan": "vlan100", "ad_assignment": "prod",
                "vmware_cluster": "dual-site",
                "tshirt_size": "xl", "cpu_cores": 16, "ram_gb": 32,
                "os_disk_gb": 200, "extra_disk_1": 500, "extra_disk_2": 200,
                "extra_disk_3": 0, "extra_disk_4": 0,
                "description_text": "PostgreSQL Datenbank-Server Produktion",
                "orderer_email": "requester@test.local",
                "responsible_email": "dba-team@test.local",
                "contact_group_email": "db-team@test.local",
                "ticket_id": "JIRA-5002",
                "maintenance_window": "sun-02-06", "patch_wave": "wave3",
                "backup_enabled": True, "site_replication": True,
                "os_template": "rhel9",
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

        # ORD-4: Submitted — Dev-Umgebung Team Alpha (1x Linux VM)
        o4 = Order.objects.create(
            user=requester, status=OrderStatus.SUBMITTED,
            notes="Entwicklungsumgebung fuer Microservices-Projekt",
        )
        OrderItem.objects.create(
            order=o4, template=linux,
            parameters={
                "system_type": "app", "mandant": "a1",
                "security_area": "sec2", "org_area": "ou1",
                "location": "standort1", "dns_server": "10.2.0.10",
                "ad_tier": "tier1", "network_layer": "backend",
                "network_vlan": "vlan200", "ad_assignment": "debug",
                "vmware_cluster": "single-site",
                "tshirt_size": "m", "cpu_cores": 4, "ram_gb": 8,
                "os_disk_gb": 80, "extra_disk_1": 100, "extra_disk_2": 0,
                "extra_disk_3": 0, "extra_disk_4": 0,
                "description_text": "Docker Host fuer Microservices-Entwicklung",
                "orderer_email": "requester@test.local",
                "responsible_email": "dev-lead@test.local",
                "contact_group_email": "team-alpha@test.local",
                "ticket_id": "JIRA-4800",
                "maintenance_window": "wed-02-06", "patch_wave": "wave1",
                "backup_enabled": True, "site_replication": False,
                "os_template": "ubuntu-2404",
            },
        )

        # ORD-5: Done — SAP Application Server (1x Windows VM) + Subscription
        o5 = Order.objects.create(
            user=requester, status=OrderStatus.DONE,
            notes="SAP S/4HANA Produktionsumgebung",
        )
        item5 = OrderItem.objects.create(
            order=o5, template=windows,
            parameters={
                "system_type": "app", "mandant": "a1",
                "security_area": "sec1", "org_area": "ou1",
                "location": "standort1", "dns_server": "10.1.0.10",
                "ad_tier": "tier1", "network_layer": "backend",
                "network_vlan": "vlan100", "ad_assignment": "prod",
                "vmware_cluster": "dual-site",
                "tshirt_size": "l", "cpu_cores": 8, "ram_gb": 16,
                "os_disk_gb": 120, "extra_disk_1": 200, "extra_disk_2": 100,
                "extra_disk_3": 0, "extra_disk_4": 0,
                "description_text": "SAP S/4HANA Produktionsumgebung",
                "orderer_email": "requester@test.local",
                "responsible_email": "sap-admin@test.local",
                "contact_group_email": "sap-team@test.local",
                "ticket_id": "JIRA-3500",
                "maintenance_window": "sun-02-06", "patch_wave": "wave3",
                "backup_enabled": True, "site_replication": True,
                "os_template": "win2022",
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

        # ORD-6: Done — Monitoring Stack (1x Linux VM) + Subscription
        o6 = Order.objects.create(
            user=requester, status=OrderStatus.DONE,
            notes="Zentrales Monitoring fuer alle Standorte",
        )
        item6 = OrderItem.objects.create(
            order=o6, template=linux,
            parameters={
                "system_type": "app", "mandant": "a1",
                "security_area": "sec1", "org_area": "ou1",
                "location": "standort1", "dns_server": "10.1.0.10",
                "ad_tier": "tier1", "network_layer": "management",
                "network_vlan": "vlan100", "ad_assignment": "app",
                "vmware_cluster": "single-site",
                "tshirt_size": "m", "cpu_cores": 4, "ram_gb": 8,
                "os_disk_gb": 80, "extra_disk_1": 200, "extra_disk_2": 100,
                "extra_disk_3": 0, "extra_disk_4": 0,
                "description_text": "Prometheus + Grafana Monitoring Stack",
                "orderer_email": "requester@test.local",
                "responsible_email": "ops-team@test.local",
                "contact_group_email": "monitoring-team@test.local",
                "ticket_id": "JIRA-3200",
                "maintenance_window": "sat-02-06", "patch_wave": "wave2",
                "backup_enabled": True, "site_replication": False,
                "os_template": "alma10",
            },
        )
        Subscription.objects.create(
            user=requester, order_item=item6, status="active",
        )

        # ORD-7: Done — Domain Controller Standort2 (by admin, 1x Windows VM)
        o7 = Order.objects.create(
            user=admin, status=OrderStatus.DONE,
            notes="Zweiter DC fuer HA",
        )
        item7 = OrderItem.objects.create(
            order=o7, template=windows,
            parameters={
                "system_type": "dc", "mandant": "a1",
                "security_area": "sec1", "org_area": "ou1",
                "location": "standort2", "dns_server": "10.3.0.10",
                "ad_tier": "tier0", "network_layer": "backend",
                "network_vlan": "vlan100", "ad_assignment": "prod",
                "vmware_cluster": "dual-site",
                "tshirt_size": "m", "cpu_cores": 4, "ram_gb": 8,
                "os_disk_gb": 80, "extra_disk_1": 0, "extra_disk_2": 0,
                "extra_disk_3": 0, "extra_disk_4": 0,
                "description_text": "Zweiter Domain Controller fuer HA am Standort2",
                "orderer_email": "admin@test.local",
                "responsible_email": "ad-team@test.local",
                "contact_group_email": "infra-team@test.local",
                "ticket_id": "JIRA-2800",
                "maintenance_window": "sun-02-06", "patch_wave": "wave3",
                "backup_enabled": True, "site_replication": True,
                "os_template": "win2022",
            },
        )
        Subscription.objects.create(
            user=admin, order_item=item7, status="active",
        )

        # ORD-8: Pending Approval — Fileserver Abteilung Finanzen (by approver)
        o8 = Order.objects.create(
            user=approver, status=OrderStatus.PENDING_APPROVAL,
            notes="Abloesung alter NAS-Appliance",
        )
        OrderItem.objects.create(
            order=o8, template=windows,
            parameters={
                "system_type": "fp", "mandant": "b1",
                "security_area": "sec1", "org_area": "ou2",
                "location": "standort1", "dns_server": "10.1.0.10",
                "ad_tier": "tier1", "network_layer": "backend",
                "network_vlan": "vlan100", "ad_assignment": "prod",
                "vmware_cluster": "dual-site",
                "tshirt_size": "l", "cpu_cores": 8, "ram_gb": 16,
                "os_disk_gb": 120, "extra_disk_1": 1000, "extra_disk_2": 1000,
                "extra_disk_3": 500, "extra_disk_4": 0,
                "description_text": "Fileserver zur Abloesung alter NAS-Appliance",
                "orderer_email": "approver@test.local",
                "responsible_email": "storage-team@test.local",
                "contact_group_email": "finance-team@test.local",
                "ticket_id": "JIRA-4900",
                "maintenance_window": "sun-02-06", "patch_wave": "wave3",
                "backup_enabled": True, "site_replication": True,
                "os_template": "win2022",
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
            details={"version": "1.3.3"},
        )
