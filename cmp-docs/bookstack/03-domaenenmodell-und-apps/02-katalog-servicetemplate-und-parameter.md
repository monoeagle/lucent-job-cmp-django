# Katalog: ServiceTemplate und Parameter

`ServiceTemplate` ist der Katalogeintrag, aus dem im Bestell-Wizard ein Formular
entsteht. Dieses Kapitel dokumentiert das Modell und das reale Schema seines
`parameters`-JSON-Felds — Details zum Anlegen neuer Parameter stehen in Anhang A.

## 1. Ziel des Kapitels

Wer ein neues Template oder einen neuen Parameter versteht (oder anlegt), braucht
zwei Dinge: die Feldstruktur von `ServiceTemplate` selbst, und das Schema, das im
`parameters`-Feld erwartet wird. Beides steht hier — geprüft an
`cmp/apps/catalog/models.py`, `cmp/apps/catalog/services.py` und
`cmp/core/domain/validators.py`.

## 2. Feldreferenz ServiceTemplate

`cmp/apps/catalog/models.py:14`, Tabelle `service_templates`:

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | `BigAutoField` | Primärschlüssel |
| `name` | `CharField(200)`, unique | Template-Name |
| `category` | `CharField(30)` | Kategorie — Freitext, siehe Abschnitt 3 |
| `description` | `TextField`, blank | Beschreibungstext |
| `parameters` | `JSONField`, default `list` | Parameter-Schema (Liste, siehe Abschnitt 4) |
| `is_active` | `BooleanField`, default `True` | Sichtbar im aktiven Katalog |
| `version` | `PositiveIntegerField`, default `1` | Versionsnummer |
| `created_at` | `DateTimeField`, auto | via `TimeStampedModel` |
| `updated_at` | `DateTimeField`, auto | via `TimeStampedModel` |

`ServiceTemplate` erbt von `TimeStampedModel` (`cmp/core/mixins.py`), daher die
beiden Zeitstempelfelder zusätzlich zu den fachlichen Spalten.

## 3. Kategorien: TextChoices vs. reale Nutzung

`cmp/apps/catalog/models.py:6` definiert `TemplateCategory` als
`models.TextChoices` mit fünf Werten: `compute`, `database`, `container`,
`network`, `storage`. Diese Klasse wird jedoch **nicht** als `choices=` auf dem
Feld `category` selbst gesetzt — das Feld ist ein einfaches `CharField(30)` ohne
DB-seitige Einschränkung. Verwendet wird `TemplateCategory` aktuell nur an einer
Stelle: im Kategorie-Filter des Katalog-Formulars
(`cmp/apps/catalog/forms.py:11`, `TemplateCategory.choices` für die Dropdown-Optionen).

Real befüllt sind Templates ausschließlich mit `category="compute"`
(`cmp/apps/catalog/services.py:336` und `:355`, `SEED_TEMPLATES`: "Linux VM" und
"Windows VM"). Die vier anderen `TemplateCategory`-Werte existieren im Code, aber
kein aktuell erzeugtes Template nutzt sie — Ist-Stand, kein Fehler.

## 4. Das Parameter-Schema

`parameters` ist eine Liste von Parameter-Objekten. Die real verwendete Struktur
stammt aus der Konstante `SHARED_PARAMS` in `cmp/apps/catalog/services.py:15-321`
(24 gemeinsame Parameter für Linux- und Windows-VM-Templates, ergänzt um je einen
`os_template`-Parameter pro OS). Jedes Parameter-Objekt trägt diese Schlüssel:

| Schlüssel | Beispielwert | Bedeutung |
|---|---|---|
| `key` | `"cpu_cores"` | Eindeutiger Parametername, auch Formularfeld-Name |
| `label` | `"CPU Cores"` | Anzeigetext im Formular |
| `type` | `"integer"` | Werttyp — siehe Abschnitt 5 |
| `required` | `true` / `false` | Pflichtfeld |
| `tofu_variable_name` | `"cpu_cores"` | Name der Ziel-Variable für die Provisioning-Pipeline |
| `display_order` | `41` | Sortierung innerhalb der Gruppe |
| `group` | `"VM Sizing"` | Abschnittsüberschrift im Wizard |
| `description` | optional | Hilfetext |
| `constraints` | `{...}` | Typabhängige Zusatzangaben, siehe Abschnitt 5 |
| `default_value` | optional | Vorbelegung |
| `depends_on` | Liste | Sichtbarkeitsregeln, siehe Abschnitt 6 |
| `affects_options_of` | Liste von `key`s | Welche anderen Parameter dieser Wert beeinflusst |

Sieben Gruppen sind real belegt (`group`-Werte, in `display_order` sortiert):
Netzwerk, Platzierung, Betriebssystem (nur `os_template`, template-spezifisch),
VM Sizing, Datenspeicher, Server Informationen, Softwaremanagement, Backup.

## 5. Typen und ihre `constraints`

`cmp/core/domain/validators.py` unterscheidet folgende `type`-Werte:

| `type` | Prüfung in `TemplateValidator` | Typische `constraints` |
|---|---|---|
| `enum` | Wert muss in `constraints.options[].value` mit `enabled: true` vorkommen | `{"options": [{"value", "label", "enabled", "metadata"?}]}` |
| `choice` | Wert muss in `options` (Top-Level, nicht `constraints`) vorkommen | `{"options": [...]}` — im aktuellen Katalog ungenutzt |
| `string` | `isinstance(v, str)` | z. B. `pattern`, `min_length`, `max_length` (nur beschreibend) |
| `integer` | `isinstance(v, int)`, kein `bool` | z. B. `min`, `max`, `step`, `unit` (nur beschreibend) |
| `boolean` | `isinstance(v, bool)` | meist `{}` |
| `float` | `isinstance(v, (int, float))`, kein `bool` | im aktuellen Katalog ungenutzt |

**Ist-Stand, geprüft:** `TemplateValidator.validate_parameters()`
(`cmp/core/domain/validators.py`) prüft nur `required` und den Werttyp bzw. die
`enum`/`choice`-Optionsliste. Zahlen- und Textconstraints wie `min`, `max`,
`pattern`, `min_length`, `max_length` werden **nicht** durchgesetzt — weder vom
Validator noch vom dynamischen Formular (`cmp/apps/orders/forms.py`,
`OrderParameterForm`, das lediglich `type` auf ein Django-Feld ohne
Validatoren abbildet). Sie sind aktuell reine Dokumentationsangaben im JSON.

Alle real seeded Templates nutzen ausschließlich `enum`, `string`, `integer` und
`boolean` — `choice` und `float` sind im Validator implementiert, aber in keinem
Template belegt.

## 6. `depends_on` und `affects_options_of`

Beide Felder werden im Parameter-Objekt mitgeführt, aber **nicht** von
`TemplateValidator` ausgewertet. `depends_on` enthält Regeln der Form
`{"parameter_key", "operator", "value", "effect"}` (z. B. `lb_subnet` ist nur bei
`system_type in [web, app]` sichtbar) — das ist reine Metadaten, die für eine
clientseitige oder wizard-interne Sichtbarkeitssteuerung gedacht sind.
`affects_options_of` listet, welche anderen Parameter durch die Wahl dieses Werts
beeinflusst werden sollen (z. B. `tshirt_size` beeinflusst `cpu_cores`, `ram_gb`,
`os_disk_gb`). Details zur Verdrahtung dieser Abhängigkeiten gehören in Anhang A.5
und werden hier nicht wiederholt.

## 7. Verweis auf das Kochbuch

Wie ein neuer Parameter oder ein neues Template konkret angelegt wird — inklusive
TDD-Reihenfolge und Formular-Probe — beschreibt Anhang A (A.1–A.5). Dieses Kapitel
bleibt bei der Referenz: welche Felder es gibt und wie sie geprüft werden.

## 8. Zusammenfassung

`ServiceTemplate` ist ein schlankes Modell; die eigentliche Komplexität steckt im
`parameters`-JSON. Real genutzt werden vier Werttypen (`enum`, `string`, `integer`,
`boolean`) mit zwölf Schlüsseln je Parameter-Objekt. Der Validator prüft nur
Pflicht und Grundtyp — Zusatz-Constraints und Abhängigkeitsregeln sind Metadaten
ohne serverseitige Durchsetzung. `TemplateCategory` existiert mit fünf Werten,
real belegt ist bislang nur `compute`.

> Quelle: cmp/apps/catalog/models.py, cmp/apps/catalog/services.py, cmp/apps/catalog/forms.py, cmp/apps/orders/forms.py, cmp/core/domain/validators.py — am Code geprüft 2026-07-22
