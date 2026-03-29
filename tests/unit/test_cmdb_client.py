from apps.cmdb.clients import CmdbStubClient


class TestCmdbStubClient:
    def setup_method(self):
        self.client = CmdbStubClient()

    def test_list_locations(self):
        assert len(self.client.list_locations()) == 3

    def test_list_networks(self):
        assert len(self.client.list_networks()) == 7

    def test_list_networks_by_location(self):
        nets = self.client.list_networks(location_id="loc-fra")
        assert len(nets) == 3
        assert all(n["location_id"] == "loc-fra" for n in nets)

    def test_list_networks_by_zone(self):
        nets = self.client.list_networks(zone="production")
        assert len(nets) == 3

    def test_list_tenants(self):
        assert len(self.client.list_tenants()) == 2

    def test_get_location_by_id(self):
        loc = self.client.get_location("loc-fra")
        assert loc["name"] == "Frankfurt"

    def test_get_location_not_found(self):
        assert self.client.get_location("nonexistent") is None

    def test_get_zones(self):
        zones = self.client.get_zones()
        assert "production" in zones
        assert "development" in zones
        assert "management" in zones
