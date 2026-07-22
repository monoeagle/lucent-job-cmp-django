# Nicht-funktionale Anforderungen

Dieses Kapitel beschreibt die Qualitätsanforderungen an CMP — Authentifizierung/
Autorisierung, Logging/Monitoring, Backup/Update und Betrieb — mit Status und
Code-/Doku-Beleg.

## 1. Ziel des Kapitels

Wer wissen will, wie CMP mit Sicherheit, Nachvollziehbarkeit und Betriebsfähigkeit
umgeht, findet hier den geprüften Ist-Stand statt einer Behauptung. Die IDs in diesem
Kapitel (`NFR_*`) sind ein eigenes Schema für dieses Handbuch — die Gap-Analyse
(`analyse/analyse-bestellportal.md`) definiert `FK_*` ausschließlich für optionale
**funktionale** Anforderungen (siehe Kapitel 3, Abschnitt 8), nicht für Qualitäts-
attribute. Um Verwechslung zu vermeiden, führt dieses Kapitel eine eigene Zählung ein.

## 2. Legende

| Symbol | Bedeutung |
|---|---|
| ✅ | Umgesetzt und dokumentiert |
| 🟡 | Teilweise umgesetzt oder nur als Empfehlung dokumentiert, nicht automatisiert |
| ❌ | Nicht umgesetzt |

## 3. Authentifizierung und Autorisierung (NFR_AUTH01–05)

| ID | Anforderung | Status | Beleg |
|---|---|---|---|
| NFR_AUTH01 | Session-basierte Authentifizierung | ✅ | django-allauth, `AUTHENTICATION_BACKENDS` (`cmp/config/settings/base.py:93-96`) |
| NFR_AUTH02 | Kein offenes Self-Signup | ✅ | `ACCOUNT_SIGNUP_ENABLED = False` (`cmp/config/settings/base.py:99`) — Benutzer werden ausschließlich von einem Admin angelegt |
| NFR_AUTH03 | Rollenbasierte Zugriffskontrolle | ✅ | Vier Rollen, vier Mixins mit `required_roles`-Prüfung (`cmp/core/mixins.py:22-94`, siehe Kapitel 2) |
| NFR_AUTH04 | Sichere Cookies/TLS-Redirect in Produktion | ✅ | `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT` per Default `True`, aus der Umgebung überschreibbar (`cmp/config/settings/production.py:18-29,57-60`); `SECRET_KEY` ohne Default → Fehlstart, wenn nicht gesetzt (`cmp/config/settings/production.py:39`) |
| NFR_AUTH05 | CSP-Header / Rate Limiting gegen Brute-Force | ❌ | Kein `django-csp`, kein Rate-Limiting-Paket in `requirements.txt`; kein `Content-Security-Policy`-Header im Code (`grep -rn "Content-Security-Policy\|ratelimit" cmp/ requirements.txt` ohne Treffer). Offenes Arbeitspaket AP-19 (`todo.md`) |

Active-Directory-Anbindung ist eine funktionale, keine Qualitätsanforderung — siehe
FM_BA07 in Kapitel 3, Abschnitt 6 (❌, kein `django-auth-ldap`).

## 4. Logging und Monitoring (NFR_LOG01–03)

| ID | Anforderung | Status | Beleg |
|---|---|---|---|
| NFR_LOG01 | Anwendungs-Logging (`LOGGING`-Konfiguration) | ❌ | Keine `LOGGING`-Einstellung in `cmp/config/settings/*.py`, kein `getLogger(__name__)` im gesamten Anwendungscode (`grep -rn "LOGGING\|getLogger" cmp/config cmp/apps cmp/core` ohne Treffer). Offenes Arbeitspaket AP-14 (`todo.md`) |
| NFR_LOG02 | Revisionssicheres Audit-Log für Bestellungen/Genehmigungen/Provisioning | 🟡 | Modell und Export vollständig (`AuditLog`, `cmp/apps/audit/models.py`; `AuditLogExportView`, `cmp/apps/audit/views.py:32`), `AuditService.log` wird aber im laufenden Betrieb nirgends aufgerufen — nur `seed.py` (7×). Eine über die Oberfläche ausgelöste Genehmigung erzeugt aktuell **keinen** Audit-Eintrag (`analyse/analyse-bestellportal.md`, Abschnitt 1c) |
| NFR_LOG03 | Infrastruktur-Monitoring (Prometheus/Grafana/Sentry o.ä.) | ❌ | Bewusst nicht vorgesehen — Zielbild ist eine air-gapped Single-VM-Installation ohne externen Monitoring-Stack (`analyse/analyse-bestellportal.md`, Abschnitt 1d). Betriebssicht beschränkt sich auf `journalctl` und manuelle Health-Checks (`docs/deployment/vm-installation.md`, Abschnitt 17) |

Prozess-Logs (gunicorn, Celery) laufen nach `journald` und sind damit vorhanden
(`sudo journalctl -u cmp-web -f`, `docs/deployment/vm-installation.md:531-535`) — das
ist Betriebssystem-Logging, kein strukturiertes Anwendungs-Logging im Sinne von
NFR_LOG01.

## 5. Backup und Update (NFR_BACKUP01–03)

| ID | Anforderung | Status | Beleg |
|---|---|---|---|
| NFR_BACKUP01 | Dokumentiertes Datenbank-Backup | 🟡 | Als Empfehlung dokumentiert (`sudo -u postgres pg_dump -Fc cmp_prod > ...`, `docs/deployment/vm-installation.md:540-544`), aber nicht Teil des Installers — kein automatisierter Cron-/Timer-Job wird eingerichtet. Sicherheits-Checkliste führt es als manuell abzuhakenden Punkt (`docs/deployment/vm-installation.md:588`) |
| NFR_BACKUP02 | Wiederholbares Update-Verfahren | 🟡 | `deploy/install.sh` ist erneut ausführbar und startet `cmp-web`/`cmp-celery` beim erneuten Lauf mit aktuellem Code neu (`deploy/install.sh:284-289`, Kommentar: „`restart` statt `enable --now` … nach einem Upgrade liefe sonst der alte Code weiter"). Es gibt aber **kein separates** Update-Kommando, und die Idempotenz ist bisher nicht durch einen Test belegt — offenes Arbeitspaket AP-17 (`todo.md`) |
| NFR_BACKUP03 | Abräumzweig (Uninstall/Purge) | ❌ | Kein `uninstall`/`purge`-Pfad in `deploy/install.sh` (`grep -in "uninstall\|purge" deploy/install.sh` ohne Treffer). Offenes Arbeitspaket AP-16 (`todo.md`) |

## 6. Betrieb (NFR_BETRIEB01–04)

| ID | Anforderung | Status | Beleg |
|---|---|---|---|
| NFR_BETRIEB01 | Konfiguration ohne hardcodierte Secrets | ✅ | Produktions-Settings laden alle sicherheitsrelevanten Werte über `django-environ` aus der Umgebung, kein Secret im Code (`cmp/config/settings/production.py:1-11,16-28`) |
| NFR_BETRIEB02 | `DEBUG=True` in Produktion ausgeschlossen | ✅ | `DEBUG = env("DEBUG")` mit Default `False` (`cmp/config/settings/production.py:19,38`); als FATAL-Regel auch in `CLAUDE.md` festgehalten |
| NFR_BETRIEB03 | Nativer Betrieb ohne Container (Single-VM) | ✅ | systemd-Units für `cmp-web` (gunicorn/WSGI) und `cmp-celery`, dahinter nginx als TLS-Terminierung (`cmp-docs/docs/betrieb/laufzeit-topologie.md`, Abschnitt „Wer macht was"); Container-Variante ist optionales, separates Arbeitspaket AP-11 |
| NFR_BETRIEB04 | Asynchrone Provisioning-Tasks blockieren keinen Request | ✅ | Celery + Redis als Broker/Result-Backend, View legt Task ab und antwortet sofort (`cmp-docs/docs/betrieb/laufzeit-topologie.md`, Abschnitt „Celery — die lange Arbeit"); `CELERY_TASK_ALWAYS_EAGER = False` in Produktion (`cmp/config/settings/production.py:49`) |

**Korrektur gegenüber `cmp-docs/docs/grundlagen/ueberblick.md`:** Die dortige Angabe
„Server | ASGI (Daphne/Uvicorn)" ist am aktuellen Code nicht (mehr) zutreffend. Produktiv
läuft CMP über **gunicorn/WSGI**, nicht ASGI: `WSGI_APPLICATION = "config.wsgi.application"`
(`cmp/config/settings/base.py:66`), keine `ASGI_APPLICATION`-Einstellung, kein
`channels` in `requirements.txt`, und `deploy/install.sh` installiert/startet
ausschließlich gunicorn (`deploy/install.sh:231,280`). Django Channels ist geplant, aber
noch nicht eingebaut (AP-12, `CLAUDE.md`) — bis dahin ist der Server WSGI, nicht ASGI.

## 7. Teststrategie als Qualitätssicherung

TDD ist projektweit Pflicht (`.claude/rules/testing.md`). Stand 2026-07-22 zählt die
Testsuite **347 Tests** (`pytest --collect-only`, Projektwurzel). Externe Abhängigkeiten
(GitLab-Pipeline, CMDB) sind über Stub-Clients ersetzt, keine echten Netzwerkaufrufe in
Tests (`cmp/apps/provisioning/clients.py`, `cmp-docs/docs/betrieb/stubs-mocks.md`).

## 8. Zusammenfassung

Authentifizierung und Autorisierung sind solide umgesetzt (Session-Auth, vier
hierarchische Rollen, sichere Cookie-Defaults in Produktion) — offen sind CSP und
Rate-Limiting (AP-19). Logging ist die größte Lücke: weder strukturiertes Anwendungs-
Logging noch ein im Betrieb tatsächlich befülltes Audit-Log (AP-14, Abhängigkeit von
AP-13). Backup ist dokumentiert, aber nicht automatisiert; ein Abräumzweig für die
Installation fehlt vollständig (AP-16, AP-17). Der Betrieb selbst — native
systemd-Installation mit gunicorn, nginx, Celery, Redis, PostgreSQL, Secrets über
`django-environ` — ist sauber umgesetzt und dokumentiert.

> Quelle: cmp/config/settings/base.py, cmp/config/settings/production.py, cmp/core/mixins.py, cmp/apps/audit/, deploy/install.sh, docs/deployment/vm-installation.md, cmp-docs/docs/betrieb/laufzeit-topologie.md, analyse/analyse-bestellportal.md, todo.md (AP-13, AP-14, AP-16, AP-17, AP-19), CLAUDE.md — am Code geprüft 2026-07-22
