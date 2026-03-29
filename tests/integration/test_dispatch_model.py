import pytest
from apps.provisioning.models import DispatchLog
from tests.factories import OrderItemFactory


@pytest.mark.django_db
class TestDispatchLogModel:
    def test_create(self):
        item = OrderItemFactory()
        log = DispatchLog.objects.create(
            order_item=item,
            pipeline_id="abc123",
            status="running",
            payload={"template": "VM", "params": {"cpu": 4}},
        )
        assert log.pk is not None

    def test_str(self):
        item = OrderItemFactory()
        log = DispatchLog.objects.create(
            order_item=item, pipeline_id="abc123", status="running"
        )
        assert "abc123" in str(log)

    def test_has_dispatched_at(self):
        item = OrderItemFactory()
        log = DispatchLog.objects.create(
            order_item=item, pipeline_id="abc", status="running"
        )
        assert log.dispatched_at is not None

    def test_completed_at_nullable(self):
        item = OrderItemFactory()
        log = DispatchLog.objects.create(
            order_item=item, pipeline_id="abc", status="running"
        )
        assert log.completed_at is None

    def test_default_payload(self):
        item = OrderItemFactory()
        log = DispatchLog.objects.create(
            order_item=item, pipeline_id="abc", status="running"
        )
        assert log.payload == {}
