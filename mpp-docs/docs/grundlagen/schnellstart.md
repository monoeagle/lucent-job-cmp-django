# Schnellstart

## In 3 Schritten zum laufenden System

### 1. Setup

```bash
bash scripts/run.sh
# → Taste 1: Vollständiges Setup
```

### 2. Server starten

```bash
# Im run.sh Menü:
# → Taste 2: Dev-Server starten
# Oder manuell:
cd mpp && python manage.py runserver 8000
```

### 3. Im Browser öffnen

```
http://localhost:8000
```

## Demo-Zugänge

| User | Passwort | Rolle | Kann |
|------|----------|-------|------|
| test-requester | test123 | requester | Bestellen, eigene Orders sehen |
| test-approver | test123 | approver | Bestellen + Genehmigen/Ablehnen |
| test-admin | test123 | admin | Alles + Django Admin + Audit |
| test-multi | test123 | approver | Bestellen + Genehmigen |
| test-superadmin | test123 | superadmin | Alles + DSGVO-Anonymisierung |

## Demo-Workflow

1. **Login** als `test-requester` / `test123`
2. **Katalog** → Service-Katalog öffnen
3. **Template wählen** → z.B. "Linux VM" → Details
4. **Bestellen** → Parameter eingeben → Bestellung erstellen
5. **Bestellung einreichen** → Status wechselt zu "Submitted"
6. **Logout**, Login als `test-approver`
7. **Genehmigungen** → Offene Bestellung genehmigen
8. **Logout**, Login als `test-admin`
9. **Django Admin** → `http://localhost:8000/admin/` → Alle Daten einsehen
10. **Audit-Log** → Alle Aktionen nachvollziehen

## Navigation

| URL | Seite | Rolle |
|-----|-------|-------|
| `/` | Dashboard | alle |
| `/catalog/` | Service-Katalog | alle |
| `/orders/` | Meine Bestellungen | requester+ |
| `/approvals/` | Genehmigungen | approver+ |
| `/subscriptions/` | Subscriptions | requester+ |
| `/notifications/` | Benachrichtigungen | alle |
| `/audit/` | Audit-Log | admin+ |
| `/admin/` | Django Admin | admin+ |
| `/accounts/profile/` | Profil | alle |
