# Rollenmodell

CMP kennt vier Rollen, gepflegt als einfaches Feld auf dem `User`-Modell — kein
separates Berechtigungssystem, keine Gruppen, keine AD-Anbindung (dazu
[Kapitel 4.5](05-ausblick-ad-ldap.md)). Diese Seite zeigt, woraus eine Rolle besteht,
wer sie vergibt und wofür jede Rolle gedacht ist.

## 1. Ziel des Kapitels

Wer eine neue Rolle einführen oder eine bestehende ändern will, soll hier den
Ist-Zustand vorfinden: die vier tatsächlichen Rollenwerte, die Hierarchie zwischen
ihnen, und den einzigen Weg, wie eine Rolle einem Benutzer zugewiesen wird.

## 2. Die Rolle als Feld, nicht als System

Die vier Rollenwerte sind ein `TextChoices`-Enum ohne Django-Abhängigkeiten außer
`TextChoices` selbst (`cmp/core/domain/enums.py:5-9`):

```python
class UserRole(models.TextChoices):
    REQUESTER = "requester", "Requester"
    APPROVER = "approver", "Approver"
    ADMIN = "admin", "Admin"
    SUPERADMIN = "superadmin", "Superadmin"
```

`User.role` ist ein `CharField` mit diesen Choices, Default `requester`
(`cmp/apps/accounts/models.py:9-13`). Es gibt kein separates Rollen- oder
Berechtigungsmodell, keine Tabelle `roles` oder `permissions` — die Rolle ist ein
einzelnes Feld auf dem Benutzer-Datensatz.

Die vier Werte bilden eine strikte Hierarchie, hinterlegt als Liste
(`cmp/apps/accounts/services.py:5-10`):

```python
ROLE_HIERARCHY = [
    UserRole.REQUESTER,
    UserRole.APPROVER,
    UserRole.ADMIN,
    UserRole.SUPERADMIN,
]
```

`AccountService.is_at_least_role(user_role, minimum_role)` vergleicht die Positionen
beider Werte in dieser Liste (`cmp/apps/accounts/services.py:42-50`) — so entsteht die
Einschluss-Logik „jede höhere Rolle darf alles, was eine niedrigere darf" ohne
explizite Rechte-Liste je Rolle. Diese Funktion wird sowohl von den vier
Rollen-Mixins in `cmp/core/mixins.py` (indirekt, über feste `required_roles`-Listen)
als auch direkt in Views genutzt, etwa in `OrderListView._can_see_all()`
(`cmp/apps/orders/views.py:30-37`) und `DashboardView.get_context_data`
(`cmp/apps/dashboard/views.py:18`).

## 3. Wer vergibt eine Rolle

Es gibt genau zwei Wege, wie ein Benutzer seine Rolle bekommt — beide ohne
Selbstbedienung, konsistent mit `ACCOUNT_SIGNUP_ENABLED = False`
([Kapitel 4.1](01-authentifizierung.md)):

1. **Seed-Routine für Demo/Dev:** `AccountService.seed_stub_users()` legt fünf feste
   Benutzer mit fest zugeordneter Rolle an, definiert in `STUB_USERS`
   (`cmp/apps/accounts/services.py:12-18`). Die Rolle steht hier im Code, nicht in
   einer UI.
2. **Django Admin für reale Benutzer:** Das Feld `role` ist im `UserAdmin` editierbar
   (`cmp/apps/accounts/admin.py:11-13`). Das setzt voraus, dass der bearbeitende
   Account selbst Zugriff auf `/admin/` und die Permission `accounts.change_user`
   hat. Im Seed wird diese Permission an niemanden vergeben (geprüft:
   `grep -rn "user_permissions\|\.groups\.add\|assign_perm" cmp/apps/` findet keinen
   Treffer außer dem Migrations-Feld selbst) — verlässlich funktioniert das nur für
   `is_superuser=True`, also `test-superadmin`. Für `admin`-Benutzer ohne separat
   vergebene Permission ist das nicht geprüft und im Zweifel wirkungslos; Details
   dazu in [Kapitel 4.3](03-rechte-matrix.md).

Es existiert keine App-eigene View, über die ein Benutzer die eigene oder eine fremde
Rolle ändert (geprüft: `cmp/apps/accounts/views.py` enthält ausschließlich die
lesende `ProfileView`).

## 4. Die vier Rollen im Einzelnen

| Rolle | Zweck | Wer vergibt sie | Was sie zusätzlich darf |
|---|---|---|---|
| `requester` | Standardrolle jedes neuen Benutzers | Automatisch (Modell-Default, `accounts/models.py:12`) oder explizit im Seed/Admin | Katalog durchsuchen, bestellen, eigene Bestellungen/Subscriptions/Benachrichtigungen einsehen |
| `approver` | Genehmigt Bestellungen | Seed (`STUB_USERS`) oder Django Admin | Zusätzlich: Genehmigungs-Queue, genehmigen/ablehnen |
| `admin` | Betrieb und Auswertung | Seed oder Django Admin | Zusätzlich: Admin-Dashboard, Systemkonfiguration ansehen, Audit-Log |
| `superadmin` | Regelpflege und voller Systemzugriff | Seed oder Django Admin (`is_superuser=True` zwingend für sicheren Admin-Zugriff, s.o.) | Zusätzlich: Regel-Übersicht im eigenen Admin-Panel, uneingeschränkter Django-Admin-Zugriff |

Die vollständige Anwendungsfall-Liste je Rolle (mit URL und View) steht in
[Kapitel 1.2](../01-ziel-und-anforderungen/02-benutzerrollen-und-anwendungsfaelle.md),
die vollständige Rechte-Matrix mit Code-Beleg je Zelle in
[Kapitel 4.3](03-rechte-matrix.md).

## 5. Zusammenfassung

Eine Rolle in CMP ist nichts weiter als ein Textfeld auf `User` mit vier möglichen
Werten und einer festen Hierarchie-Liste im Code — kein Gruppenmodell, keine
Django-Permissions je Rolle. Zugewiesen wird sie ausschließlich über die
Seed-Routine (Demo) oder Django Admin (real), nie durch den Benutzer selbst. Wie
diese Rolle in einzelnen Views durchgesetzt wird, zeigt die Rechte-Matrix im
nächsten Abschnitt.

> Quelle: cmp/core/domain/enums.py, cmp/apps/accounts/models.py, cmp/apps/accounts/services.py, cmp/apps/accounts/admin.py, cmp/apps/accounts/views.py, cmp/apps/orders/views.py, cmp/apps/dashboard/views.py — am Code geprüft 2026-07-22
