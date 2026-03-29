import pytest
from apps.provisioning.models import DispatchLog
from apps.provisioning.services import ProvisioningService
from core.domain.value_objects import OrderStatus
from core.exceptions import ConflictError, NotFoundError
from tests.factories import OrderFactory, OrderItemFactory


@pytest.mark.django_db
class TestProvisioningServiceDispatch:
    def test_dispatch_order(self):
        order = OrderFactory(status=OrderStatus.APPROVED)
        item = OrderItemFactory(order=order)
        ProvisioningService.dispatch_order(order.pk)
        order.refresh_from_db()
        assert order.status == OrderStatus.PROVISIONING
        assert DispatchLog.objects.filter(order_item=item).count() == 1

    def test_dispatch_creates_log_per_item(self):
        order = OrderFactory(status=OrderStatus.APPROVED)
        OrderItemFactory(order=order)
        OrderItemFactory(order=order)
        ProvisioningService.dispatch_order(order.pk)
        assert DispatchLog.objects.count() == 2

    def test_dispatch_non_approved_raises(self):
        order = OrderFactory(status=OrderStatus.DRAFT)
        with pytest.raises(ConflictError):
            ProvisioningService.dispatch_order(order.pk)

    def test_dispatch_nonexistent_raises(self):
        with pytest.raises(NotFoundError):
            ProvisioningService.dispatch_order(99999)


@pytest.mark.django_db
class TestProvisioningServiceComplete:
    def test_complete_success(self):
        order = OrderFactory(status=OrderStatus.PROVISIONING)
        item = OrderItemFactory(order=order)
        log = DispatchLog.objects.create(
            order_item=item, pipeline_id="abc", status="running"
        )
        ProvisioningService.complete_dispatch(log.pk, success=True)
        log.refresh_from_db()
        assert log.status == "success"
        assert log.completed_at is not None

    def test_complete_failure(self):
        order = OrderFactory(status=OrderStatus.PROVISIONING)
        item = OrderItemFactory(order=order)
        log = DispatchLog.objects.create(
            order_item=item, pipeline_id="abc", status="running"
        )
        ProvisioningService.complete_dispatch(log.pk, success=False)
        log.refresh_from_db()
        assert log.status == "failed"

    def test_all_done_completes_order(self):
        order = OrderFactory(status=OrderStatus.PROVISIONING)
        item = OrderItemFactory(order=order)
        log = DispatchLog.objects.create(
            order_item=item, pipeline_id="abc", status="running"
        )
        ProvisioningService.complete_dispatch(log.pk, success=True)
        order.refresh_from_db()
        assert order.status == OrderStatus.DONE

    def test_any_failed_fails_order(self):
        order = OrderFactory(status=OrderStatus.PROVISIONING)
        item1 = OrderItemFactory(order=order)
        item2 = OrderItemFactory(order=order)
        log1 = DispatchLog.objects.create(
            order_item=item1, pipeline_id="a", status="running"
        )
        log2 = DispatchLog.objects.create(
            order_item=item2, pipeline_id="b", status="running"
        )
        ProvisioningService.complete_dispatch(log1.pk, success=True)
        ProvisioningService.complete_dispatch(log2.pk, success=False)
        order.refresh_from_db()
        assert order.status == OrderStatus.FAILED
