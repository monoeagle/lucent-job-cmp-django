"""Celery tasks for provisioning operations."""
from celery import shared_task

from .services import ProvisioningService


@shared_task
def dispatch_provisioning(order_id):
    """Dispatch all items of an approved order and (Stub) complete them at once."""
    ProvisioningService.dispatch_order(order_id)
    # Stub: keine echte Pipeline -> Rueckmeldung sofort simulieren.
    # AP-20 ersetzt das durch echtes Polling (complete_provisioning).
    from apps.provisioning.models import DispatchLog

    for log in DispatchLog.objects.filter(
        order_item__order_id=order_id, status="running"
    ):
        ProvisioningService.complete_dispatch(log.pk, success=True)


@shared_task
def complete_provisioning(dispatch_log_id, success=True):
    """Mark a dispatch as complete."""
    ProvisioningService.complete_dispatch(dispatch_log_id, success=success)
