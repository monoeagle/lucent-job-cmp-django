"""Service layer for provisioning operations."""
from django.utils import timezone

from apps.orders.services import OrderService
from apps.provisioning.clients import GitLabStubClient
from apps.provisioning.models import DispatchLog
from core.domain.value_objects import OrderStatus, StatusMachine
from core.exceptions import ConflictError, NotFoundError


class ProvisioningService:
    """Application service for dispatching and completing provisioning."""

    @staticmethod
    def dispatch_order(order_id):
        """Dispatch all items of an approved order to the provisioning pipeline."""
        order = OrderService.get_order(order_id)
        if order.status != OrderStatus.APPROVED:
            raise ConflictError(
                f"Cannot dispatch order in status '{order.status}'."
            )
        StatusMachine.validate_transition(order.status, OrderStatus.PROVISIONING)
        order.status = OrderStatus.PROVISIONING
        order.save()

        client = GitLabStubClient()
        for item in order.items.select_related("template").all():
            result = client.trigger_pipeline(
                item.template.name, item.parameters
            )
            DispatchLog.objects.create(
                order_item=item,
                pipeline_id=result["pipeline_id"],
                status="running",
                payload={
                    "template": item.template.name,
                    "parameters": item.parameters,
                },
            )

    @staticmethod
    def complete_dispatch(dispatch_log_id, success=True):
        """Mark a dispatch log as complete and update order status if all done."""
        try:
            log = DispatchLog.objects.select_related(
                "order_item__order"
            ).get(pk=dispatch_log_id)
        except DispatchLog.DoesNotExist:
            raise NotFoundError(
                f"DispatchLog with id={dispatch_log_id} not found."
            )

        log.status = "success" if success else "failed"
        log.completed_at = timezone.now()
        log.save()

        order = log.order_item.order
        all_logs = DispatchLog.objects.filter(order_item__order=order)

        if all_logs.filter(status="running").exists():
            return

        if all_logs.filter(status="failed").exists():
            order.status = OrderStatus.FAILED
        else:
            order.status = OrderStatus.DONE
        order.save()
