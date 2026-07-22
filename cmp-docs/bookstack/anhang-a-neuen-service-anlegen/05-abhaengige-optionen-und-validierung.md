# A.5 Abhängige Optionen und Validierung

Wenn eine Auswahl eine andere beeinflusst — „T-Shirt-Größe M setzt 4 CPU und 8 GB RAM" oder
„das Feld Loadbalancing-Subnetz nur für Web- und App-Server". Diese Seite sagt, was davon
heute wirkt und was nur im Schema steht.

## 1. Ziel des Kapitels

Das Schema kennt zwei Mechanismen für Abhängigkeiten. Sie sehen ähnlich aus, verhalten sich
aber grundverschieden. Wer das verwechselt, baut eine Regel, die nie greift.

| Schlüssel | Gedacht für | Wirkt heute |
|---|---|---|
| `affects_options_of` + `metadata` | Zielfelder automatisch vorbelegen | ja, im einseitigen Formular |
| `depends_on` | Feld ein-/ausblenden | **nein** |

## 2. Vorbelegung über `affects_options_of`

Ein Parameter nennt die Felder, die er beeinflusst; jede seiner Optionen liefert die Werte
dafür in `metadata` mit. Beispiel aus der VM-Vorlage
(`cmp/apps/catalog/services.py:166`, gekürzt):

```json
{
  "key": "tshirt_size",
  "type": "enum",
  "affects_options_of": ["cpu_cores", "ram_gb", "os_disk_gb"],
  "constraints": {"options": [
    {"value": "m", "label": "M — 4 CPU, 8 GB RAM, 80 GB Disk", "enabled": true,
     "metadata": {"cpu_cores": 4, "ram_gb": 8, "os_disk_gb": 80}}
  ]}
}
```

Wählt der Besteller „M", werden die drei Zielfelder gefüllt. Umgesetzt ist das in JavaScript
direkt in der Vorlage `cmp/templates/orders/form_view.html:91-152`:

1. Das Parameterschema wird per `json_script` in die Seite geschrieben
   (`cmp/templates/orders/form_view.html:89`).
2. Aus allen Parametern mit `affects_options_of` entsteht eine Zuordnung Quelle → Ziele.
3. Bei jeder Änderung der Quelle wird die `metadata` der gewählten Option gelesen und in die
   Zielfelder geschrieben — je nach Feldtyp als Auswahlwert, Zahl, Text oder Häkchen.

Die Werte werden **gesetzt, nicht gesperrt**: Der Besteller kann sie danach überschreiben.
Genau das ist bei „T-Shirt-Größe" gewollt (`custom` bleibt möglich).

**Wichtige Einschränkungen, geprüft am 2026-07-22:**

- Der Mechanismus greift **nur im einseitigen Formular**. Die Wizard-Vorlagen unter
  `cmp/templates/orders/wizard/` enthalten kein entsprechendes Skript — dort findet keine
  Vorbelegung statt.
- Er greift nur für `type: "enum"` (der Code prüft das ausdrücklich,
  `cmp/templates/orders/form_view.html:112`). Bei `type: "choice"` passiert nichts.
- Er läuft im Browser. Ohne JavaScript bleibt die Vorbelegung aus — ein Grund mehr, keine
  fachliche Regel allein darauf zu stützen.

## 3. `depends_on` — im Schema vorhanden, ohne Wirkung

Zwei ausgelieferte Parameter tragen eine Sichtbarkeitsregel:

```json
"depends_on": [
  {"parameter_key": "system_type", "operator": "in", "value": ["web", "app"], "effect": "visible"}
]
```

(`lb_subnet`, `cmp/apps/catalog/services.py:82`; `site_replication`, `cmp/apps/catalog/services.py:311`.)

**Geprüft:** Außerhalb der Schema-Definition kommt `depends_on` im gesamten Anwendungscode
nicht vor — weder in Views, Formularen, Vorlagen noch in JavaScript. Die Felder werden also
immer angezeigt. Die Regel ist heute Dokumentation der Absicht, keine Funktion.

Wer eine echte Ein-/Ausblendung braucht, muss sie bauen. Bis dahin gilt: **Kein neuer
Parameter sollte sich darauf verlassen.** Ein Feld, das nur manchmal sinnvoll ist, wird
stattdessen als optional (`required: false`) geführt und im `description`-Text erklärt.

## 4. Was der Validator wirklich prüft

`TemplateValidator.validate_parameters` (`cmp/core/domain/validators.py:15`) ist die einzige
serverseitige Prüfung. Sie prüft je Parameter:

| Prüfung | Umgesetzt |
|---|---|
| Pflichtfeld vorhanden | ja |
| Datentyp passend (`integer`, `string`, `boolean`, `float`) | ja |
| Wert in der Auswahlliste (`enum` über `constraints.options`, nur `enabled: true`) | ja |
| Wert in der Auswahlliste (`choice` über `options`) | ja |
| `min`, `max`, `step`, `pattern`, `min_length`, `max_length` | **nein** |
| Abhängigkeiten zwischen Parametern (`depends_on`, `metadata`) | **nein** |

Beispielausgaben, nachgemessen am 2026-07-22:

```
gueltig  : []
ungueltig: [{'key': 'monitoring_profile', 'message': "Value must be one of: ['basis', 'standard']"}]
fehlt    : [{'key': 'monitoring_profile', 'message': "Required parameter 'monitoring_profile' is missing."}]
```

Eine leere Liste bedeutet „gültig"; jeder Fehler ist ein Objekt mit `key` und `message`.

## 5. Was das für die Absicherung bedeutet

Die Einschränkungen aus `metadata` — etwa `allowed_system_types` bei `ad_tier` oder
`security_areas` bei `network_vlan` — sind **Komfort im Browser, keine Kontrolle**. Ein
abgeschickter Datensatz mit einer fachlich unsinnigen, aber formal erlaubten Kombination
(gültiger Einzelwert, unpassende Kombination) wird heute serverseitig angenommen.

Für neue Optionen daraus zwei Regeln:

1. **Jede Regel, die wirklich gelten muss, gehört auf den Server** — in den Validator oder in
   die Formularklasse. JavaScript ist Bedienkomfort.
2. **Was nur im Browser passiert, wird im Schema als solches kenntlich gemacht**
   (`description`), damit spätere Leser die Lücke nicht für eine Zusicherung halten.

## 6. Zusammenfassung

- `affects_options_of` + `metadata` belegt Zielfelder vor — nur im einseitigen Formular, nur
  bei `enum`, nur im Browser.
- `depends_on` steht im Schema, wird aber nirgends ausgewertet.
- Der Validator prüft Pflicht, Typ und Auswahlliste — sonst nichts.
- Fachliche Regeln, die halten müssen, serverseitig umsetzen.

> Quelle: `cmp/apps/catalog/services.py:82,166,311`, `cmp/templates/orders/form_view.html:89,91-152`, `cmp/core/domain/validators.py:3,15`, `cmp/templates/orders/wizard/` (kein Skript) — am Code geprüft 2026-07-22
