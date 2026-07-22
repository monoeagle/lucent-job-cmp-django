# TDD und Teststrategie

TDD ist im Projekt verbindlich vorgeschrieben. Diese Seite zeigt die reale
Testsuite, die verwendeten Werkzeuge — und zwei Stellen, an denen die
gelebte Praxis von der niedergeschriebenen Regel abweicht.

## 1. Ziel des Kapitels

Wer einen Test schreibt, soll wissen: welches Werkzeug für welche Ebene,
wie die Suite läuft, und was tatsächlich (nicht behauptet) an Testzahl
und Testart im Repository steckt.

## 2. TDD ist Pflicht

`.claude/rules/testing.md` schreibt Test-zuerst vor: der Test muss vor
der Implementierung existieren und **rot** sein, bevor Code folgt. Ein
vollständig durchgespieltes Beispiel dieses Ablaufs steht in Anhang A.3
(„Rezept: neue Bestelloption") — Test schreiben, rot sehen, Parameter
ergänzen, grün sehen, Gesamtlauf grün.

## 3. Testarchitektur

`pytest.ini` (Projektwurzel):

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
pythonpath = cmp
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

Drei Ordner unter `tests/` (Dateizahl nachgezählt am 2026-07-22):

| Ordner | Testdateien | Zweck |
|---|---|---|
| `tests/unit/` | 23 | Domain-Logik, Services, Clients, Settings — ohne HTTP |
| `tests/integration/` | 16 | Views + DB über den `client`-Fixture |
| `tests/e2e/` | 1 | vollständige Workflows über mehrere Views |

## 4. Reale Testzahl

```bash
venv/bin/python3 -m pytest --collect-only -q
```

Ausgeführt am 2026-07-22 aus der Projektwurzel (passend zu
`pythonpath = cmp`, `testpaths = tests` in `pytest.ini`): letzte Zeile
**„330 tests collected"**. Diese Zahl ist frisch erhoben, nicht aus dem
Changelog fortgeschrieben (der zuletzt dort genannte Stand — v1.3.1 —
lautete ebenfalls 330, deckt sich also).

## 5. Keine Coverage-Kennzahl

`pytest-cov` ist **nicht** installiert — geprüft über
`venv/bin/python3 -m pip list` (2026-07-22): kein `pytest-cov`, kein
`coverage` im Paketstand, keine Erwähnung in `requirements/*.txt`. Es gibt
daher keine Coverage-Prozentzahl für dieses Projekt. Eine geschätzte Zahl
wäre erfunden — sie fehlt hier bewusst.

## 6. factory_boy für Testdaten

`tests/factories.py:10-16` (`UserFactory`):

```python
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user-{n}")
    password = factory.PostGenerationMethodCall("set_password", "test123")
    role = UserRole.REQUESTER
```

`factory.Sequence` verhindert Namenskollisionen über mehrere Tests
hinweg, `PostGenerationMethodCall` sorgt für ein echtes gehashtes Passwort
statt eines Klartextfelds.

## 7. Ist-Stand: überwiegend `client`-Fixture, `rf` nur für die Mixin-Tests

`.claude/rules/testing.md` schreibt **„RequestFactory für View-Tests
(nicht Client)"** vor. Der reale Code folgt dem überwiegend **nicht** — aber
die Suche danach ist eine Falle: Die Klasse `RequestFactory` wird nirgends
importiert (`grep -r RequestFactory tests/ cmp/` → null Treffer), pytest-django
stellt sie jedoch als Fixture **`rf`** bereit. Und die wird benutzt: in
`tests/integration/test_role_access.py` in **11** Tests — der einzigen Datei,
die die Rollen-Mixins isoliert prüft, wo eine echte Request-Instanz ohne
URL-Routing genau passt.

Alle übrigen View-Tests nehmen den `client`-Fixture (Djangos Test-`Client`):
**54** Testfunktionen gegenüber 11 mit `rf`, allein in
`tests/integration/test_order_views.py` **49** Aufrufe von
`client.get(...)`/`client.post(...)`. Beispiel (Zeilen 1-17):

```python
import pytest
from django.urls import reverse
from tests.factories import UserFactory, ServiceTemplateFactory, OrderFactory, OrderItemFactory


@pytest.mark.django_db
class TestOrderListView:
    def test_requires_login(self, client):
        response = client.get(reverse("orders:list"))
        assert response.status_code == 302

    def test_returns_200(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("orders:list"))
        assert response.status_code == 200
```

Diese Zeile ist eine dokumentierte Zielregel, keine gelebte Praxis — beim
Schreiben neuer View-Tests ist beides zu erwarten: der bestehende Stil
(`client`-Fixture) und die Möglichkeit, dass jemand die Doku-Regel
(`RequestFactory`) wörtlich nimmt. Für Konsistenz mit dem bestehenden Code
ist der `client`-Fixture die pragmatische Wahl.

## 8. Externe Abhängigkeiten: Stub-Clients statt Mock-Objekte

Auch hier weicht die Praxis vom naheliegenden Verständnis der Regel
„Externe Abhängigkeiten mocken" ab: `unittest.mock`, `Mock(...)` und
`@patch` kommen in der gesamten Suite **kein einziges Mal** vor (eine
erste Suche traf nur auf `monkeypatch` als Teilstring, das ist die
pytest-Fixture für Umgebungsvariablen, kein Mock-Objekt). Statt Mocks
gibt es dedizierte **Stub-Client-Klassen**, die direkt instanziiert
werden:

- `GitLabStubClient` (`cmp/apps/provisioning/clients.py:5`) — simuliert
  Pipeline-Trigger im Speicher.
- `CmdbStubClient` (`cmp/apps/cmdb/clients.py:8`) — liest Standorte,
  Netzwerke und Tenants aus YAML-Fixtures (`cmp/stubs/cmdb/*.yml`).

Beleg in `tests/unit/test_provisioning_client.py:1-10`:

```python
from apps.provisioning.clients import GitLabStubClient


class TestGitLabStubClient:
    def setup_method(self):
        self.client = GitLabStubClient()

    def test_trigger_returns_pipeline_id(self):
        result = self.client.trigger_pipeline("VM", {"cpu": 4})
        assert "pipeline_id" in result
```

Für den Ausbau (echter GitLab-/OpenTofu-Client, AP-20) bedeutet das: der
Austausch-Punkt ist die Stub-Client-Klasse selbst, kein Mock im Testcode.

## 9. Celery: `EAGER` in Tests und Entwicklung

`config/settings/testing.py:19-21`:

```python
# Celery: run tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

`config/settings/development.py:8` setzt dieselbe Variable für die
lokale Entwicklung; `config/settings/production.py:49` setzt sie
ausdrücklich auf `False` — ein eigener Test
(`tests/unit/test_production_settings.py:98-100`) sichert das ab.

## 10. Tests ausführen

```bash
venv/bin/python3 -m pytest -q                        # gesamte Suite
venv/bin/python3 -m pytest tests/unit/ -v --tb=short  # nur Unit
venv/bin/python3 -m pytest tests/integration/ -v --tb=short
venv/bin/python3 -m pytest tests/e2e/ -v --tb=short
```

Entspricht den Optionen a–d in `scripts/run.sh:277-301` (Menüpunkt 3).

## 11. Zusammenfassung

TDD ist Pflicht und wird für neue Bestelloptionen nachweislich so gelebt
(Anhang A.3). Die Suite umfasst real **347 Tests** (2026-07-23), ohne
Coverage-Kennzahl, da `pytest-cov` fehlt. Zwei Regeln aus
`.claude/rules/testing.md` sind Zielbild, nicht Ist-Stand: View-Tests
laufen über den `client`-Fixture statt `RequestFactory`, und externe
Abhängigkeiten werden über Stub-Client-Klassen ersetzt, nicht über
`unittest.mock`.

> Quelle: `pytest.ini`, `.claude/rules/testing.md`, `tests/factories.py:10-16`, `tests/integration/test_order_views.py:1-17`, `tests/unit/test_provisioning_client.py:1-10`, `cmp/apps/provisioning/clients.py:5`, `cmp/apps/cmdb/clients.py:8`, `cmp/config/settings/testing.py:19-21`, `cmp/config/settings/development.py:8`, `cmp/config/settings/production.py:49`, `tests/unit/test_production_settings.py:98-100`, `scripts/run.sh:277-301`; Testzahl per `pytest --collect-only -q` — am Code geprüft 2026-07-22
