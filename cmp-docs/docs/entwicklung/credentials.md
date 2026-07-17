# Credentials

## Demo-Benutzer

Werden über `python manage.py seed` erstellt.

| Username | Passwort | Rolle | is_staff | is_superuser |
|----------|----------|-------|----------|-------------|
| test-requester | test123 | requester | Nein | Nein |
| test-approver | test123 | approver | Nein | Nein |
| test-admin | test123 | admin | Ja | Nein |
| test-multi | test123 | approver | Nein | Nein |
| test-superadmin | test123 | superadmin | Ja | Ja |

## Rollen-Berechtigungen

| Aktion | requester | approver | admin | superadmin |
|--------|-----------|----------|-------|------------|
| Login | ja | ja | ja | ja |
| Katalog ansehen | ja | ja | ja | ja |
| Bestellen | ja | ja | ja | ja |
| Eigene Orders | ja | ja | ja | ja |
| Approval-Queue | — | ja | ja | ja |
| Genehmigen/Ablehnen | — | ja | ja | ja |
| Django Admin | — | — | ja | ja |
| Audit-Log | — | — | ja | ja |
| Katalog verwalten | — | — | ja | ja |
| DSGVO-Anonymisierung | — | — | — | ja |

## Datenbank

| Parameter | Wert |
|-----------|------|
| Host | localhost |
| Port | 5432 |
| User | cmp |
| Passwort | cmp |
| Dev-DB | cmp_django_dev |
| Test-DB | cmp_django_test |

## Django Admin

URL: `http://localhost:8000/admin/`

Zugang: `test-admin` oder `test-superadmin` (is_staff=True)

Verwaltbar über Admin:
- Benutzer und Rollen
- Service-Templates
- Approval-Regeln
- Bestellungen und Items
- Availability Rules
- Notifications
- Audit-Logs
- Subscriptions
