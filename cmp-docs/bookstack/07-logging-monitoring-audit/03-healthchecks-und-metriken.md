# Healthchecks und Metriken

CMP hat keinen HTTP-Health-Endpoint und keinen Metriken-Stack. Diese Seite
belegt das per `grep` und beschreibt, was stattdessen an Status-Signalen
existiert: der Installer-Prüfbereich und systemd/journald.

## 1. Ziel des Kapitels

Wer nach einem `/health`- oder `/readiness`-Endpoint sucht, um CMP in ein
Monitoring einzubinden, findet hier den Befund: Es gibt keinen. Die Seite
zeigt, was stattdessen als Status-Quelle zur Verfügung steht — der
Installer-Prüfbereich (`--check`) und `systemd`/`journald` — und warum das so
bewusst entschieden ist.

## 2. Kein HTTP-Health-Endpoint

Suche über den gesamten Anwendungscode, Stand 2026-07-22:

```
grep -rniE "health|readiness|healthz|/ready" cmp/ --include=*.py
```

Ergebnis: **0 Treffer.** `cmp/config/urls.py` (die einzige URL-Konfiguration
oberster Ebene, `find cmp -maxdepth 2 -iname urls.py` findet nur diese eine
Datei) registriert keine Health-Route. Es existiert also kein Endpoint, den
ein externer Monitoring-Client (Kubernetes-Probe, Load-Balancer-Check,
Uptime-Monitoring) abfragen könnte.

## 3. Bewusste Entscheidung gegen einen externen Monitoring-Stack

Das ist keine übersehene Lücke, sondern eine getroffene Entscheidung für das
Zielbild: Eine air-gapped Single-VM-Installation ohne externen
Monitoring-Stack. `requirements.txt` enthält entsprechend kein
Monitoring-Paket:

```
grep -inE "sentry|prometheus|django-health|healthcheck" requirements.txt
```

Ergebnis: 0 Treffer. Die Betriebssicht beschränkt sich stattdessen auf den
Installer-Prüfbereich (Abschnitt 4) und manuelle Prüfbefehle über
`journalctl`/`systemctl` (Abschnitt 5).

## 4. Der Installer-Prüfbereich als Ersatz

`deploy/install.sh` bringt einen Prüfbereich mit, der als einfacher
Health-Check für Cron/Monitoring taugt — kommentiert direkt im Code
(`deploy/install.sh:114-115`):

> „Exit 0 nur, wenn alles grün ist — damit taugt `--check` als Health-Check
> für Monitoring/Cron. Jedes warn/fail/unknown ergibt Exit 1."

Aufruf: `sudo ./deploy/install.sh --check`. Die Funktion `status_sammeln()`
(`deploy/install.sh:93-105`) reiht folgende Einzelprüfungen aneinander:

| Prüfung | Funktion | Datei:Zeile |
|---|---|---|
| Python-Version | `cmp_status_python` | `deploy/ui.sh` |
| PostgreSQL | `cmp_status_postgres` | `deploy/ui.sh` |
| Redis | `cmp_status_redis` | `deploy/ui.sh` |
| nginx | `cmp_status_nginx` | `deploy/ui.sh` |
| App-Verzeichnis + Version | `cmp_status_app` | `deploy/ui.sh:190-198` |
| Datenbank vorhanden | `cmp_status_database` | `deploy/ui.sh:202-215` |
| Dienst `cmp-web` aktiv | `cmp_status_service cmp-web` | `deploy/ui.sh:177-184` |
| Dienst `cmp-celery` aktiv | `cmp_status_service cmp-celery` | `deploy/ui.sh:177-184` |
| Links/Ports konsistent | `cmp_status_links` | `deploy/ui.sh` |

`cmp_status_service()` (`deploy/ui.sh:177-184`) prüft dabei ausschließlich
`systemctl is-active --quiet <unit>` — kein HTTP-Request, kein Applikations-
Ping, nur der systemd-Dienststatus. `aktion_pruefen()` (`deploy/install.sh:116-123`)
sammelt alle Zeilen und gibt Exit 1 zurück, sobald eine Zeile mit
`fail`, `warn` oder `unknown` beginnt — das macht `--check` cron-tauglich,
ohne dass die Anwendung selbst einen Health-Endpoint braucht.

## 5. Was systemd/journald zusätzlich hergibt

Die beiden Unit-Dateien werden nicht als statische Dateien im Repo gepflegt,
sondern zur Installationszeit gerendert
(`cmp_render_web_unit`, `deploy/lib.sh:162-188`; `cmp_render_celery_unit`,
`deploy/lib.sh:191-215`). Relevant für Logging/Status:

| Unit | `ExecStart` | Datei:Zeile |
|---|---|---|
| `cmp-web` | `gunicorn config.wsgi:application --bind 127.0.0.1:8001 --workers 3 --timeout 60 --access-logfile - --error-logfile -` | `deploy/lib.sh:177` |
| `cmp-celery` | `celery -A config worker --loglevel=info --concurrency=2` | `deploy/lib.sh:205` |

`--access-logfile -`/`--error-logfile -` leiten gunicorns Zugriffs- und
Fehlerprotokoll auf stdout/stderr um — ohne eigenes `StandardOutput=` in der
Unit landet das damit im systemd-Journal der jeweiligen Unit. Celery loggt
mit `--loglevel=info` ebenfalls nach stdout/journal. Damit ergeben sich zwei
Kommandos als manuelle Statusquelle:

```bash
sudo journalctl -u cmp-web -f
sudo journalctl -u cmp-celery -f
```

Diese beiden Zeilen stehen auch in der VM-Installationsanleitung, Abschnitt
„17. Betrieb: Logs, Backups, Health" (`docs/deployment/vm-installation.md:530-537`).
Dieselbe Anleitung listet zusätzlich eine Tabelle manueller
Health-Indikatoren (`docs/deployment/vm-installation.md:546-554`):
`systemctl is-active cmp-web`/`cmp-celery`, `psql "$DATABASE_URL" -c 'SELECT 1'`,
`redis-cli ping`, `manage.py migrate --check` — alles Einzelbefehle zum
manuellen Ausführen, kein automatisierter Health-Endpoint und kein
Dashboard.

## 6. Zusammenfassung

CMP hat keinen HTTP-Health- oder Readiness-Endpoint und keinen
Metriken-/APM-Stack — beides ist bewusst nicht Teil des Zielbilds einer
air-gapped Single-VM-Installation. An dessen Stelle steht der
Installer-Prüfbereich (`--check`), der über `systemctl is-active` je Dienst
prüft und cron-tauglich mit Exit-Code antwortet, ergänzt um
gunicorn-/Celery-Logs im systemd-Journal und eine Handvoll manueller
Prüfbefehle aus der VM-Installationsanleitung. Ein automatisiertes,
zentrales Monitoring existiert nicht.

> Quelle: cmp/config/urls.py, requirements.txt, deploy/install.sh, deploy/lib.sh, deploy/ui.sh, docs/deployment/vm-installation.md — am Code geprüft 2026-07-22
