# Troubleshooting

Symptom → Ursache → Prüfbefehl, für die produktive systemd-Installation. Die
vorhandene Fehlersuche-Seite `cmp-docs/docs/betrieb/troubleshooting.md` ist
größtenteils für die **lokale Entwicklungsumgebung** geschrieben (Port 8000,
`cmp_django_dev`, Node/Tailwind) — dieses Kapitel übernimmt nur, was für den
Produktivbetrieb zutrifft, und prüft jeden Befehl gegen die echten Dienst- und
Pfadnamen aus `deploy/lib.sh`.

## 1. Ziel des Kapitels

Wer nach der Installation ein konkretes Symptom sieht — 502, 403, ein
verweigerter Login, ein hängender Provisioning-Task — soll hier die
wahrscheinlichste Ursache und den passenden Prüfbefehl finden, ohne die
gesamte Installation neu durchzugehen.

## 2. Web-Zugriff

| Symptom | Wahrscheinliche Ursache | Prüfbefehl |
|---|---|---|
| `502 Bad Gateway` | gunicorn (`cmp-web`) läuft nicht, oder SELinux blockiert die Verbindung zu Port 8001 | `systemctl status cmp-web --no-pager`; `sudo ausearch -m avc -ts recent` |
| `403` auf `/static/…` | falscher SELinux-Kontext auf `staticfiles/`, oder `collectstatic` nicht gelaufen | `restorecon -Rv /opt/cmp/app/cmp/staticfiles`; danach neu laden |
| `DisallowedHost` (HTTP 400) | FQDN fehlt in `ALLOWED_HOSTS`, oder Zugriff per IP statt FQDN | `grep ALLOWED_HOSTS /etc/cmp/cmp.env`; Zugriff exakt über den FQDN wiederholen (Kapitel 2.3, Abschnitt 6) |
| `CSRF verification failed` | Origin fehlt in `CSRF_TRUSTED_ORIGINS`, oder ohne Schema (`http://`/`https://`) eingetragen | `grep CSRF_TRUSTED_ORIGINS /etc/cmp/cmp.env` |
| Zertifikatswarnung im Browser trotz HTTPS-Modus | self-signed/interne CA nicht im Trust-Store des Clients, oder SAN passt nicht zum FQDN | Zertifikat manuell in den Client-Trust-Store importieren (Kapitel 8.3, Abschnitt 7) |
| Portal von außen nicht erreichbar, `127.0.0.1:8001` lokal aber ok | nginx fehlte bei der Installation, firewalld blockt, oder Zugriff per IP | `sudo ss -tlnp \| grep -E ':(80\|443\|8001)'`; `sudo firewall-cmd --list-all`; `curl -I http://<fqdn>/` |

## 3. Dienste und Prozesse

| Symptom | Wahrscheinliche Ursache | Prüfbefehl |
|---|---|---|
| `cmp-web` startet nicht: `ModuleNotFoundError: config` | `WorkingDirectory` der Unit zeigt nicht auf `/opt/cmp/app/cmp` (dort liegt `manage.py` und das Paket `config`) | `systemctl cat cmp-web \| grep WorkingDirectory` — erwartet `/opt/cmp/app/cmp` (`deploy/lib.sh:173`) |
| `psycopg.OperationalError` | DB-Passwort in `DATABASE_URL` falsch, oder `pg_hba.conf` erzwingt nicht `scram-sha-256` für `127.0.0.1` | `grep DATABASE_URL /etc/cmp/cmp.env`; `sudo -u postgres psql -c "\du"` |
| Rolle/Datenbank fehlen nach einem Fehlstart | Installation zwischen Schritt 4/8 und 5/8 abgebrochen | `sudo ./deploy/install.sh --check` erneut ausführen — Rolle und DB werden getrennt geprüft und nachgezogen (`deploy/lib.sh:218-236`) |

## 4. Provisioning-Kette (Celery)

| Symptom | Wahrscheinliche Ursache | Prüfbefehl |
|---|---|---|
| Bestellung bleibt in `APPROVED`, kein Provisioning startet | Erwartetes Verhalten heute — die Genehmigungs-View löst `dispatch_provisioning` noch nicht automatisch aus (Kapitel 8.4, AP-13); kein Fehler, sondern die bekannte Lücke | `todo.md`, Abschnitt AP-13 gegenlesen, bevor an der Celery-Konfiguration gesucht wird |
| Task hängt, obwohl er ausgelöst wurde | `cmp-celery` läuft nicht, oder Redis nicht erreichbar | `systemctl status cmp-celery --no-pager`; `redis-cli ping` |
| `redis.exceptions.ConnectionError` | Redis-Dienst nicht aktiv, oder `CELERY_BROKER_URL` zeigt auf einen falschen Host | `systemctl is-active redis`; `grep CELERY_BROKER_URL /etc/cmp/cmp.env` |

## 5. TLS-Redirect-Schleife

**Symptom:** Der Browser läuft in eine Endlos-Weiterleitung zwischen HTTP und
HTTPS.

**Ursache:** `SECURE_PROXY_SSL_HEADER` in `production.py:56` vertraut dem
`X-Forwarded-Proto`-Header von nginx — setzt die nginx-Konfiguration diesen
Header nicht, hält Django jede Anfrage für unverschlüsselt und leitet erneut um.

```bash
grep -A2 'location /' /etc/nginx/conf.d/cmp.conf | grep X-Forwarded-Proto
```

Fehlt die Zeile `proxy_set_header X-Forwarded-Proto $scheme;`, wurde die
nginx-Konfiguration außerhalb von `install.sh` von Hand verändert — ein
erneuter, unveränderter Lauf von `install.sh` stellt die vom Installer
gerenderte Fassung wieder her.

## 6. Der Prüfbereich selbst als erster Schritt

Bevor einzelne Befehle aus den Tabellen oben einzeln nachvollzogen werden,
liefert der eingebaute Prüfbereich meist schneller eine Übersicht:

```bash
sudo ./deploy/install.sh --check
```

Jede rot markierte Zeile (`fail`/`warn`/`unknown`) verweist auf genau die
Komponente, bei der sich die weitere Suche lohnt — der Befehl ändert nichts an
der Installation (`deploy/install.sh:113-124`).

## 7. Was aus der Entwicklungs-Fehlersuche bewusst nicht übernommen wurde

`cmp-docs/docs/betrieb/troubleshooting.md` beschreibt zusätzlich
Node.js-/Tailwind-Buildfehler, Port 8000 (`runserver`), `cmp_django_dev` und
Dev-Testuser — das sind Symptome der lokalen Entwicklungsumgebung
(`config.settings.development`), die in einer systemd-Installation ohne
`runserver` und ohne Frontend-Build nicht auftreten. Sie wurden hier bewusst
weggelassen, statt unpassend auf die Produktionsumgebung übertragen zu werden.

## 8. Zusammenfassung

Die meisten Produktionsprobleme lassen sich einer von vier Ursachen zuordnen:
ein gestoppter Dienst (`cmp-web`, `cmp-celery`, `redis`, `postgresql-16`), eine
fehlende Umgebungsvariable in `/etc/cmp/cmp.env` (`ALLOWED_HOSTS`,
`CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`), ein SELinux-/firewalld-Zustand, der
nicht zum gewählten TLS-Modus passt, oder — bei der Provisioning-Kette — die
bekannte, noch offene Verdrahtungslücke aus AP-13. `install.sh --check` ist der
schnellste erste Schritt, weil er alle vier Bereiche in einem Lauf zeigt.

> Quelle: docs/deployment/vm-installation.md, docs/deployment/vm-installation-offline.md, cmp-docs/docs/betrieb/troubleshooting.md, deploy/install.sh, deploy/lib.sh, cmp/config/settings/production.py, todo.md (AP-13) — am Code geprüft 2026-07-22
