# C — Einen neuen Service anlegen

> **In diesem Anhang:** Der Katalog des CMP wächst nicht durch neue Views oder
> neue Django-Apps, sondern durch neue **Datensätze**. Dieser Anhang zeigt dir
> das Rezept dafür — und ebenso ehrlich, wo dieses Rezept an seine Grenze
> stößt: sobald ein Service etwas *tun* soll, statt nur bestellbar zu sein.
>
> **Das lernst du:**
> - Wie ein neuer bestellbarer Service allein durch ein `ServiceTemplate`
>   entsteht — ohne neue View, ohne Migration
> - Wie ein Parameter-Schema aufgebaut ist, kompakt an einem Beispiel
> - Wo die eigentliche **Ausführung** eines Services passiert — und warum der
>   Katalog dafür allein nicht reicht
> - Was heute an dieser Naht schon da ist (`GitLabStubClient`) und was noch
>   fehlt
> - Wie du das Ganze im TDD-Zyklus angehst
>
> **Voraussetzung:** [03 — Die Fachdomäne](03-fachdomaene.md) und
> [07 — Async & Provisioning](07-async-und-provisioning.md).

---

## Teil 1: Der datengetriebene Teil (Katalog)

Die wichtigste Erkenntnis dieses Anhangs zuerst:

💡 **Merke:** Ein neuer bestellbarer Service ist zuerst **Daten, kein Code**.
Es gibt keine `AdPasswordResetService`-Klasse und kein eigenes Modul dafür —
es gibt einen einzigen Datensatz vom Typ `ServiceTemplate`
(`cmp/apps/catalog/models.py`).

```
ServiceTemplate
├── name          "AD-Passwort zurücksetzen"
├── category      "network"
├── description   "Setzt das Active-Directory-Passwort eines Benutzers zurück."
├── is_active     True
└── parameters    [ {…}, {…} ]   ← die Bestelloptionen, als JSON-Liste
```

Bestellen, Genehmigen und die Formular-Oberfläche funktionieren dadurch
**ohne neue View und ohne Migration** — der Katalog liest die Vorlage zur
Laufzeit aus dem JSON-Feld `parameters`. Ein Parameter mehr in der Liste ist
ein Formularfeld mehr, ein Wizard-Schritt mehr bei neuem `group`-Wert — nicht
mehr und nicht weniger.

### Beispiel-Schema: „AD-Passwort-Reset"

Als roter Faden für diesen Anhang nehmen wir einen Service, der (anders als
die vorhandenen VM-Vorlagen) keine Maschine baut, sondern eine einzelne
AD-Aktion auslöst:

```python
{
    "name": "AD-Passwort zurücksetzen",
    "category": "network",
    "description": "Setzt das Active-Directory-Passwort eines Benutzers zurück.",
    "parameters": [
        {
            "key": "target_username", "label": "Zielbenutzer", "type": "string",
            "required": True, "display_order": 10, "group": "AD-Aktion",
            "description": "Der AD-Benutzername, dessen Passwort zurückgesetzt wird.",
            "constraints": {"min_length": 3, "max_length": 64},
            "depends_on": [], "affects_options_of": [],
        },
        {
            "key": "domain", "label": "Domäne", "type": "enum",
            "required": True, "default": "corp.local",
            "display_order": 11, "group": "AD-Aktion",
            "constraints": {"options": [
                {"value": "corp.local", "label": "corp.local", "enabled": True},
                {"value": "test.local", "label": "test.local", "enabled": True},
            ]},
            "depends_on": [], "affects_options_of": [],
        },
    ],
}
```

Zwei Details, die aus dem Schema-Kapitel der Referenzdoku wichtig sind:

- **`type` kennt feste Werte** — `string`, `integer`, `float`, `boolean`,
  `enum` (Auswahlliste über `constraints.options`). Für neue Auswahllisten
  gilt: immer `enum`, nicht das ältere `choice`.
- **Vorbelegung heißt `default`**, nicht `default_value` — nur `default`
  wird von den Formularklassen tatsächlich gelesen
  (`cmp/apps/orders/forms.py`).

> 🔍 Die vollständige Feldreferenz (`group`, `display_order`, `constraints`,
> `depends_on`, `tofu_variable_name` — inklusive der Fälle, in denen ein
> Schlüssel im Schema steht, aber **nicht** ausgewertet wird) findest du in
> der ausführlichen Referenzdokumentation unter
> [`cmp-docs/bookstack/anhang-a-neuen-service-anlegen/`](../../cmp-docs/bookstack/anhang-a-neuen-service-anlegen/).
> Dieser Guide-Anhang zeigt dir das Prinzip, die Bookstack-Seiten das
> vollständige Kochbuch mit jeder Fußangel.

### Wie die Vorlage in die Datenbank kommt

Zwei Wege, beide am Code geprüft:

1. **Seed** — `CatalogService.seed_templates()` legt die Einträge aus der
   Liste `SEED_TEMPLATES` (`cmp/apps/catalog/services.py`) per
   `get_or_create(name=...)` an. Heute enthält diese Liste die Vorlagen
   „Linux VM" und „Windows VM" — unser AD-Beispiel ist (noch) nicht darin,
   es dient hier nur als Anschauung.
2. **Django Admin** — `ServiceTemplate` ist im Admin registriert
   (`cmp/apps/catalog/admin.py`). Da `parameters` ein JSON-Feld ist, lässt
   sich eine Vorlage dort direkt anlegen oder bearbeiten, ganz ohne Seed-Lauf.

⚠️ **Achtung:** `get_or_create(name=...)` **aktualisiert keine bestehende**
Vorlage. Existiert der Name schon, ändert ein erneuter Seed-Lauf nichts an
den Parametern — für Änderungen an einer bereits vorhandenen Vorlage bleibt
nur der Admin oder eine neu aufgesetzte Entwicklungsdatenbank.

---

## Teil 2: Der Ausführungs-Teil (die Naht zum echten System)

Ein Katalog-Eintrag reicht, solange „bestellen" die ganze Geschichte ist.
Sobald ein Service etwas **tut** — eine VM bauen, oder eben ein
AD-Passwort zurücksetzen —, braucht es mehr: die eigentliche Aktion passiert
in der **Provisioning-Schicht**, nicht im Katalog.

Zentrale Stelle dafür ist `ProvisioningService.dispatch_order()`
(`cmp/apps/provisioning/services.py`):

```python
@staticmethod
def dispatch_order(order_id):
    """Dispatch all items of an approved order to the provisioning pipeline."""
    order = OrderService.get_order(order_id)
    if order.status != OrderStatus.APPROVED:
        raise ConflictError(f"Cannot dispatch order in status '{order.status}'.")
    transition(order, OrderStatus.PROVISIONING, None)

    client = GitLabStubClient()
    for item in order.items.select_related("template").all():
        result = client.trigger_pipeline(item.template.name, item.parameters)
        DispatchLog.objects.create(
            order_item=item,
            pipeline_id=result["pipeline_id"],
            status="running",
            payload={"template": item.template.name, "parameters": item.parameters},
        )
```

Das ist bereits **die Naht**: Ein Client bekommt Vorlagenname und Parameter,
liefert eine Kennung und einen Status zurück, und ein `DispatchLog` merkt sich
das Ergebnis. Alles danach — `complete_dispatch()`, der Order-Status, die
Benachrichtigung, das Anlegen des Abos — kennt nur noch `DispatchLog.status`.
Es ist dem Rest des Systems egal, **welcher** Client dahintersteckt.

### Was es heute wirklich gibt: `GitLabStubClient`

```python
class GitLabStubClient:
    """In-memory stub that simulates GitLab CI pipeline triggers."""

    def trigger_pipeline(self, template_name, parameters):
        pipeline_id = uuid.uuid4().hex[:12]
        self._pipelines[pipeline_id] = "running"
        return {"pipeline_id": pipeline_id, "status": "running"}

    def get_pipeline_status(self, pipeline_id):
        return self._pipelines.get(pipeline_id)

    def complete_pipeline(self, pipeline_id, success=True):
        if pipeline_id in self._pipelines:
            self._pipelines[pipeline_id] = "success" if success else "failed"
```

`GitLabStubClient` simuliert eine GitLab-CI-Pipeline komplett in-memory — es
gibt keine echte Anbindung, kein Netzwerk-Aufruf, kein Polling. Genau dieselbe
Naht (`trigger_pipeline` → `DispatchLog` → `complete_dispatch`) ist auch der
Erweiterungspunkt für einen echten Client.

> ⚠️ **Achtung:** `dispatch_order()` erzeugt **einen einzigen**
> `GitLabStubClient` und ruft ihn für **jede** Order-Position auf — unabhängig
> davon, welche Vorlage dahintersteckt. Es gibt heute **keine** Unterscheidung
> nach `category` oder `name`. Würdest du unsere AD-Beispielvorlage aus Teil 1
> ungeändert bestellen, liefe sie ebenfalls durch den GitLab-Stub: Er würde
> eine erfundene `pipeline_id` zurückgeben, der Order-Status würde brav auf
> `done` laufen — aber in Active Directory würde **nichts** passieren. Ein
> echter Client (AD, oder ein zweites echtes GitLab-Backend) ist heute **nicht
> gebaut**. Das ist der geplante Erweiterungspunkt: Stub → echt.

### Skizze: wie ein `AdClient` aussehen könnte

Rein zur Illustration — dieser Code existiert **nicht** im Projekt, er zeigt
nur, wie ein zweiter Client dieselbe Naht bedienen würde:

```python
# ILLUSTRATION — kein vorhandener Code, nur zur Veranschaulichung der Naht
class AdStubClient:
    """So könnte ein AD-Client aussehen — analog zu GitLabStubClient."""

    def __init__(self):
        self._jobs = {}

    def trigger_password_reset(self, target_username, domain):
        job_id = uuid.uuid4().hex[:12]
        self._jobs[job_id] = "running"
        return {"pipeline_id": job_id, "status": "running"}

    def get_reset_status(self, job_id):
        return self._jobs.get(job_id)
```

Damit das tatsächlich greift, müsste `dispatch_order()` außerdem lernen,
**welchen** Client es für welches Item nimmt — heute instanziiert es
bedingungslos `GitLabStubClient()`. Eine denkbare (ebenfalls nur skizzierte)
Erweiterung:

```python
# ILLUSTRATION — zeigt nur die Idee, kein vorhandener Code
CLIENTS_BY_CATEGORY = {
    "network": AdStubClient(),
}

for item in order.items.select_related("template").all():
    client = CLIENTS_BY_CATEGORY.get(item.template.category, GitLabStubClient())
    result = client.trigger_pipeline(item.template.name, item.parameters)
    ...
```

Der Rest der Kette — `DispatchLog`, `complete_dispatch()`, der
Order-Zustandsautomat aus [Kapitel 05](05-bestell-lebenszyklus.md), die
Benachrichtigung, das Abo — bliebe dabei **komplett unverändert**. Genau das
ist der Sinn der Kapselung: Die Ausführungslogik ist austauschbar, ohne dass
Katalog, Genehmigung oder der Rest von Provisioning davon wissen.

---

## Teil 3: So gehst du vor (TDD)

TDD ist im Projekt Pflicht (`.claude/rules/testing.md`), auch für einen neuen
Katalog-Eintrag. Der Ablauf in Kurzform:

1. **ROT** — Test zuerst. Für einen neuen Service z. B. in
   `tests/unit/test_catalog_service.py`:

   ```python
   from apps.catalog.services import SEED_TEMPLATES


   def test_ad_passwort_reset_vorlage_existiert():
       namen = [t["name"] for t in SEED_TEMPLATES]
       assert "AD-Passwort zurücksetzen" in namen
   ```

   ```bash
   python -m pytest tests/unit/test_catalog_service.py -k ad_passwort_reset
   ```

   Der Test muss zuerst **fehlschlagen** — siehe
   [Kapitel 11](11-dein-erster-beitrag.md) zum Grundmuster ROT → GRÜN →
   REFACTOR.

2. **GRÜN** — minimal implementieren. Für eine neue Bestelloption genügt der
   Eintrag im Schema (Teil 1). Für eine echte Ausführung kommt der neue
   Client-Code dazu, so schlank wie das Stub-Vorbild.

3. **Ganze Suite** laufen lassen, nicht nur den neuen Test:

   ```bash
   python -m pytest
   ```

   Ein neues `required: true`-Feld kann bestehende Tests brechen, die
   Bestellungen mit vollständigen Parametern aufbauen.

4. **Linter** über die geänderten Dateien:

   ```bash
   ruff check cmp/apps/catalog/services.py
   ```

5. **In die Datenbank bringen** — je nach Umgebung per Seed
   (`python cmp/manage.py seed`, nur für neue Namen) oder per Django-Admin
   (für Änderungen an bestehenden Vorlagen, siehe Teil 1).

6. Für Code-Konventionen, Commit-Stil und die Frage „wo gehört mein Code
   überhaupt hin" gilt weiterhin [Kapitel 10](10-so-arbeiten-wir.md).

🔍 Ein komplett durchgespieltes Beispiel dieses Zyklus — inklusive echtem
roten Testlauf, minimaler Implementierung und Commit — findest du in
[11 — Dein erster Beitrag](11-dein-erster-beitrag.md).

---

## 🔍 Im Code nachsehen

| Was | Wo |
|-----|-----|
| Das Modell hinter jedem Service | `cmp/apps/catalog/models.py` (`ServiceTemplate`, `TemplateCategory`) |
| Die Schema-Definitionen der ausgelieferten Vorlagen | `cmp/apps/catalog/services.py` (`SHARED_PARAMS`, `SEED_TEMPLATES`) |
| Die Validierung der Parameterwerte | `cmp/core/domain/validators.py` (`TemplateValidator.validate_parameters`) |
| Admin-Pflege der Vorlagen | `cmp/apps/catalog/admin.py` |
| Die Naht zur Ausführung | `cmp/apps/provisioning/services.py` (`ProvisioningService.dispatch_order`, `complete_dispatch`) |
| Der heute einzige Client | `cmp/apps/provisioning/clients.py` (`GitLabStubClient`) |

Öffne `dispatch_order()` und such nach einer Stelle, die nach `category`
oder `name` unterscheidet — es gibt keine. Genau das ist der Befund aus
Teil 2: ein Client für alle Vorlagen, heute.

---

## Selbstcheck

Bevor du weiterliest, kannst du diese Fragen beantworten?

1. Du willst der Linux-VM ein neues Auswahlfeld hinzufügen. Brauchst du dafür
   eine Migration? Warum (nicht)?
2. Was passiert **heute tatsächlich**, wenn du eine AD-Passwort-Reset-Vorlage
   anlegst und bestellst, ohne die Provisioning-Schicht anzufassen?
3. Welche Methode bleibt garantiert unverändert, egal welchen Client du für
   `dispatch_order()` einsetzt?

<details>
<summary>Antworten anzeigen</summary>

1. Nein. `parameters` ist ein JSON-Feld — ein neuer Eintrag in der Liste
   ändert das Datenbankschema nicht. Eine Migration bräuchtest du nur, wenn
   du das `ServiceTemplate`-Modell selbst (also seine Felder) änderst.
2. Sie durchläuft `dispatch_order()`, bekommt aber denselben
   `GitLabStubClient` wie jede andere Vorlage. Der Stub erfindet eine
   `pipeline_id`, die Order läuft brav auf `done` — aber es passiert nichts
   in Active Directory. Ohne einen echten AD-Client bleibt es bei der
   Simulation.
3. `complete_dispatch()` — sie kennt nur `DispatchLog.status` und weiß
   nichts vom konkreten Client, der diesen Status gesetzt hat.

</details>

---

⟵ [B — Spickzettel](B-spickzettel.md) · [📖 Übersicht](README.md)
