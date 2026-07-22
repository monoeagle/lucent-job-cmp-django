# A.3 Rezept: neue Bestelloption an einem bestehenden Service

Der häufigste Fall. Beispiel: An der Linux-VM soll ein Auswahlfeld „Monitoring-Profil"
ergänzt werden. Der Ablauf ist für jede neue Option derselbe.

## 1. Ausgangslage

- Der Service existiert bereits im Katalog (hier: „Linux VM").
- Die Option soll im Formular **und** im Wizard erscheinen.
- Sie soll pflichtig sein und eine Vorbelegung haben.

Ergebnis am Ende: ein neues Auswahlfeld in der Gruppe „Softwaremanagement", das bei
ungültiger Eingabe abgelehnt wird.

## 2. Schritt 1 — Test zuerst

TDD ist im Projekt verbindlich (`.claude/rules/testing.md`). Der Test kommt vor der Änderung
und muss zuerst **rot** sein.

Datei `tests/unit/test_catalog_service.py` (oder eine neue Datei im selben Verzeichnis):

```python
from apps.catalog.services import SEED_TEMPLATES


def test_linux_vm_hat_monitoring_profil():
    linux = [t for t in SEED_TEMPLATES if t["name"] == "Linux VM"][0]
    keys = [p["key"] for p in linux["parameters"]]
    assert "monitoring_profile" in keys
```

Ausführen:

```
venv/bin/python -m pytest tests/unit/test_catalog_service.py -q
```

Der Test muss fehlschlagen. Tut er das nicht, prüft er nicht das, was sein Name sagt.

## 3. Schritt 2 — Parameter im Schema ergänzen

In `cmp/apps/catalog/services.py`. Ist die Option für **alle** VM-Vorlagen gedacht, gehört sie
in die Liste `SHARED_PARAMS` (ab Zeile 15); ist sie nur für eine Vorlage gedacht, in deren
eigene Parameterliste innerhalb von `SEED_TEMPLATES` (ab Zeile 333).

```python
{
    "key": "monitoring_profile",
    "label": "Monitoring-Profil",
    "type": "enum",
    "required": True,
    "default": "standard",
    "tofu_variable_name": "monitoring_profile",
    "display_order": 72,
    "group": "Softwaremanagement",
    "description": "Umfang der Ueberwachung",
    "constraints": {"options": [
        {"value": "basis", "label": "Basis — nur Verfuegbarkeit", "enabled": True},
        {"value": "standard", "label": "Standard — Verfuegbarkeit und Last", "enabled": True},
        {"value": "erweitert", "label": "Erweitert — inkl. Dienste", "enabled": False},
    ]},
    "depends_on": [],
    "affects_options_of": [],
}
```

Vier Entscheidungen, die hier fallen:

- **`group`**: Ein bestehender Gruppenname ordnet das Feld einem vorhandenen Wizard-Schritt zu.
  Ein neuer Name erzeugt einen zusätzlichen Schritt (siehe A.1, Abschnitt 5).
- **`display_order`**: bestimmt die Position. `72` reiht hinter `patch_wave` (71) ein.
- **`default`**, nicht `default_value` — siehe A.2, Abschnitt 6.
- **`enabled: False`** hält eine Option im Schema, blendet sie aber aus. Besser als Löschen,
  weil bestehende Bestellungen den Wert weiter enthalten dürfen.

## 4. Schritt 3 — Test grün, dann Gesamtlauf

```
venv/bin/python -m pytest tests/unit/test_catalog_service.py -q
venv/bin/python -m pytest -q
```

Der zweite Lauf ist Pflicht: Ein Pflichtfeld mehr kann Tests brechen, die Bestellungen mit
vollständigen Parametern aufbauen.

## 5. Schritt 4 — In die Datenbank bringen

**Hier ist die häufigste Stolperfalle.** `CatalogService.seed_templates()`
(`cmp/apps/catalog/services.py:411`) legt Vorlagen mit `get_or_create(name=…)` an. Existiert
die Vorlage bereits, bleibt sie **unverändert** — das neue Feld erscheint nicht. `seed` erneut
laufen zu lassen genügt also nicht.

Drei Wege, je nach Umgebung:

| Umgebung | Vorgehen |
|---|---|
| Entwicklung | Datenbank neu aufsetzen und `manage.py seed` laufen lassen |
| Test/Produktion mit Daten | Vorlage im Django-Admin öffnen und das JSON-Feld `parameters` ergänzen |
| Wiederholbar | Eigenen Management-Befehl schreiben, der bestehende Vorlagen aktualisiert |

Ein Migrationsschritt ist **nicht** nötig: `parameters` ist ein JSON-Feld, das Schema der
Tabelle ändert sich nicht.

## 6. Schritt 5 — Probe: so siehst du, dass es geklappt hat

Nachgemessen am 2026-07-22 gegen die echten Formular- und Validierungsklassen — genau diese
Ausgaben sind zu erwarten:

Im Formular (`FullOrderForm`):

```
Label: Monitoring-Profil
Pflicht: True
Vorbelegung: 'standard'
Auswahl: [('', 'Bitte wählen...'),
          ('basis', 'Basis — nur Verfuegbarkeit'),
          ('standard', 'Standard — Verfuegbarkeit und Last')]
```

Die als `enabled: False` markierte Option „erweitert" fehlt in der Auswahl — richtig so.

Im Validator (`TemplateValidator.validate_parameters`):

```
gueltig  : []
ungueltig: [{'key': 'monitoring_profile', 'message': "Value must be one of: ['basis', 'standard']"}]
fehlt    : [{'key': 'monitoring_profile', 'message': "Required parameter 'monitoring_profile' is missing."}]
gesperrt : [{'key': 'monitoring_profile', 'message': "Value must be one of: ['basis', 'standard']"}]
```

Im Wizard (`OrderCreateView._get_steps`):

```
Wizard-Schritte: ['Kontext', 'Netzwerk', 'Platzierung', 'Betriebssystem', 'Vm Sizing',
                  'Datenspeicher', 'Server Informationen', 'Softwaremanagement', 'Backup',
                  'Zusammenfassung']
Parameter im Schritt Softwaremanagement: ['maintenance_window', 'patch_wave', 'monitoring_profile']
```

Kein neuer Schritt, das Feld sitzt an dritter Stelle im bestehenden Schritt — wie beabsichtigt.

Zuletzt im Browser prüfen, **beide** Bestellwege:

- `/orders/create/<template_pk>/form/` — einseitiges Formular
- `/orders/create/<template_pk>/` — Wizard

## 7. Checkliste

- [ ] Test geschrieben und **rot gesehen**
- [ ] Parameter im Schema ergänzt (`SHARED_PARAMS` oder vorlagenspezifisch)
- [ ] `group` und `display_order` bewusst gesetzt
- [ ] `default` statt `default_value`
- [ ] Test grün, Gesamtlauf grün
- [ ] Vorlage in der Datenbank aktualisiert (nicht nur `seed`)
- [ ] Formular **und** Wizard im Browser geprüft

## 8. Zusammenfassung

Eine neue Bestelloption ist ein JSON-Objekt in einer Liste. Migration braucht es keine, wohl
aber einen Weg, die bereits vorhandene Vorlage in der Datenbank zu aktualisieren — `seed`
allein tut das nicht. Für einen komplett neuen Service weiter mit A.4.

> Quelle: `cmp/apps/catalog/services.py:15,333,411`, `cmp/apps/orders/forms.py:182`, `cmp/apps/orders/views.py:90`, `cmp/core/domain/validators.py:15`, `.claude/rules/testing.md`; Ausgaben aus einer Probe gegen die echten Klassen — am Code geprüft 2026-07-22
