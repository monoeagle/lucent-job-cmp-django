"""Zentraler Order-Statuswechsel — der einzige erlaubte Ort fuer order.status = ...

Buendelt Uebergangspruefung (StatusMachine), Statuswechsel und Audit-Log.
Bewusst OHNE Benachrichtigungen: deren Empfaenger/Text sind je Uebergang
verschieden und bleiben am jeweiligen Aufrufort in den Services.

Wohnt in apps/orders/ (nicht core/domain/), weil er AuditService aus apps/
aufruft und core nicht auf apps zeigen darf.
"""
from apps.audit.services import AuditService
from core.domain.value_objects import StatusMachine


def transition(order, to_status, actor, **details):
    """Validate + apply a status change and record it in the audit log."""
    from_status = str(order.status)
    StatusMachine.validate_transition(order.status, to_status)
    order.status = to_status
    order.save()
    action = f"order.{getattr(to_status, 'value', to_status)}"
    AuditService.log(
        actor,
        action,
        "order",
        order.pk,
        details={"from": from_status, **details},
    )
