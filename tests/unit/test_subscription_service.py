import pytest
from apps.subscriptions.models import Subscription
from apps.subscriptions.services import SubscriptionService
from core.domain.value_objects import OrderStatus
from core.exceptions import ConflictError
from tests.factories import UserFactory, OrderFactory, OrderItemFactory


@pytest.mark.django_db
class TestSubscriptionServiceCreate:
    def test_create_from_completed_order(self):
        user = UserFactory()
        order = OrderFactory(user=user, status=OrderStatus.DONE)
        OrderItemFactory(order=order)
        subs = SubscriptionService.create_from_order(order.pk)
        assert len(subs) == 1
        assert subs[0].status == "active"

    def test_create_from_non_done_raises(self):
        order = OrderFactory(status=OrderStatus.DRAFT)
        with pytest.raises(ConflictError):
            SubscriptionService.create_from_order(order.pk)


@pytest.mark.django_db
class TestSubscriptionServiceList:
    def test_list_user_subscriptions(self):
        user = UserFactory()
        order = OrderFactory(user=user, status=OrderStatus.DONE)
        OrderItemFactory(order=order)
        SubscriptionService.create_from_order(order.pk)
        assert len(SubscriptionService.list_user_subscriptions(user.pk)) == 1

    def test_empty_when_no_subs(self):
        user = UserFactory()
        assert len(SubscriptionService.list_user_subscriptions(user.pk)) == 0


@pytest.mark.django_db
class TestSubscriptionServiceCancel:
    def test_cancel(self):
        user = UserFactory()
        order = OrderFactory(user=user, status=OrderStatus.DONE)
        OrderItemFactory(order=order)
        subs = SubscriptionService.create_from_order(order.pk)
        SubscriptionService.cancel(subs[0].pk)
        subs[0].refresh_from_db()
        assert subs[0].status == "cancelled"

    def test_cancel_already_cancelled_raises(self):
        user = UserFactory()
        order = OrderFactory(user=user, status=OrderStatus.DONE)
        OrderItemFactory(order=order)
        subs = SubscriptionService.create_from_order(order.pk)
        SubscriptionService.cancel(subs[0].pk)
        with pytest.raises(ConflictError):
            SubscriptionService.cancel(subs[0].pk)
