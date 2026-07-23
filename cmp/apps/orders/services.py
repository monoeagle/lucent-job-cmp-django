"""Service layer for the orders app."""
from apps.accounts.services import AccountService
from apps.catalog.services import CatalogService
from apps.notifications.services import NotificationService
from apps.orders.models import Order, OrderItem
from apps.orders.transitions import transition
from core.domain.enums import UserRole
from core.domain.value_objects import OrderStatus
from core.exceptions import ConflictError, NotFoundError, ValidationError


class OrderService:
    """Application service for order operations."""

    @staticmethod
    def create_order(user, notes=""):
        """Create a new draft order for a user."""
        return Order.objects.create(user=user, notes=notes)

    @staticmethod
    def get_order(order_id):
        """Get an order by ID or raise NotFoundError."""
        try:
            return Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            raise NotFoundError(f"Order with id={order_id} not found.")

    @staticmethod
    def get_order_for_user(order_id, user):
        """Get an order the given user may see.

        Owners see their own orders, approvers and above see all — anything
        else raises NotFoundError, so a foreign order stays indistinguishable
        from a missing one.
        """
        order = OrderService.get_order(order_id)
        if order.user_id == user.pk:
            return order
        if AccountService.is_at_least_role(user.role, UserRole.APPROVER):
            return order
        raise NotFoundError(f"Order with id={order_id} not found.")

    @staticmethod
    def list_user_orders(user_id):
        """Return all orders for a given user."""
        return list(Order.objects.filter(user_id=user_id))

    @staticmethod
    def add_item(order_id, template_id, parameters):
        """Add an item to a draft order, validating parameters."""
        order = OrderService.get_order(order_id)
        if order.status != OrderStatus.DRAFT:
            raise ConflictError("Items can only be added to draft orders.")
        template = CatalogService.get_template(template_id)
        errors = CatalogService.validate_template_parameters(
            template_id, parameters
        )
        if errors:
            raise ValidationError(
                "Parameter validation failed.", details=errors
            )
        return OrderItem.objects.create(
            order=order, template=template, parameters=parameters
        )

    @staticmethod
    def remove_item(item_id):
        """Remove an item from a draft order."""
        try:
            item = OrderItem.objects.select_related("order").get(pk=item_id)
        except OrderItem.DoesNotExist:
            raise NotFoundError(f"OrderItem with id={item_id} not found.")
        if item.order.status != OrderStatus.DRAFT:
            raise ConflictError(
                "Items can only be removed from draft orders."
            )
        item.delete()

    @staticmethod
    def submit_order(order_id, actor):
        """Submit a draft order and route it into the approval workflow."""
        # lazy: bricht den orders<->approvals-Importzyklus
        from apps.approvals.services import ApprovalService

        order = OrderService.get_order(order_id)
        if order.status != OrderStatus.DRAFT:
            raise ConflictError(
                f"Cannot submit order in status '{order.status}'."
            )
        if order.items.count() == 0:
            raise ValidationError("Cannot submit an order without items.")
        transition(order, OrderStatus.VALIDATED, actor)
        transition(order, OrderStatus.SUBMITTED, actor)
        if ApprovalService.needs_approval(order.pk):
            requests = ApprovalService.create_approval_requests(order.pk, actor)
            OrderService._notify_approvers(order, requests)
        else:
            transition(order, OrderStatus.APPROVED, actor)
        return order

    @staticmethod
    def _notify_approvers(order, requests):
        """Notify every user eligible to decide one of the created requests."""
        empfaenger = {}
        for role in {req.rule.approver_role for req in requests}:
            for user in AccountService.list_users_with_min_role(role):
                empfaenger[user.pk] = user
        for user in empfaenger.values():
            NotificationService.create(
                user,
                "Neue Genehmigung erforderlich",
                f"Bestellung #{order.pk} wartet auf Ihre Genehmigung.",
                category="info",
            )
