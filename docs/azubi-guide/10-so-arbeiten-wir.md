# 09 — So arbeiten wir

> **In diesem Kapitel:** Bevor du selbst Code schreibst, lernst du die Spielregeln
> kennen, nach denen im CMP-Projekt gearbeitet wird — TDD, Tests, Code-Konventionen
> und Releases. Diese Regeln sind kein Bürokratie-Ballast, sondern schützen genau
> vor den Fallstricken, die du in [Kapitel 05](05-bestell-lebenszyklus.md) schon
> gesehen hast (z. B. die goldene Regel „nur über `transition()`").
>
> **Das lernst du:**
> - Warum TDD hier Pflicht ist und wie der rot → grün → refactor-Zyklus aussieht
> - Wie das Testverzeichnis aufgebaut ist und welche Werkzeuge zum Einsatz kommen
> - Die wichtigsten Code-Regeln in Kurzform
> - Wie Versionierung und Releases im Projekt funktionieren
>
> **Voraussetzung:** [09 — Setup lokal](09-setup-lokal.md) (dein Projekt sollte
> laufen und `pytest` sollte grün durchlaufen).

---

## TDD ist Pflicht — kein Sonderfall

Im CMP-Projekt gilt: **erst der Test, dann der Code.** Das ist keine Empfehlung,
sondern eine feste Regel. Der Ablauf ist immer derselbe, dreiteilige Zyklus:

1. **Rot** — Du schreibst einen Test für ein Verhalten, das es noch nicht gibt.
   Er schlägt fehl (rot), weil der Code fehlt.
2. **Grün** — Du schreibst *gerade so viel* Code, dass der Test durchläuft.
   Nicht mehr, nicht weniger.
3. **Refactor** — Jetzt, wo der Test grün ist und dich absichert, räumst du auf:
   Namen verbessern, Duplikate entfernen, Struktur klären. Die Tests bleiben
   dabei grün.

💡 **Merke:** Wenn du merkst, dass du Produktivcode schreibst, bevor der
zugehörige Test existiert — stopp. Schreib zuerst den Test.

⚠️ **Achtung:** „Ich schreibe den Test danach noch dazu" ist in der Praxis fast
immer ein Test, der bewusst oder unbewusst an den bereits fertigen Code angepasst
wird. Das prüft nicht das Verhalten, sondern bestätigt nur, was du sowieso schon
getan hast.

---

## Das Testverzeichnis

Alle Tests leben zentral unter `tests/` — nicht verstreut in den einzelnen Apps.
Die Konfiguration dafür steht in `pytest.ini`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
pythonpath = cmp
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

Innerhalb von `tests/` ist nach **Testebene** sortiert:

| Verzeichnis / Datei | Zweck |
|---|---|
| `tests/unit/` | Tests für einzelne Services und Domänenlogik, isoliert von der Datenbank-Session (soweit möglich) — z. B. `test_order_service.py`, `test_transitions.py` |
| `tests/integration/` | Tests, die mehrere Teile zusammen prüfen — Models, Views, DB-Zugriffe — z. B. `test_order_views.py`, `test_order_model.py` |
| `tests/e2e/` | Tests, die einen kompletten Ablauf durchspielen, z. B. den gesamten Bestell-Lebenszyklus aus Kapitel 05 (`test_order_workflow.py`) |
| `tests/factories.py` | Zentrale `factory_boy`-Factories für alle Models (`UserFactory`, `OrderFactory`, `ServiceTemplateFactory`, …) |
| `tests/conftest.py` | Geteilte pytest-Fixtures, u. a. die Datenbank-Anbindung für die Testumgebung |

🔍 **Im Code nachsehen:** Wirf einen Blick in `tests/factories.py` — du siehst dort,
dass z. B. `OrderFactory` eine Bestellung immer mit `status = OrderStatus.DRAFT`
anlegt. Genau die Zustände aus Kapitel 05.

---

## Die Werkzeuge: pytest-django + factory_boy

Zwei Bibliotheken tragen den Großteil der Testarbeit:

- **pytest-django** bindet Django in pytest ein — Fixtures wie `django_db` oder
  der `client` regeln Datenbank-Zugriff und HTTP-Requests in Tests.
- **factory_boy** erzeugt Testdaten, ohne dass du in jedem Test lange
  Objekt-Konstruktionen wiederholen musst. Statt `User.objects.create(...)`
  mit allen Pflichtfeldern schreibst du einfach `UserFactory()`.

```python
@pytest.mark.django_db
class TestOrderServiceAddItem:
    def test_add_item_to_draft_order(self):
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[...])
        order = OrderService.create_order(user=user)
        item = OrderService.add_item(order_id=order.pk, template_id=template.pk, parameters={"cpu": 4})
        assert item.order == order
```

💡 **Merke:** Für View-Tests gilt die Konvention, `RequestFactory` statt des
vollen Django-Test-`Client` einzusetzen — dazu mehr in der Vertiefung unten.
Externe Abhängigkeiten (z. B. ein CMDB- oder Provisioning-Backend) werden dabei
grundsätzlich **gemockt**, nicht echt angesprochen.

⚠️ **Achtung:** Celery-Tasks laufen in Tests nicht asynchron über Redis, sondern
synchron im selben Prozess. Dafür sorgt `CELERY_TASK_ALWAYS_EAGER = True` in den
Test-Settings (`config.settings.testing`). Ein `.delay()`-Aufruf in einem Test
läuft also sofort durch — kein Worker, kein Redis nötig.

---

## Kleine, fokussierte Tests

Ein Test prüft **eine** Sache. Lieber viele kleine Tests mit sprechenden Namen
(`test_add_item_validates_parameters`, `test_add_item_to_non_draft_raises`) als
ein großer Test, der drei Verhaltensweisen gleichzeitig abdeckt. Schlägt so ein
kleiner Test fehl, weißt du sofort, was kaputt ist — ohne den Test erst
auseinandernehmen zu müssen.

---

## Die wichtigsten Code-Regeln

Neben dem Testen gelten ein paar feste Konventionen für den Produktivcode:

| Regel | Kurzfassung |
|---|---|
| Thin Views | Logik gehört in Services (`services.py`), nicht in Views |
| Forms für Validierung | Kein rohes `request.POST` — Validierung läuft über Django-Forms |
| Django Admin | Primäres Admin-Tool für alle Verwaltungsaufgaben |
| Kein Self-Signup | `ACCOUNT_SIGNUP_ENABLED = False` — Nutzer legt ausschließlich der Admin an |
| Settings via django-environ | Niemals Secrets hart im Code — alles über Umgebungsvariablen |
| Migrationen squashen | Vor einem Release werden Migrationen zusammengefasst |

⚠️ **Achtung:** `DEBUG=True` in Produktion ist **fatal** — das darf niemals
deployt werden.

Für den Stil selbst (Formatierung, unbenutzte Imports, Reihenfolge von
Importen) läuft lokal **ruff** als Linter:

```bash
ruff check
```

💡 **Merke:** Führ `ruff check` vor jedem Commit aus. Ein sauberer Lint-Lauf ist
Teil der „Definition of Done" — nicht optional.

### Harte Zahlen: Zeilenlänge, Dateigröße, Imports

Neben den Regeln aus der Tabelle oben gibt es ein paar **konkrete Zahlen**, die
im Projekt als dokumentierte Team-Konvention festgehalten sind
(`cmp-docs/docs/entwicklung/conventions.md`):

| Konvention | Richtwert |
|---|---|
| Zeilenlänge | max. 100 Zeichen |
| Dateigröße | möglichst < 200 Zeilen pro Datei |
| View-Methoden | Richtwert ~15 Zeilen — alles Längere gehört in einen Service |
| Import-Reihenfolge | Standardbibliothek → Third-Party → Local, jeweils alphabetisch sortiert |
| Linter | `ruff` |

⚠️ **Achtung:** Diese Zahlen sind aktuell **nicht** über eine eigene
`pyproject.toml`- oder `ruff.toml`-Konfiguration im Repo erzwungen — eine solche
Datei existiert im Projekt (Stand jetzt) nicht. `ruff check` deckt mit seinen
Standard-Regeln allgemeine Dinge ab (z. B. unbenutzte Imports, offensichtliche
Syntax-Probleme). Zeilenlänge, Dateigröße, View-Länge und Import-Reihenfolge sind
darüber hinaus eine **dokumentierte Team-Konvention**, an die sich Code-Reviews
halten — nicht (noch) automatisch erzwungenes Tooling. Halte dich trotzdem
daran: Reviewer prüfen genau das.

---

## Versionierung & Releases

### Commit-Nachrichten: `type(scope): description`

Für **alle** Commits — nicht nur für Releases — gilt im Projekt ein festes
Format:

```
type(scope): description
```

| Teil | Bedeutung |
|---|---|
| `type` | Art der Änderung, z. B. `feat`, `fix`, `docs`, `refactor`, `test` |
| `scope` | Betroffener Bereich: eine Projektphase `B0`–`B9` oder ein App-Name (z. B. `orders`, `approvals`) — optional |
| `description` | Kurze, konkrete Beschreibung, was sich ändert |

Beispiele aus der Historie:

```
feat(B2): add CatalogService with list, search, validate
fix: restore conftest keepdb and flush stale test data
docs: add Phase B3 order lifecycle implementation plan
```

💡 **Merke:** `scope` ist optional (siehe das `fix`-Beispiel ohne Klammern),
`type` dagegen nicht — jeder Commit fängt mit einem der festen Types an.

### Versionsnummer & Release-Tags

Es gibt für dieses Projekt **keine** GitHub-Actions-Pipeline — Releases laufen
manuell. Die Single Source of Truth für die Versionsnummer ist `lucent-hub.yml`:

```yaml
name: cmp-Django
version: "1.5.0"
```

Jeder Release bekommt zusätzlich einen Git-Tag nach dem Muster `vX.Y.Z`
(aktuell bis `v1.5.0`) und einen Commit nach dem festen Muster:

```
release: vX.Y.Z — Kurzbeschreibung was sich geändert hat
```

Beispiel aus der Historie: `release: v1.5.0 — AP-13 Bestellkette; Doku, Ablaufdiagramm und Kennzahlen nachgezogen`.

🔍 **Im Code nachsehen:** Schau dir mit `git log --oneline --grep="^release:"`
die bisherigen Release-Commits an — du siehst das Muster sofort.

---

## CI/CD & automatisiertes Testing

> **Ist-Stand:** Es gibt **keine** CI/CD-Pipeline — kein `.github/`-Verzeichnis,
> keine GitHub-Actions. Tests laufen heute **manuell** (`pytest`,
> `scripts/run.sh`). Der folgende Abschnitt ist eine **Empfehlung** (Soll), kein
> Ist-Zustand.

Die Regel „TDD ist Pflicht" lebt aktuell von Disziplin. Eine kleine
**CI-Pipeline** würde daraus ein **automatisches Gate** machen: bei jedem Push
bzw. Merge-Request läuft

- `pytest` (alle Tests),
- `ruff check` (Lint),
- `python cmp/manage.py check --deploy` (Deployment-Checks),

und ein roter Lauf blockiert den Merge. Mehr braucht die Entwicklung nicht.

💡 **Merke:** Für die CI ist **kein** laufender Celery-Worker und **kein** Redis
nötig. In den Tests gilt `CELERY_TASK_ALWAYS_EAGER=True` — die Provisioning-Tasks
(`dispatch_provisioning`, `complete_dispatch`) laufen **synchron im Testprozess**.
Die Task-Logik wird also voll getestet, ganz ohne Broker und Worker. Ein echter
Worker ist nur im **Betrieb** nötig (siehe [12 — Wie es in Produktion läuft](12-wie-es-in-produktion-laeuft.md)).

⚠️ **Achtung — häufiger Denkfehler:** Der Worker reagiert **nicht** auf Ereignisse
der CI/CD-Pipeline. Zur Laufzeit verarbeitet er echte Anwendungs-Tasks, die über
**Redis** ankommen (z. B. ausgelöst durch eine genehmigte Bestellung) — die Pipeline
ist dafür keine Ereignisquelle. Der einzige Berührungspunkt: Beim **Deployment** wird
der Worker-Dienst neu gestartet (`systemctl restart cmp-celery`), damit er den neuen
Code lädt.

---

## Definition of Done — deine Checkliste

Bevor du eine Änderung als „fertig" betrachtest, geh diese Liste durch:

- [ ] **Rot → grün:** Es gibt mindestens einen Test, der ohne deine Änderung
      fehlschlägt und mit ihr durchläuft
- [ ] **`ruff check`** läuft ohne Fehler
- [ ] **Konventionen eingehalten:** Logik in Services, Validierung über Forms,
      keine hartkodierten Secrets
- [ ] **Migration erstellt**, falls du ein Model geändert hast (`makemigrations`)
- [ ] **Kleine Tests:** Jeder neue Test prüft genau ein Verhalten

---

## Vertiefung für Entwickler

<details>
<summary><b>Die Service-Schicht testen</b></summary>

**Warum `RequestFactory` statt Test-Client?** Weil Views im CMP-Projekt bewusst
*dünn* gehalten werden (siehe Tabelle oben) — die eigentliche Logik steckt in den
Services, nicht in der View-Funktion. Ein Test mit dem vollen Django-`Client`
(oder der `client`-Fixture von pytest-django) durchläuft immer den kompletten
HTTP-Stack: URL-Routing, Middleware, Session, Template-Rendering. Das ist gut für
End-to-End-Abdeckung, aber schwerfällig, wenn du eigentlich nur eine
Service-Methode wie `OrderService.add_item()` oder `ApprovalService.approve()`
prüfen willst.

Der schlankere Weg: Du baust dir mit `RequestFactory` nur das *Request-Objekt*,
das eine View bräuchte, und rufst die View-Funktion direkt auf — ganz ohne
Server, Middleware-Kette oder URL-Resolver dazwischen. Noch direkter geht es,
wenn du die Service-Methode *ganz ohne* View aufrufst, so wie es die
Unit-Tests unter `tests/unit/` tun (siehe `test_order_service.py` weiter oben).
Der Vorteil: Schlägt der Test fehl, weißt du sofort, dass die *Fachlogik*
betroffen ist — nicht ein Routing-Fehler oder eine Middleware-Eigenheit.
Integrationstests mit dem echten `client` (wie in `tests/integration/`) bleiben
trotzdem wichtig — sie prüfen genau die Schicht, die `RequestFactory`-Tests
bewusst auslassen: dass URL, View und Template tatsächlich zusammenpassen.

**Wie Factories und Fixtures zusammenspielen:** `tests/factories.py` kennt für
jedes zentrale Model eine Factory (`UserFactory`, `OrderFactory`,
`ServiceTemplateFactory`, `OrderItemFactory`). Diese Factories setzen sinnvolle
Default-Werte — `OrderFactory` erzeugt z. B. immer eine Bestellung im Zustand
`DRAFT` — und lassen sich per Keyword-Argument überschreiben, wenn ein Test einen
anderen Ausgangszustand braucht (`OrderFactory(status=OrderStatus.SUBMITTED)`).
Fixtures aus `tests/conftest.py` ergänzen das um Infrastruktur, die für *jeden*
Test gleich ist — im Projekt aktuell vor allem der Zugriff auf die
Test-Datenbank. Der Clou: Ein Testfall in `tests/unit/` liest sich dadurch fast
wie eine kleine Geschichte — „gegeben ein User, gegeben ein Template, wenn ich
ein Item hinzufüge, dann …" — ohne dass du dich um Konstruktions-Details
kümmern musst.

**Statuswechsel ohne echten Celery/Redis testen:** Ein Übergang wie
`approved → provisioning` löst im echten Betrieb einen Celery-Task aus
(`dispatch_provisioning.delay(...)`, siehe [Kapitel 07](07-async-und-provisioning.md)).
In der Testumgebung ist `CELERY_TASK_ALWAYS_EAGER = True` gesetzt — der Task läuft
dadurch synchron im selben Prozess, statt über einen echten Broker (Redis) an
einen separaten Worker verteilt zu werden. Ein Test kann also z. B.
`ApprovalService.approve()` aufrufen und danach direkt prüfen, ob die Order im
erwarteten Folgezustand steht — ganz ohne Redis-Server, ohne Worker-Prozess und
ohne künstliche Wartezeit. Externe Systeme dahinter (CMDB, Provisioning-Backend)
werden dabei zusätzlich gemockt, sodass der Test wirklich nur die *eigene*
Statuslogik prüft, nicht die Zuverlässigkeit eines Drittsystems.

</details>

<details>
<summary><b>Die Test-Datenbank: warum <code>--keepdb</code>?</b></summary>

Normalerweise legt Django für einen Testlauf eine frische Test-Datenbank an und
räumt sie danach wieder weg. Im CMP-Projekt hat der Datenbank-User dafür aber
keine `CREATEDB`-Berechtigung — `tests/conftest.py` ruft `setup_databases()`
deshalb explizit mit `keepdb=True` auf: Die Test-Datenbank bleibt zwischen
Testläufen bestehen und wird **wiederverwendet**, statt bei jedem Lauf neu
erzeugt zu werden.

⚠️ **Achtung:** Das hat einen Haken. Änderst du ein Model (neues Feld, neue
Migration), merkt die wiederverwendete Test-Datenbank davon zunächst nichts —
ihr Schema entspricht noch dem alten Stand. Du musst sie danach **manuell**
zurücksetzen:

```bash
PGPASSWORD=cmp psql -h localhost -U cmp -d cmp_django_test -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
cd cmp && python manage.py migrate --settings=config.settings.testing
```

Zwei Befehle helfen dir dabei, den Überblick zu behalten, bevor du zu diesem
Mittel greifst:

- **`python manage.py check`** — prüft das Projekt auf offensichtliche Fehler
  (kaputte Model-Referenzen, fehlerhafte Settings), ganz ohne die Datenbank
  anzufassen. Guter erster Schritt, wenn ein Testlauf mit einem unklaren Fehler
  abbricht.
- **`python manage.py showmigrations`** — zeigt dir alle Migrationen und markiert,
  welche bereits angewendet sind (`[X]`) und welche noch fehlen (`[ ]`). Damit
  siehst du sofort, ob deine Model-Änderung überhaupt schon eine Migration hat.

</details>

---

## 🔍 Im Code nachsehen

| Was | Wo |
|-----|-----|
| Test-Konfiguration | `pytest.ini` |
| Test-Settings (u. a. `CELERY_TASK_ALWAYS_EAGER`) | `cmp/config/settings/testing.py` |
| Zentrale Test-Factories | `tests/factories.py` |
| Geteilte Test-Fixtures | `tests/conftest.py` |
| Unit-/Integration-/E2E-Tests | `tests/unit/`, `tests/integration/`, `tests/e2e/` |
| Versions-Quelle | `lucent-hub.yml` |
| Django- und Test-Regeln im Klartext | `.claude/rules/django.md`, `.claude/rules/testing.md` |

Am einfachsten verstehst du den Zyklus, wenn du ihn selbst durchspielst:
Öffne `tests/unit/test_order_service.py`, ändere testweise eine Assertion so,
dass sie fehlschlägt, führe `pytest tests/unit/test_order_service.py` aus — und
sieh dir das Rot an, bevor du es wieder grün machst.

---

## Selbstcheck

Bevor du weiterliest, kannst du diese Fragen beantworten?

1. Was bedeutet „rot → grün → refactor" in eigenen Worten?
2. Warum brauchst du für Celery-Tasks in Tests keinen laufenden Redis-Server?
3. Wo liegt die Versionsnummer des Projekts, und wonach ist ein Release-Commit benannt?

<details>
<summary>Antworten anzeigen</summary>

1. Erst einen fehlschlagenden Test schreiben (rot), dann gerade so viel Code,
   dass er durchläuft (grün), dann bei grünen Tests aufräumen (refactor).
2. Weil `CELERY_TASK_ALWAYS_EAGER = True` in den Test-Settings Tasks synchron im
   selben Prozess ausführt, statt sie über einen echten Broker zu verteilen.
3. In `lucent-hub.yml` (Feld `version`). Release-Commits folgen dem Muster
   `release: vX.Y.Z — Kurzbeschreibung`.

</details>

---

⟵ [09 — Setup lokal](09-setup-lokal.md) · [📖 Übersicht](README.md) · [11 — Dein erster Beitrag](11-dein-erster-beitrag.md) ⟶
