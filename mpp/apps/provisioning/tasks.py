"""Celery tasks for provisioning operations."""
from celery import shared_task

from .services import ProvisioningService


@shared_task
def dispatch_provisioning(order_id):
    """Dispatch all items of an approved order."""
    ProvisioningService.dispatch_order(order_id)


@shared_task
def complete_provisioning(dispatch_log_id, success=True):
    """Mark a dispatch as complete."""
    ProvisioningService.complete_dispatch(dispatch_log_id, success=success)
