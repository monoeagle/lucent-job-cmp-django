from pathlib import Path

import yaml

STUBS_DIR = Path(__file__).resolve().parent.parent.parent / "stubs" / "cmdb"


class CmdbStubClient:
    def __init__(self):
        self._locations = self._load("locations.yml")
        self._networks = self._load("networks.yml")
        self._tenants = self._load("tenants.yml")

    def _load(self, filename):
        with open(STUBS_DIR / filename) as f:
            return yaml.safe_load(f)

    def list_locations(self):
        return self._locations

    def list_networks(self, location_id=None, zone=None):
        nets = self._networks
        if location_id:
            nets = [n for n in nets if n["location_id"] == location_id]
        if zone:
            nets = [n for n in nets if n["zone"] == zone]
        return nets

    def list_tenants(self):
        return self._tenants

    def get_location(self, location_id):
        for loc in self._locations:
            if loc["id"] == location_id:
                return loc
        return None

    def get_zones(self):
        return sorted(set(n["zone"] for n in self._networks))
