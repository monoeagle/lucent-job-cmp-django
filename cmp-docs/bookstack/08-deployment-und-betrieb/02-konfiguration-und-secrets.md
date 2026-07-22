# Konfiguration und Secrets

Wie CMP in Produktion konfiguriert wird, welche Umgebungsvariablen es gibt und
warum `DEBUG=True` in Produktion ein Totalausfall der Absicherung wäre.

## 1. Ziel des Kapitels

Wer die Umgebungsdatei einer Installation liest oder einen neuen Wert ergänzen
will, findet hier die vollständige, am Code geprüfte Liste der Variablen, die
`config.settings.production` kennt — mit Default, Pflicht-Status und Fundstelle.

## 2. django-environ statt hartcodierter Werte

`config.settings.production` liest **alle** sicherheitsrelevanten Werte über
`django-environ` aus der Prozessumgebung, kein Secret steht im Code
(`cmp/config/settings/production.py:1-11`). Auf der VM injiziert systemd die
Werte über `EnvironmentFile=/etc/cmp/cmp.env` in beide Units (`cmp-web.service`,
`cmp-celery.service`, `deploy/lib.sh:174,203`). Zusätzlich liest das Modul optional
eine `.env`-Datei neben `manage.py`, falls vorhanden — auf der VM ist das nicht
der übliche Weg, da systemd die Variablen bereits liefert
(`cmp/config/settings/production.py:31-35`).

Die Datei selbst bekommt restriktive Rechte: `chown root:cmp`, `chmod 640` — nur
root schreibt, die Gruppe `cmp` liest mit (`deploy/install.sh:254`).

## 3. Vollständige Variablenliste

Ermittelt aus `cmp/config/settings/production.py` (Schema-Definition
Zeile 18–29, Zuweisung Zeile 38–63):

| Variable | Typ | Default | Pflicht? | Zeile |
|---|---|---|---|---|
| `SECRET_KEY` | str | **kein Default** | ja — Fehlstart ohne | `production.py:39` |
| `DATABASE_URL` | URL | **kein Default** | ja — Fehlstart ohne | `production.py:43` |
| `ALLOWED_HOSTS` | Liste | `[]` | nein — siehe Warnung unten | `production.py:22,40` |
| `DEBUG` | bool | `False` | nein | `production.py:19,38` |
| `DB_CONN_MAX_AGE` | int | `60` | nein | `production.py:44` |
| `CELERY_BROKER_URL` | str | `redis://localhost:6379/0` | nein | `production.py:47` |
| `CELERY_RESULT_BACKEND` | str | Wert von `CELERY_BROKER_URL` | nein | `production.py:48` |
| `SECURE_SSL_REDIRECT` | bool | `True` | nein | `production.py:20,57` |
| `SESSION_COOKIE_SECURE` | bool | `True` | nein | `production.py:27,59` |
| `CSRF_COOKIE_SECURE` | bool | `True` | nein | `production.py:28,60` |
| `CSRF_TRUSTED_ORIGINS` | Liste | `[]` | nein — praktisch aber nötig, sonst scheitert jedes Formular an CSRF | `production.py:23,61` |
| `SECURE_HSTS_SECONDS` | int | `31536000` (1 Jahr) | nein | `production.py:21,63` |

`install.sh` schreibt in Schritt 5/8 die Pflichtwerte plus `CELERY_BROKER_URL`
direkt, und hängt die modusabhängigen Security-Zeilen an
(`deploy/install.sh:243-253`, siehe Kapitel 8.3).

## 4. Korrektur: `ALLOWED_HOSTS` ist keine echte Pflichtvariable

Der Modul-Docstring nennt `ALLOWED_HOSTS` neben `SECRET_KEY` und `DATABASE_URL`
als „Pflicht-Variable" (`production.py:10`). Am Code geprüft stimmt das nur für
die beiden anderen: `SECRET_KEY` und `DATABASE_URL` werden ohne Default an
`env()` übergeben — fehlen sie, wirft `django-environ` `ImproperlyConfigured` und
der Prozess startet nicht (verifiziert per Testaufruf gegen `django-environ` ohne
gesetzte Variable). `ALLOWED_HOSTS` hat dagegen einen Schema-Default von `[]`
(`production.py:22`) — fehlt die Variable, startet Django **ohne Fehler**, lehnt
dann aber jeden Host mit `DisallowedHost` (HTTP 400) ab. Praktisch macht das
keinen Unterschied (das Portal ist ohne passenden `ALLOWED_HOSTS`-Wert ohnehin
unbenutzbar) — der Unterschied liegt darin, *wie* es scheitert: sofortiger
Fehlstart bei den beiden echten Pflichtwerten, stiller Leerlauf bei
`ALLOWED_HOSTS`.

## 5. `DEBUG=True` in Produktion ist FATAL

Das ist projektweite Regel (`CLAUDE.md`) und in den Settings selbst abgesichert:
Der Schema-Default für `DEBUG` ist `False` (`production.py:19`), die Zuweisung
`DEBUG = env("DEBUG")` übernimmt diesen Default, solange die Variable nicht
gesetzt ist (`production.py:38`). Das ist die Stelle, die eine vergessene
Konfiguration absichert — sie verhindert aber **keine bewusste Übersteuerung**:
Setzt jemand `DEBUG=True` explizit in `/etc/cmp/cmp.env`, übernimmt Django das
ungeprüft, es gibt keine zusätzliche Laufzeit-Sperre dagegen. Die Absicherung ist
ein sicherer Default, kein Hard-Block.

```bash
grep '^DEBUG=' /etc/cmp/cmp.env    # muss False sein oder ganz fehlen
```

`manage.py check --deploy` läuft bei jeder Installation mit (Schritt 6/8,
`deploy/install.sh:266`) und meldet Sicherheitswarnungen — bricht die
Installation aber nicht ab (`warn`, nicht `die`), die Ausgabe muss also gelesen
werden.

## 6. `.env.example` als Vorlage — mit Namensrest aus der Umbenennung

Die Vorlage `.env.example` im Repo-Wurzelverzeichnis zeigt alle gängigen
Variablen mit Beispielwerten. Sie stammt aus der Zeit vor der Umbenennung von
MPP zu CMP und trägt noch den alten Projektnamen in Kommentaren und
Platzhalter-Hostnamen (`.env.example:1,17`) — inhaltlich (Variablennamen,
Defaults) ist sie weiterhin gültig, nur die Beispielwerte sind nicht
nachgezogen.

## 7. Zusammenfassung

Produktions-Settings kommen vollständig aus der Umgebung, injiziert über
systemd `EnvironmentFile=`. Zwei Variablen sind echte Pflichtwerte
(`SECRET_KEY`, `DATABASE_URL`) und lassen Django ohne sie gar nicht erst
starten; `ALLOWED_HOSTS` hat einen stillen Leerlisten-Default und scheitert erst
beim ersten Request. `DEBUG=True` in Produktion bleibt verboten — abgesichert
durch einen sicheren Default, nicht durch eine Laufzeitsperre gegen bewusstes
Setzen.

> Quelle: cmp/config/settings/production.py, cmp/config/settings/base.py, .env.example, deploy/install.sh, CLAUDE.md — am Code geprüft 2026-07-22
