# Datenmodell

## Übersicht

15 Tabellen in PostgreSQL, verwaltet über Django ORM und Migrations.

```
users ←── orders ←── order_items ←── dispatch_logs
              ↑           ↑
              │      order_item_groups
              │
         approval_requests ←── approval_rules

service_templates ←── availability_rules
                  ←── context_restrictions

users ←── user_tenant_assignments
     ←── notifications
     ←── subscriptions
     ←── group_subscriptions
     ←── audit_logs
```

## Tabellen

### users

Custom User Model (erbt von Django AbstractUser).

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| username | CharField(150) | Benutzername (unique) |
| email | EmailField | E-Mail |
| password | CharField | Passwort-Hash |
| role | CharField(20) | `requester`, `approver`, `admin`, `superadmin` |
| is_staff | Boolean | Django Admin Zugang |
| is_superuser | Boolean | Superuser-Flag |
| created_at | DateTime | Erstellungszeitpunkt |
| updated_at | DateTime | Letzte Änderung |

### service_templates

Service-Katalog-Einträge mit parametrischem JSON-Schema.

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| name | CharField(200) | Template-Name (unique) |
| category | CharField(30) | Kategorie (compute, database, container, ...) |
| description | TextField | Beschreibung |
| parameters | JSONField | Parameter-Schema (Liste von Parametern) |
| is_active | Boolean | Aktiv im Katalog |
| version | PositiveInteger | Versionsnummer |
| created_at | DateTime | Erstellungszeitpunkt |
| updated_at | DateTime | Letzte Änderung |

**Parameter-Schema (JSON):**

```json
[
  {
    "key": "cpu",
    "type": "integer",
    "label": "CPUs",
    "required": true,
    "default": 2
  },
  {
    "key": "os_version",
    "type": "choice",
    "label": "OS Version",
    "required": true,
    "options": ["ubuntu-22.04", "ubuntu-24.04"],
    "default": "ubuntu-24.04"
  }
]
```

Unterstützte Typen: `integer`, `string`, `boolean`, `float`, `choice`

### orders

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| user_id | FK → users | Besteller |
| status | CharField(30) | Status (siehe Status-Machine) |
| notes | TextField | Anmerkungen |
| created_at | DateTime | Erstellungszeitpunkt |
| updated_at | DateTime | Letzte Änderung |

**Status-Werte:** `draft`, `validated`, `submitted`, `pending_approval`, `approved`, `rejected`, `provisioning`, `done`, `failed`

### order_items

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| order_id | FK → orders | Zugehörige Bestellung |
| template_id | FK → service_templates | Service-Template |
| parameters | JSONField | Gewählte Parameter-Werte |
| group_id | FK → order_item_groups (nullable) | Optionale Gruppen-Zuordnung |
| created_at | DateTime | Erstellungszeitpunkt |

### order_item_groups

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| order_id | FK → orders | Zugehörige Bestellung |
| template_id | FK → service_templates | Service-Template |
| quantity | PositiveInteger | Anzahl |
| shared_parameters | JSONField | Geteilte Parameter |
| created_at | DateTime | Erstellungszeitpunkt |

### approval_rules

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| template_id | FK → service_templates | Für welches Template |
| condition | JSONField | Bedingungen (z.B. min_cpu) |
| approver_role | CharField(20) | Welche Rolle genehmigt |
| is_active | Boolean | Regel aktiv |
| created_at | DateTime | Erstellungszeitpunkt |

### approval_requests

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| order_id | FK → orders | Bestellung |
| rule_id | FK → approval_rules | Auslösende Regel |
| status | CharField(20) | `pending`, `approved`, `rejected` |
| decided_by_id | FK → users (nullable) | Entscheider |
| decided_at | DateTime (nullable) | Entscheidungszeitpunkt |
| comment | TextField | Kommentar |
| created_at | DateTime | Erstellungszeitpunkt |

### dispatch_logs

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| order_item_id | FK → order_items | Zugehöriges Item |
| pipeline_id | CharField(100) | GitLab Pipeline-ID |
| status | CharField(30) | `pending`, `running`, `success`, `failed` |
| payload | JSONField | Request-Daten |
| dispatched_at | DateTime | Dispatch-Zeitpunkt |
| completed_at | DateTime (nullable) | Abschluss-Zeitpunkt |

### availability_rules

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| template_id | FK → service_templates | Template |
| location | CharField(50) | Location-ID (z.B. "loc-fra") |
| tenant | CharField(50) | Tenant-ID |
| is_available | Boolean | Verfügbar an diesem Standort? |

### context_restrictions

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| template_id | FK → service_templates | Template |
| parameter_key | CharField(50) | Eingeschränkter Parameter |
| context_field | CharField(50) | Kontext-Feld (location, tenant) |
| allowed_values | JSONField | Erlaubte Werte |

### user_tenant_assignments

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| user_id | FK → users | Benutzer |
| tenant | CharField(50) | Tenant-ID |

Unique: `(user_id, tenant)`

### notifications

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| user_id | FK → users | Empfänger |
| title | CharField(200) | Titel |
| message | TextField | Nachricht |
| is_read | Boolean | Gelesen-Status |
| category | CharField(50) | Kategorie (info, warning, ...) |
| created_at | DateTime | Erstellungszeitpunkt |

### subscriptions

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| user_id | FK → users | Inhaber |
| order_item_id | FK → order_items | Ursprüngliches Item |
| status | CharField(30) | `active`, `cancelled` |
| valid_from | DateTime | Gültig ab |
| valid_until | DateTime (nullable) | Gültig bis (bei Kündigung) |

### group_subscriptions

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| user_id | FK → users | Inhaber |
| order_item_group_id | FK → order_item_groups | Ursprüngliche Gruppe |
| status | CharField(30) | `active`, `cancelled` |

### audit_logs

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| id | BigAutoField | Primärschlüssel |
| user_id | FK → users (nullable) | Auslösender User (null bei Anonymisierung) |
| action | CharField(100) | Aktion (z.B. "order_created") |
| resource_type | CharField(50) | Ressource (z.B. "order") |
| resource_id | Integer | Ressourcen-ID |
| details | JSONField | Zusätzliche Details |
| ip_address | GenericIPAddress (nullable) | IP-Adresse |
| timestamp | DateTime | Zeitstempel |
