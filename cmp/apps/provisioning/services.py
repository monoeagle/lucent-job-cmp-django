"""Service layer for provisioning operations."""
from django.utils import timezone

from apps.notifications.services import NotificationService
from apps.orders.services import OrderService
from apps.orders.transitions import transition
from apps.provisioning.clients import GitLabStubClient
from apps.provisioning.models import DispatchLog
from apps.subscriptions.services import SubscriptionService
from core.domain.value_objects import OrderStatus
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
        transition(order, OrderStatus.PROVISIONING, None)

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
            transition(order, OrderStatus.FAILED, None)
            NotificationService.create(
                order.user,
                "Bereitstellung fehlgeschlagen",
                f"Die Bereitstellung Ihrer Bestellung #{order.pk} ist "
                "fehlgeschlagen.",
                category="error",
            )
        else:
            transition(order, OrderStatus.DONE, None)
            SubscriptionService.create_from_order(order.pk)
            NotificationService.create(
                order.user,
                "Bestellung abgeschlossen",
                f"Ihre Bestellung #{order.pk} wurde erfolgreich bereitgestellt.",
                category="success",
            )
