# Stubs & Mocks

## Übersicht

MPP verwendet Stubs für externe Systeme, die in der Entwicklung nicht verfügbar sind. Stubs haben das gleiche Interface wie die Live-Implementierung — der Wechsel erfolgt über ein Setting.

## CMDB Stub

**Klasse:** `apps.cmdb.clients.CmdbStubClient`
**Daten:** `mpp/stubs/cmdb/`

Simuliert eine CMDB (Configuration Management Database) mit YAML-Dateien:

### locations.yml (3 Standorte)

| ID | Name | Datacenter |
|----|------|-----------|
| loc-fra | Frankfurt | DC-FRA-01 |
| loc-ber | Berlin | DC-BER-01 |
| loc-muc | München | DC-MUC-01 |

### networks.yml (7 Netzwerke)

| ID | Name | Location | Zone | VLAN | CIDR |
|----|------|----------|------|------|------|
| net-prod-fra | Production Frankfurt | loc-fra | production | 100 | 10.1.0.0/24 |
| net-dev-fra | Development Frankfurt | loc-fra | development | 200 | 10.2.0.0/24 |
| net-prod-ber | Production Berlin | loc-ber | production | 100 | 10.3.0.0/24 |
| net-mgmt-fra | Management Frankfurt | loc-fra | management | 300 | 10.4.0.0/24 |
| net-dev-ber | Development Berlin | loc-ber | development | 200 | 10.5.0.0/24 |
| net-prod-muc | Production München | loc-muc | production | 100 | 10.6.0.0/24 |
| net-dev-muc | Development München | loc-muc | development | 200 | 10.7.0.0/24 |

**3 Zonen:** production, development, management

### tenants.yml (2 Mandanten)

| ID | Name |
|----|------|
| tenant-alpha | Alpha Corp |
| tenant-beta | Beta GmbH |

### Methoden

```python
client = CmdbStubClient()
client.list_locations()                    # → 3 Standorte
client.list_networks(location_id="loc-fra")  # → 3 Netzwerke in Frankfurt
client.list_networks(zone="production")     # → 3 Produktions-Netzwerke
client.list_tenants()                       # → 2 Mandanten
client.get_location("loc-fra")             # → {"id": "loc-fra", "name": "Frankfurt", ...}
client.get_zones()                          # → ["development", "management", "production"]
```

## GitLab Stub Client

**Klasse:** `apps.provisioning.clients.GitLabStubClient`

Simuliert GitLab-Pipeline-Triggers in-memory (kein externer Service nötig).

```python
client = GitLabStubClient()
result = client.trigger_pipeline("Linux VM", {"cpu": 4})
# → {"pipeline_id": "a1b2c3d4e5f6", "status": "running"}

client.get_pipeline_status(result["pipeline_id"])
# → "running"

client.complete_pipeline(result["pipeline_id"], success=True)
client.get_pipeline_status(result["pipeline_id"])
# → "success"
```

Im Development-Modus läuft Celery mit `ALWAYS_EAGER=True` — Provisioning-Tasks werden synchron ausgeführt, kein Redis erforderlich.

## Seed-Daten

`python manage.py seed` erstellt:

| Daten | Anzahl |
|-------|--------|
| Benutzer | 5 (test-requester, -approver, -admin, -multi, -superadmin) |
| Service-Templates | 3 (Linux VM, Windows VM, PostgreSQL DB) |
| Approval-Regeln | 3 (eine pro Template) |
| Tenant-Zuordnungen | 5 (alle User → tenant-alpha) |

## Umschaltung Stub → Live

Der Wechsel zu echten Systemen erfordert:

1. **CMDB:** Neue `CmdbLiveClient`-Klasse mit gleichem Interface erstellen
2. **GitLab:** `GitLabLiveClient` mit echtem API-Aufruf erstellen
3. **Setting:** Client-Klasse über Setting konfigurierbar machen

Das Interface (Methoden-Signaturen) ist identisch — der Wechsel ist ein Einzeiler pro Client.
