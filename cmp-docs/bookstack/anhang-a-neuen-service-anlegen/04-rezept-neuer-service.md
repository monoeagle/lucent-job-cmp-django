# A.4 Rezept: kompletter neuer Service

Beispiel: Der Katalog soll um „PostgreSQL-Datenbank" erweitert werden — von der Kachel im
Katalog bis zur Provisionierung. Der Ablauf gilt für jeden neuen Service.

## 1. Ausgangslage

Ein neuer Service braucht **keine neue Django-App, keine neue View, keine neue Vorlage und
keine Migration.** Alles Nötige entsteht aus einem `ServiceTemplate`-Datensatz. Zu tun sind
fünf Dinge:

1. Vorlage mit Parametern definieren
2. Kategorie wählen
3. Genehmigungsregel festlegen
4. In die Datenbank bringen
5. Provisionierung prüfen

## 2. Schritt 1 — Test zuerst

```python
from apps.catalog.services import SEED_TEMPLATES


def test_postgres_vorlage_existiert():
    namen = [t["name"] for t in SEED_TEMPLATES]
    assert "PostgreSQL Datenbank" in namen


def test_postgres_hat_pflichtparameter():
    t = [t for t in SEED_TEMPLATES if t["name"] == "PostgreSQL Datenbank"][0]
    keys = [p["key"] for p in t["parameters"]]
    assert "db_version" in keys
    assert "db_size_gb" in keys
```

Ausführen und **rot sehen**:

```
venv/bin/python -m pytest tests/unit/test_catalog_service.py -q
```

## 3. Schritt 2 — Vorlage definieren

In `cmp/apps/catalog/services.py`, Liste `SEED_TEMPLATES` (ab Zeile 333):

```python
{
    "name": "PostgreSQL Datenbank",
    "category": "database",
    "description": "Verwaltete PostgreSQL-Instanz.",
    "parameters": [
        {
            "key": "db_version", "label": "PostgreSQL-Version", "type": "enum",
            "required": True, "default": "16",
            "tofu_variable_name": "db_version",
            "display_order": 10, "group": "Datenbank",
            "constraints": {"options": [
                {"value": "15", "label": "PostgreSQL 15", "enabled": True},
                {"value": "16", "label": "PostgreSQL 16", "enabled": True},
            ]},
            "depends_on": [], "affects_options_of": [],
        },
        {
            "key": "db_size_gb", "label": "Speicher", "type": "integer",
            "required": True, "default": 20,
            "tofu_variable_name": "db_size_gb",
            "display_order": 11, "group": "Datenbank",
            "constraints": {"min": 10, "max": 2000, "step": 10, "unit": "GB"},
            "depends_on": [], "affects_options_of": [],
        },
        {
            "key": "description_text", "label": "Funktionsbeschreibung", "type": "string",
            "required": True,
            "tofu_variable_name": "description_text",
            "display_order": 60, "group": "Server Informationen",
            "constraints": {"min_length": 5, "max_length": 500},
            "depends_on": [], "affects_options_of": [],
        },
    ],
}
```

Hinweise:

- Die VM-Vorlagen setzen ihre Parameterliste aus `SHARED_PARAMS` plus einem
  betriebssystemspezifischen Teil zusammen (`_build_vm_params`, `cmp/apps/catalog/services.py:324`).
  Für einen Service, der **keine** VM ist, wäre das falsch — `SHARED_PARAMS` enthält Netzwerk-,
  Platzierungs- und Sizing-Felder, die auf eine Datenbank nicht passen. Deshalb hier eine
  eigene Liste.
- Jede `group` erzeugt einen Wizard-Schritt. Zwei Gruppen bedeuten hier: Kontext →
  Datenbank → Server Informationen → Zusammenfassung.
- Schranken wie `min`/`max` sind heute beschreibend (siehe A.2, Abschnitt 5).

## 4. Schritt 3 — Kategorie

Die Kategorie steuert den Filter im Katalog. Erlaubt sind die Werte aus `TemplateCategory`
(`cmp/apps/catalog/models.py:6`): `compute`, `database`, `container`, `network`, `storage`.

**Achtung, geprüft:** Das Modellfeld `category` ist ein `CharField(max_length=30)` **ohne**
`choices` (`cmp/apps/catalog/models.py:16`). Ein frei erfundener Wert lässt sich also
speichern — er taucht dann aber im Filter nicht auf, weil das Filterformular seine Auswahl
aus `TemplateCategory.choices` bildet (`cmp/apps/catalog/forms.py:11`). Wer eine neue
Kategorie braucht, ergänzt sie in `TemplateCategory`, nicht nur im Vorlagen-Datensatz.

## 5. Schritt 4 — Genehmigungsregel

Ob eine Bestellung genehmigt werden muss, entscheidet eine `ApprovalRule` je Vorlage
(`cmp/apps/approvals/models.py`). Der Seed legt für **jede** vorhandene Vorlage eine Regel mit
`approver_role="approver"` an (`cmp/apps/accounts/management/commands/seed.py:41-46`). Für eine
Vorlage, die ohne Genehmigung auskommen soll, wird entweder keine Regel angelegt oder die
vorhandene auf `is_active=False` gesetzt.

**Ist-Stand, geprüft am 2026-07-22:** `ApprovalService.create_approval_requests`
(`cmp/apps/approvals/services.py:25`) wird im Anwendungscode nirgends aufgerufen — die
Genehmigungs-Warteschlange füllt sich im Betrieb daher nicht von selbst. Das ist eine bekannte
Lücke der Bestellkette und als Arbeitspaket AP-13 erfasst. Für einen neuen Service heißt das:
Die Regel anzulegen ist richtig und nötig, ihre Wirkung entsteht erst mit AP-13.

## 6. Schritt 5 — In die Datenbank bringen

Wie in A.3, Abschnitt 5. Für einen **neuen** Namen ist es einfacher als für eine Änderung:
`CatalogService.seed_templates()` legt Vorlagen an, die noch nicht existieren
(`cmp/apps/catalog/services.py:411`). Ein Lauf von

```
venv/bin/python cmp/manage.py seed
```

genügt für den neuen Service. Beachte: Der Seed-Befehl legt Demodaten (Bestellungen,
Genehmigungen, Audit-Einträge) nur beim **ersten** Lauf an, wenn Vorlagen neu entstanden sind
(`cmp/apps/accounts/management/commands/seed.py:26`).

## 7. Schritt 6 — Provisionierung

Hier ist nichts zu tun. `ProvisioningService.dispatch_order`
(`cmp/apps/provisioning/services.py:15`) arbeitet vorlagenunabhängig: Es übergibt je Position
den Vorlagennamen und die Parameter an den Pipeline-Client und schreibt einen `DispatchLog`.
Ein neuer Service braucht dort keine Sonderbehandlung.

Im Entwicklungsbetrieb steht dahinter der `GitLabStubClient`
(`cmp/apps/provisioning/clients.py`), der eine Pipeline-Kennung erfindet, statt eine echte
Pipeline zu starten — siehe Kapitel „Stubs und Mocks".

## 8. Probe: so siehst du, dass es geklappt hat

- [ ] `venv/bin/python -m pytest -q` — vollständig grün
- [ ] `/catalog/` zeigt die neue Kachel
- [ ] Filter „Kategorie = database" findet sie
- [ ] `/catalog/<pk>/` zeigt Beschreibung und Parameterübersicht
- [ ] `/orders/create/<pk>/form/` zeigt alle Felder in der gewünschten Reihenfolge
- [ ] `/orders/create/<pk>/` zeigt die erwarteten Wizard-Schritte
- [ ] Eine Bestellung lässt sich anlegen; `order_items.parameters` enthält die Werte

## 9. Zusammenfassung

Ein neuer Service ist ein Datensatz, kein Modul. Zu entscheiden sind Parameterliste,
Kategorie und Genehmigungsregel; Katalog, Formular, Wizard und Provisionierung ergeben sich
daraus. Nicht übernehmen sollte man `SHARED_PARAMS`, wenn der Service keine VM ist.

> Quelle: `cmp/apps/catalog/services.py:324,333,411`, `cmp/apps/catalog/models.py:6,16`, `cmp/apps/catalog/forms.py:11`, `cmp/apps/approvals/services.py:25`, `cmp/apps/accounts/management/commands/seed.py:26,41`, `cmp/apps/provisioning/services.py:15` — am Code geprüft 2026-07-22
