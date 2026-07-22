# Django-Admin

Der Django-Admin ist das primäre Administrationswerkzeug des CMP — er wird
nicht von einer eigenen App bereitgestellt, sondern ist Djangos eingebaute
Verwaltungsoberfläche (`django.contrib.admin`).

## 1. Ziel der Seite

Ein Admin oder Superadmin soll hier Benutzer, Genehmigungsregeln,
CMDB-Kontextregeln, Service-Templates, Bestellungen, Abonnements und
Audit-Logs direkt auf Modellebene pflegen können — insbesondere legt der
Admin hier alle Benutzerkonten an, da die Selbstregistrierung deaktiviert ist.

## 2. Screenshot

![Django-Verwaltungsoberfläche (Django-Admin): Abschnitte für Accounts (Users), Approvals (Approval requests, Approval rules), Audit, CMDB (Availability rules, Context restrictions, User tenant assignments), Notifications, Orders, Provisioning, Service Catalog, Subscriptions und Websites mit Hinzufügen-/Ändern-Links.](../../docs/images/screenshots/Screenshot_13_cmp.png)

Die Startseite listet einen Abschnitt je registrierter Django-App: Accounts
(Users), Approvals (Approval requests, Approval rules), Audit (Audit logs),
Authentifizierung und Autorisierung (Gruppen), CMDB (Availability rules,
Context restrictions, User tenant assignments), Konten (E-Mail-Adressen, aus
django-allauth), Notifications, Orders (Orders, Order item groups),
Provisioning (Dispatch logs), Service Catalog (Service templates),
Subscriptions (Subscriptions, Group subscriptions) und Websites (aus dem
Django-Sites-Framework, das allauth für die Domain-Zuordnung nutzt). Jede
Zeile bietet „Hinzufügen" und „Ändern".

## 3. Rolle und Zugriff

Der Django-Admin verwendet nicht die projekteigenen
Rollen-Mixins aus `cmp/core/mixins.py`, sondern Djangos eigene
`is_staff`/`is_superuser`-Felder auf dem `User`-Modell
(`cmp/apps/accounts/models.py:7-13`). Beim Stub-User-Seeding werden diese
Felder aus der Rolle abgeleitet:
`is_staff = role in (ADMIN, SUPERADMIN)` und
`is_superuser = (role == SUPERADMIN)`
(`cmp/apps/accounts/services.py:31-32`) — Admin und Superadmin erhalten also
Zugriff auf `/admin/`, Requester und Approver nicht. Für regulär über den
Admin angelegte Benutzer gilt dieselbe Zuordnung nicht automatisch; sie muss
dort explizit gesetzt werden (Felder „Staff status" / „Superuser status").

Die je App registrierten `ModelAdmin`-Klassen liegen in den jeweiligen
`admin.py`-Dateien, z. B. `UserAdmin` in
`cmp/apps/accounts/admin.py:7` (erweitert `django.contrib.auth.admin.UserAdmin`
um das Feld `role`).

## 4. URL und View

| HTTP-Pfad | URL-Name | View | Codestelle |
|---|---|---|---|
| `/admin/` | (Django-Admin-Namespace `admin:index` u. a.) | `django.contrib.admin.site.urls` | `cmp/config/urls.py:5` |

Der Django-Admin wird als komplettes URL-Set eingebunden
(`path("admin/", admin.site.urls)`), nicht als einzelne View — jede
registrierte Modell-Admin-Klasse bekommt darüber eigene Change-List-,
Add- und Change-URLs.

## 5. Zusammenfassung

Der Django-Admin läuft parallel zu den eigenen Rollen-Mixins auf einem
zweiten, unabhängigen Berechtigungsmechanismus (`is_staff`/`is_superuser`
statt `RoleRequiredMixin`). Beide Mechanismen sind beim Stub-Seeding
konsistent gehalten, aber technisch getrennt — das ist beim Anlegen neuer
Benutzer über den Admin-UI selbst zu beachten.

> Quelle: cmp-docs/docs/images/screenshots/Screenshot_13_cmp.png, cmp/config/urls.py, cmp/apps/accounts/models.py, cmp/apps/accounts/services.py, cmp/apps/accounts/admin.py — am Code geprüft 2026-07-22
