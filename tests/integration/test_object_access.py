"""Objektbezogene Zugriffskontrolle (AP-22).

`test_role_access.py` prueft die Rollen-Ebene: Darf diese Rolle diese View
ueberhaupt aufrufen? Hier geht es um die Ebene darunter: Darf dieser Nutzer
*dieses* Objekt sehen oder aendern? Beide Requester bestehen die Mixin-Pruefung
— entscheidend ist der Besitz.
"""
import pytest
from django.urls import reverse

from apps.notifications.models import Notification
from apps.subscriptions.models import Subscription
from core.domain.enums import UserRole
from tests.factories import (
    OrderFactory,
    OrderItemFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestBestellungBesitz:
    def test_fremde_bestellung_ist_nicht_lesbar(self, client):
        besitzer = UserFactory()
        fremder = UserFactory()
        order = OrderFactory(user=besitzer)

        client.force_login(fremder)
        response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))

        assert response.status_code == 404

    def test_eigene_bestellung_bleibt_lesbar(self, client):
        besitzer = UserFactory()
        order = OrderFactory(user=besitzer)

        client.force_login(besitzer)
        response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))

        assert response.status_code == 200

    def test_approver_darf_fremde_bestellung_sehen(self, client):
        """Genehmigen setzt voraus, die fremde Bestellung lesen zu duerfen."""
        besitzer = UserFactory()
        approver = UserFactory(role=UserRole.APPROVER)
        order = OrderFactory(user=besitzer)

        client.force_login(approver)
        response = client.get(reverse("orders:detail", kwargs={"pk": order.pk}))

        assert response.status_code == 200


@pytest.mark.django_db
class TestAbonnementBesitz:
    def _abo(self, user):
        return Subscription.objects.create(user=user, order_item=OrderItemFactory())

    def test_fremdes_abo_ist_nicht_lesbar(self, client):
        fremder = UserFactory()
        abo = self._abo(UserFactory())

        client.force_login(fremder)
        response = client.get(
            reverse("subscriptions:detail", kwargs={"pk": abo.pk})
        )

        assert response.status_code == 404

    def test_eigenes_abo_bleibt_lesbar(self, client):
        besitzer = UserFactory()
        abo = self._abo(besitzer)

        client.force_login(besitzer)
        response = client.get(
            reverse("subscriptions:detail", kwargs={"pk": abo.pk})
        )

        assert response.status_code == 200

    def test_fremdes_abo_ist_nicht_kuendbar(self, client):
        fremder = UserFactory()
        abo = self._abo(UserFactory())

        client.force_login(fremder)
        client.post(reverse("subscriptions:cancel", kwargs={"pk": abo.pk}))

        abo.refresh_from_db()
        assert abo.status == "active"


@pytest.mark.django_db
class TestBenachrichtigungBesitz:
    def test_fremde_benachrichtigung_bleibt_ungelesen(self, client):
        fremder = UserFactory()
        notification = Notification.objects.create(
            user=UserFactory(), title="Privat", message="nur fuer den Besitzer"
        )

        client.force_login(fremder)
        client.post(
            reverse("notifications:mark_read", kwargs={"pk": notification.pk})
        )

        notification.refresh_from_db()
        assert notification.is_read is False

    def test_eigene_benachrichtigung_wird_gelesen(self, client):
        besitzer = UserFactory()
        notification = Notification.objects.create(
            user=besitzer, title="Meine", message="fuer mich"
        )

        client.force_login(besitzer)
        client.post(
            reverse("notifications:mark_read", kwargs={"pk": notification.pk})
        )

        notification.refresh_from_db()
        assert notification.is_read is True


@pytest.mark.django_db
class TestDebugLayout:
    def test_ist_nicht_anonym_erreichbar(self, client):
        response = client.get("/debug-layout/")

        assert response.status_code in (302, 404)


@pytest.mark.django_db
class TestGenehmigerRolle:
    """`ApprovalRule.approver_role` legt fest, wer entscheiden darf.

    Bis AP-22 war das Feld reine Dekoration: gepflegt in Admin und Seed,
    aber von keiner Pruefung gelesen.
    """

    def _anfrage(self, verlangte_rolle):
        from apps.approvals.models import ApprovalRequest, ApprovalRule
        from tests.factories import ServiceTemplateFactory

        rule = ApprovalRule.objects.create(
            template=ServiceTemplateFactory(),
            approver_role=verlangte_rolle,
            is_active=True,
        )
        return ApprovalRequest.objects.create(
            order=OrderFactory(user=UserFactory()), rule=rule, status="pending"
        )

    def test_zu_schwache_rolle_darf_nicht_genehmigen(self):
        from apps.approvals.services import ApprovalService
        from core.exceptions import ForbiddenError

        req = self._anfrage(UserRole.SUPERADMIN)
        approver = UserFactory(role=UserRole.APPROVER)

        with pytest.raises(ForbiddenError):
            ApprovalService.approve(req.pk, approver)

        req.refresh_from_db()
        assert req.status == "pending"

    def test_zu_schwache_rolle_darf_nicht_ablehnen(self):
        from apps.approvals.services import ApprovalService
        from core.exceptions import ForbiddenError

        req = self._anfrage(UserRole.SUPERADMIN)
        approver = UserFactory(role=UserRole.APPROVER)

        with pytest.raises(ForbiddenError):
            ApprovalService.reject(req.pk, approver, comment="nein")

        req.refresh_from_db()
        assert req.status == "pending"

    def test_verlangte_rolle_darf_genehmigen(self):
        from apps.approvals.services import ApprovalService

        req = self._anfrage(UserRole.SUPERADMIN)
        superadmin = UserFactory(role=UserRole.SUPERADMIN)

        ApprovalService.approve(req.pk, superadmin)

        req.refresh_from_db()
        assert req.status == "approved"

    def test_ablehnungskommentar_wird_validiert(self, client):
        """Der Kommentar kam bisher roh aus request.POST — ohne jede Grenze."""
        req = self._anfrage(UserRole.APPROVER)
        approver = UserFactory(role=UserRole.APPROVER)

        client.force_login(approver)
        client.post(
            reverse("approvals:reject", kwargs={"pk": req.pk}),
            {"comment": "x" * 3000},
        )

        req.refresh_from_db()
        assert req.status == "pending"

    def test_normaler_ablehnungskommentar_geht_durch(self, client):
        req = self._anfrage(UserRole.APPROVER)
        approver = UserFactory(role=UserRole.APPROVER)

        client.force_login(approver)
        client.post(
            reverse("approvals:reject", kwargs={"pk": req.pk}),
            {"comment": "Budget nicht freigegeben."},
        )

        req.refresh_from_db()
        assert req.status == "rejected"
        assert req.comment == "Budget nicht freigegeben."

    def test_hoehere_rolle_genuegt_ebenfalls(self):
        from apps.approvals.services import ApprovalService

        req = self._anfrage(UserRole.APPROVER)
        admin = UserFactory(role=UserRole.ADMIN)

        ApprovalService.approve(req.pk, admin)

        req.refresh_from_db()
        assert req.status == "approved"
