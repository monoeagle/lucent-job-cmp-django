# Testing

## Übersicht

| Kategorie | Framework | Anzahl |
|-----------|-----------|--------|
| Unit | pytest | 129 |
| Integration | pytest-django | 97 |
| E2E | pytest-django | 4 |
| **Gesamt** | | **230** |

> Stand v1.0.0 (2026-06-18): **230 Tests grün** (`venv/bin/python3 -m pytest`, 0 Errors).

## Test-Methodik: TDD (Test-Driven Development)

1. **Rot:** Test schreiben, der fehlschlägt
2. **Grün:** Minimale Implementation, die den Test besteht
3. **Refactor:** Code aufräumen, Tests bleiben grün

## Test-Kategorien

### Unit Tests (`tests/unit/`)

Testen Services und Domain-Logik isoliert.

```python
class TestTemplateValidator:
    def test_missing_required_parameter(self):
        schema = [{"key": "cpu", "type": "integer", "required": True}]
        errors = TemplateValidator.validate_parameters(schema, {})
        assert len(errors) == 1
```

- Kein Datenbank-Zugriff (außer bei DB-abhängigen Services)
- Externe Abhängigkeiten gemockt
- Schnell (< 1s pro Test)

### Integration Tests (`tests/integration/`)

Testen Views, Models und ihre Zusammenarbeit.

```python
@pytest.mark.django_db
class TestOrderCreateView:
    def test_post_creates_order_with_item(self, client):
        user = UserFactory()
        template = ServiceTemplateFactory(parameters=[...])
        client.force_login(user)
        response = client.post(reverse("orders:create", kwargs={"template_pk": template.pk}), {"cpu": "4"})
        assert response.status_code == 302
        assert Order.objects.filter(user=user).count() == 1
```

- Echte PostgreSQL-Datenbank (mpp_django_test)
- Django Test-Client für HTTP-Requests
- Transaktions-Isolation pro Test

### E2E Tests (`tests/e2e/`)

Testen komplette Workflows über mehrere Services.

```python
@pytest.mark.django_db
class TestFullOrderWorkflow:
    def test_complete_lifecycle_with_approval(self):
        # Create → Submit → Approve → Provision → Done
        ...
```

## Test-Fixtures

### factory_boy Factories (`tests/factories.py`)

```python
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f"user-{n}")
    password = factory.PostGenerationMethodCall("set_password", "test123")
    role = UserRole.REQUESTER

class ServiceTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ServiceTemplate
    name = factory.Sequence(lambda n: f"Template-{n}")
    category = "compute"

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order
    user = factory.SubFactory(UserFactory)
    status = OrderStatus.DRAFT
```

### pytest Fixtures (`tests/conftest.py`)

`client` und `rf` (RequestFactory) werden automatisch von pytest-django bereitgestellt.

## Befehle

```bash
# Alle Tests
python -m pytest tests/ -v

# Nur Unit Tests
python -m pytest tests/unit/ -v

# Nur Integration Tests
python -m pytest tests/integration/ -v

# Nur E2E Tests
python -m pytest tests/e2e/ -v

# Einzelner Test
python -m pytest tests/unit/test_catalog_service.py::TestCatalogServiceList::test_list_active_templates -v

# Mit Coverage
python -m pytest tests/ --cov=mpp --cov-report=term-missing
```

## Konfiguration

**pytest.ini:**
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
pythonpath = mpp
testpaths = tests
```

**testing.py:** Schnelle Passwort-Hashes (`MD5PasswordHasher`), Celery EAGER-Modus, Test-Datenbank `mpp_django_test`.

## Hinweis: keepdb

Die Test-DB wird mit `keepdb=True` wiederverwendet (mpp-User hat kein CREATEDB). Bei Schema-Änderungen muss die DB manuell gelöscht werden:

```bash
PGPASSWORD=mpp psql -h localhost -U mpp -d mpp_django_test -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
cd mpp && python manage.py migrate --settings=config.settings.testing
```
