"""Test factories for all models."""
import factory
from apps.accounts.models import User
from apps.catalog.models import ServiceTemplate
from apps.orders.models import Order, OrderItem
from core.domain.enums import UserRole
from core.domain.value_objects import OrderStatus


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user-{n}")
    password = factory.PostGenerationMethodCall("set_password", "test123")
    role = UserRole.REQUESTER


class ServiceTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ServiceTemplate

    name = factory.Sequence(lambda n: f"Template-{n}")
    category = "compute"
    description = factory.LazyAttribute(lambda o: f"Description for {o.name}")
    is_active = True
    version = 1
    parameters = factory.LazyFunction(lambda: [
        {"key": "cpu", "type": "integer", "label": "CPUs", "required": True, "default": 2},
        {"key": "ram_gb", "type": "integer", "label": "RAM (GB)", "required": True, "default": 4},
    ])


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    status = OrderStatus.DRAFT


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    template = factory.SubFactory(ServiceTemplateFactory)
    parameters = factory.LazyFunction(lambda: {"cpu": 2, "ram_gb": 4})
