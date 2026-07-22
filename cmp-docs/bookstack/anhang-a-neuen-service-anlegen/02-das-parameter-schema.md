# A.2 Das Parameter-Schema

Feldreferenz für einen einzelnen Eintrag in `ServiceTemplate.parameters`. Jeder Schlüssel wird
mit Bedeutung, erlaubten Werten und der Stelle beschrieben, die ihn tatsächlich auswertet.

## 1. Ziel des Kapitels

Wer eine Bestelloption anlegt, schreibt genau ein solches Objekt. Diese Seite sagt, welche
Schlüssel es gibt, welche wirken und welche heute nur mitgeführt werden.

## 2. Ein vollständiges Beispiel

Aus der Definition der Linux-VM (`cmp/apps/catalog/services.py:106`, gekürzt):

```json
{
  "key": "network_layer",
  "label": "Layer",
  "type": "enum",
  "required": true,
  "tofu_variable_name": "network_layer",
  "display_order": 18,
  "group": "Netzwerk",
  "description": "Verfuegbare VLANs abhaengig von Sicherheitsbereich und Layer",
  "constraints": {
    "options": [
      {"value": "frontend", "label": "Frontend", "enabled": true,
       "metadata": {"allowed_system_types": ["app", "web"]}},
      {"value": "backend", "label": "Backend", "enabled": true,
       "metadata": {"allowed_system_types": ["db", "dc", "fp", "app", "web"]}}
    ]
  },
  "depends_on": [],
  "affects_options_of": ["network_vlan"]
}
```

## 3. Die Schlüssel im Einzelnen

| Schlüssel | Pflicht | Bedeutung | Ausgewertet in |
|---|---|---|---|
| `key` | ja | Technischer Name, wird Formularfeldname und Schlüssel in `order_items.parameters` | `cmp/apps/orders/forms.py:16,109,222` |
| `label` | nein | Beschriftung im Formular; fehlt sie, wird `key` angezeigt | ebenda |
| `type` | ja | Datentyp, siehe Abschnitt 4 | `cmp/core/domain/validators.py:15` |
| `required` | nein (Vorgabe `false`) | Pflichtfeld | Formular + Validator |
| `description` | nein | Hilfetext | Vorlagen |
| `group` | nein (Vorgabe „Allgemein") | Gruppiert Felder; **erzeugt im Wizard einen eigenen Schritt** | `cmp/apps/orders/views.py:90` |
| `display_order` | nein (Vorgabe 999) | Sortierung innerhalb des Formulars und der Gruppen | `cmp/apps/orders/views.py:112`, `cmp/apps/orders/forms.py:221` |
| `constraints` | je nach Typ | Wertebereich bzw. Auswahlliste, siehe Abschnitt 5 | Validator, Formular |
| `depends_on` | nein | Abhängigkeit von einem anderen Parameter, siehe A.5 | **heute nirgends** |
| `affects_options_of` | nein | Zielfelder für die automatische Vorbelegung, siehe A.5 | `cmp/templates/orders/form_view.html:104` |
| `tofu_variable_name` | nein | Name der späteren Infrastruktur-Variablen | heute nicht ausgewertet |

## 4. Erlaubte Werte für `type`

| `type` | Formularfeld | Prüfung im Validator |
|---|---|---|
| `string` | Textfeld | `isinstance(v, str)` |
| `integer` | Zahlenfeld | ganze Zahl, `bool` ausgeschlossen |
| `float` | Zahlenfeld | Zahl, `bool` ausgeschlossen |
| `boolean` | Kontrollkästchen | `isinstance(v, bool)` |
| `enum` | Auswahlliste aus `constraints.options` | Wert muss in den aktivierten Optionen vorkommen |
| `choice` | Auswahlliste aus `options` (flache Liste) | Wert muss in `options` vorkommen |

Die Typprüfungen stehen in `TYPE_CHECKS` (`cmp/core/domain/validators.py:3`), die Auswahl-Logik
in `TemplateValidator.validate_parameters` (`cmp/core/domain/validators.py:15`).

**`enum` oder `choice`?** Beide erzeugen eine Auswahlliste, unterscheiden sich aber im Aufbau:

```json
{"type": "enum",   "constraints": {"options": [{"value": "s", "label": "Klein", "enabled": true}]}}
{"type": "choice", "options": ["s", "m", "l"]}
```

`enum` erlaubt eigene Beschriftungen, das Abschalten einzelner Optionen über `enabled` und
`metadata` für die Vorbelegung. **Für neue Optionen immer `enum` verwenden** — `choice` ist die
einfachere Altform und wird von der Vorbelegung in A.5 nicht unterstützt.

## 5. Der Block `constraints`

Der Inhalt hängt vom Typ ab. Real verwendet werden:

| Schlüssel | Bei Typ | Beispiel | Wirkung |
|---|---|---|---|
| `options` | `enum` | siehe oben | Auswahlliste; nur Einträge mit `enabled: true` erscheinen |
| `min`, `max`, `step`, `unit` | `integer`, `float` | `{"min": 1, "max": 64, "step": 1, "unit": "Kerne"}` | **nur beschreibend** — siehe Warnung unten |
| `pattern` | `string` | `"^[0-9]{1,3}\\..."` | **nur beschreibend** |
| `min_length`, `max_length` | `string` | `{"min_length": 5, "max_length": 500}` | **nur beschreibend** |

**Wichtig und geprüft:** `TemplateValidator.validate_parameters` wertet aus `constraints`
ausschließlich `options` aus. `min`, `max`, `step`, `pattern`, `min_length` und `max_length`
werden vom Validator **nicht** geprüft (`cmp/core/domain/validators.py:15-73`). Wer eine
Zahlenschranke wirklich erzwingen will, muss sie zusätzlich im Formularfeld hinterlegen. Die
Angaben im Schema sind trotzdem sinnvoll: Sie dokumentieren die Absicht und sind der Anker
für eine spätere Nachrüstung.

Ein Eintrag in `constraints.options`:

| Schlüssel | Bedeutung |
|---|---|
| `value` | gespeicherter Wert |
| `label` | angezeigter Text |
| `enabled` | `false` blendet die Option aus, ohne sie zu löschen |
| `metadata` | Zusatzdaten für die automatische Vorbelegung (siehe A.5) |

## 6. Vorbelegung: `default`, nicht `default_value`

Das Schema kennt zwei ähnliche Schreibweisen — und nur eine wirkt.

Die Formularklassen lesen `param["default"]`
(`cmp/apps/orders/forms.py:61,113,226`). Die mitgelieferten Vorlagen schreiben aber
`default_value` (`cmp/apps/catalog/services.py:169,307,315`).

Nachgemessen am 2026-07-22 mit einer Wegwerf-Probe gegen die echten Formularklassen:

```
OrderParameterForm  default_value -> None      FullOrderForm  default_value -> None
OrderParameterForm  default       -> 9         FullOrderForm  default       -> 9
tshirt_size initial im Formular: None
backup_enabled initial im Formular: None
```

**Folge:** Die Vorbelegungen der ausgelieferten Vorlagen (`tshirt_size` auf „custom",
`backup_enabled` und `site_replication` auf `false`) erscheinen heute nicht im Formular.

**Für neue Parameter gilt daher: `default` verwenden.** Die Vereinheitlichung des Schemas ist
offen und gehört als eigenes Arbeitspaket erfasst, nicht nebenbei erledigt.

## 7. Zusammenfassung

- Ein Parameter ist ein JSON-Objekt mit `key`, `label`, `type` und optional `constraints`.
- `group` steuert die Wizard-Schritte, `display_order` die Reihenfolge.
- Nur `constraints.options` wird geprüft; Zahlen- und Textschranken sind heute beschreibend.
- Vorbelegung heißt `default`. `default_value` wirkt nicht.
- Neue Auswahllisten immer als `enum` anlegen.

> Quelle: `cmp/apps/catalog/services.py:15,169,307,315`, `cmp/apps/orders/forms.py:6,61,102,113,182,226`, `cmp/apps/orders/views.py:90,112`, `cmp/core/domain/validators.py:3,15` — am Code geprüft 2026-07-22
