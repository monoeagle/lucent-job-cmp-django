# Authentifizierung

CMP meldet Benutzer über `django-allauth` an, sitzungsbasiert (Session-Cookie), ohne
Selbstregistrierung. Dieses Kapitel zeigt den Login-Mechanismus, den Login-Flow Schritt
für Schritt und die Session-relevanten Einstellungen.

## 1. Ziel des Kapitels

Wer eine neue View absichern oder den Login-Weg ändern will, soll hier nachschlagen
können: welches Auth-Backend greift, wie ein Login-Versuch technisch abläuft, wer
Benutzer anlegen darf, und welche Session-Einstellungen aktiv sind.

## 2. Auth-Backend

CMP nutzt `django-allauth==65.15.0` auf `Django==6.0.3` (`requirements.txt:9-10`),
sitzungsbasiert — kein Token, kein JWT. Zwei Backends sind konfiguriert
(`cmp/config/settings/base.py:93-96`):

```python
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
```

`ModelBackend` ist für den Zugriff über Django Admin nötig, die allauth-Backend-Klasse
für den regulären Login unter `/accounts/login/`. Beide prüfen gegen dasselbe
`User`-Modell (`AUTH_USER_MODEL = "accounts.User"`, `base.py:32`) und dasselbe
Passwort-Hash.

Relevante `allauth`-Einstellungen (`base.py:97-99`):

| Einstellung | Wert | Bedeutung |
|---|---|---|
| `ACCOUNT_LOGIN_METHODS` | `{"username"}` | Login nur über Benutzername, keine E-Mail-Login-Option |
| `ACCOUNT_EMAIL_VERIFICATION` | `"none"` | Keine E-Mail-Bestätigung nötig |
| `ACCOUNT_SIGNUP_ENABLED` | `False` | Öffentliche Registrierung ist abgeschaltet |

`AUTH_PASSWORD_VALIDATORS = []` (`base.py:78`) — das Projekt setzt aktuell keine
Passwort-Komplexitätsregeln (Django-Default-Validatoren sind deaktiviert, nicht nur
unkonfiguriert gelassen).

## 3. Registrierung ist deaktiviert — Admin legt alle Benutzer an

Mit `ACCOUNT_SIGNUP_ENABLED = False` gibt es keine Selbstregistrierung. Ein Benutzer
entsteht auf einem von zwei Wegen:

1. **Für Entwicklung/Demo:** `python manage.py seed` ruft
   `AccountService.seed_stub_users()` auf und legt fünf feste Test-Benutzer an
   (`cmp/apps/accounts/services.py:12-40`) — Details und Zugangsdaten in
   [Kapitel 1.2, Abschnitt 4](../01-ziel-und-anforderungen/02-benutzerrollen-und-anwendungsfaelle.md).
2. **Für reale Benutzer:** Django Admin unter `/admin/`. `User` ist dort registriert
   (`cmp/apps/accounts/admin.py:6-16`), das Feld `role` ist Teil der Fieldsets. Es
   existiert keine App-eigene View zum Anlegen oder Ändern eines Benutzers — die
   einzige `accounts`-View ist `ProfileView`, eine reine Anzeige des eigenen Profils,
   kein Formular (`cmp/apps/accounts/views.py:1-6`, `cmp/apps/accounts/urls.py:1-7`).

## 4. Login-Flow im Detail

Die Login-URLs kommen direkt aus `allauth.urls`, unter demselben Präfix wie die
`accounts`-App eingebunden (`cmp/config/urls.py:6-7`):

```python
path("accounts/", include("allauth.urls")),
path("accounts/", include("apps.accounts.urls")),
```

Ablauf für einen Login-Versuch:

1. `GET /accounts/login/` rendert das projekteigene Template
   `cmp/templates/account/login.html`, das allauths Standardtemplate überschreibt.
   Es zeigt ein einfaches Formular mit den Feldern `login` (Benutzername) und
   `password` (`account/login.html:8-17`).
2. `POST /accounts/login/` wird von `allauth.account`-Views verarbeitet, die die
   `AUTHENTICATION_BACKENDS` der Reihe nach prüfen.
3. Bei Erfolg legt Django eine Session an und leitet auf `LOGIN_REDIRECT_URL = "/"`
   weiter (`base.py:100`) — das ist `dashboard:home`.
4. Bei Fehler zeigt das Template bei `form.errors` immer denselben Text
   „Benutzername oder Passwort falsch." (`account/login.html:18-20`) — es unterscheidet
   nicht zwischen unbekanntem Benutzernamen und falschem Passwort.
5. `POST /accounts/logout/` (ebenfalls aus `allauth.urls`) beendet die Session und
   leitet auf `LOGOUT_REDIRECT_URL = "/accounts/login/"` weiter (`base.py:101`).

Nicht angemeldete Zugriffe auf eine geschützte View werden von
`_LazyLoginRequiredMixin.dispatch` abgefangen, das auf `settings.LOGIN_URL`
umleitet (`cmp/core/mixins.py:47-52`). `LOGIN_URL` ist im Projekt an keiner Stelle
gesetzt (geprüft: `grep -rn "LOGIN_URL" cmp/` findet nur diese eine Verwendungsstelle);
es greift Djangos Default `/accounts/login/`, der zufällig mit dem oben gezeigten
URL-Präfix übereinstimmt.

Der Zugang zu Django Admin (`/admin/`) läuft **nicht** über dieses Template, sondern
über Djangos eingebautes Admin-Login — eine eigene Form unter derselben Instanz,
die aber gegen dasselbe `User`-Modell und Passwort prüft.

## 5. Session- und Cookie-Einstellungen

In `base.py` und `development.py` ist keine `SESSION_*`-Einstellung gesetzt (geprüft:
`grep -rn "SESSION" cmp/config/settings/base.py cmp/config/settings/development.py`
liefert keinen Treffer) — es gelten Djangos Standardwerte, insbesondere
`SESSION_COOKIE_AGE` von 14 Tagen und keine automatische Ablaufzeit beim Schließen
des Browsers.

Erst `production.py` greift ein, gesteuert über `django-environ`
(`cmp/config/settings/production.py:18-29,59-60`):

| Einstellung | Produktions-Default | Quelle |
|---|---|---|
| `SESSION_COOKIE_SECURE` | `True` | `production.py:27,59` |
| `CSRF_COOKIE_SECURE` | `True` | `production.py:28,60` |
| `SECURE_SSL_REDIRECT` | `True` | `production.py:20,57` |

Ein Kommentar im Code hält fest, dass der Installer `SESSION_COOKIE_SECURE` nur im
reinen HTTP-Modus (kein TLS) auf `False` umschaltet — sonst käme ohne TLS weder das
Session- noch das CSRF-Cookie beim Client an (`production.py:24-26`).

## 6. Zusammenfassung

CMP setzt auf sitzungsbasierte Anmeldung über `django-allauth`, mit deaktivierter
Selbstregistrierung — jeder Benutzer entsteht über die Seed-Routine (Demo) oder über
Django Admin (real). Der Login-Flow ist ein klassisches Formular-POST gegen
`/accounts/login/`, geschützte Views leiten unauthentifizierte Zugriffe auf dieselbe
URL um. Session-Cookies folgen Djangos Defaults in Entwicklung und werden erst in
`production.py` gehärtet (secure, HTTPS-Redirect). Welche Rolle ein angemeldeter
Benutzer hat und was diese Rolle bedeutet, zeigt das folgende Kapitel.

> Quelle: cmp/config/settings/base.py, cmp/config/settings/development.py, cmp/config/settings/production.py, cmp/config/urls.py, cmp/core/mixins.py, cmp/apps/accounts/admin.py, cmp/apps/accounts/views.py, cmp/apps/accounts/urls.py, cmp/apps/accounts/services.py, cmp/templates/account/login.html, requirements.txt — am Code geprüft 2026-07-22
