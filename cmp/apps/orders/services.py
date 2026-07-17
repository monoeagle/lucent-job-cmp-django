"""Service layer for the orders app."""
from apps.catalog.services import CatalogService
from apps.orders.models import Order, OrderItem
from core.domain.value_objects import OrderStatus, StatusMachine
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
    def submit_order(order_id):
        """Submit a draft order (draft -> validated -> submitted)."""
        order = OrderService.get_order(order_id)
        if order.status != OrderStatus.DRAFT:
            raise ConflictError(
                f"Cannot submit order in status '{order.status}'."
            )
        if order.items.count() == 0:
            raise ValidationError("Cannot submit an order without items.")
        StatusMachine.validate_transition(order.status, OrderStatus.VALIDATED)
        order.status = OrderStatus.VALIDATED
        order.save()
        StatusMachine.validate_transition(order.status, OrderStatus.SUBMITTED)
        order.status = OrderStatus.SUBMITTED
        order.save()
        return order
