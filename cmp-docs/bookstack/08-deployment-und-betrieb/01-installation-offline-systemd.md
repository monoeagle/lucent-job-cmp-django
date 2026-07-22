# Installation — Offline/systemd auf AlmaLinux 9

Wie CMP auf einer produktiven VM landet: nativ per systemd, ohne Container, ohne
Internetzugang auf der Ziel-VM. Dieses Kapitel beschreibt den Installer
`deploy/install.sh` Schritt für Schritt, so wie er im Skript selbst steht.

## 1. Ziel des Kapitels

Wer eine neue VM aufsetzt oder einen bestehenden Lauf nachvollziehen will, findet
hier die acht Installationsschritte in der Reihenfolge, in der `install.sh` sie
tatsächlich ausführt — nicht eine Zielarchitektur-Beschreibung, sondern den
Ablauf des Skripts selbst.

## 2. Voraussetzung: Offline-Bundle + vorinstallierte System-Pakete

Der Installer bringt **keine** Betriebssystem-Pakete mit, nur die Python-Wheels
der Anwendung. Auf der Ziel-VM müssen vorher installiert sein: `python3.12`,
`postgresql16-server`, `redis`, `nginx`, `openssl` (`docs/deployment/vm-installation-offline.md:128-135`).
Fehlt eines davon, bricht der `preflight()`-Schritt kontrolliert ab, bevor
irgendetwas geschrieben wird (`deploy/install.sh:134-176`).

Das Bundle selbst muss `cmp/` (App-Code), `wheels/` (Python-Wheels) und
`requirements/production.txt` enthalten — der Preflight prüft das zuerst
(`deploy/install.sh:136-138`).

## 3. Aufruf

```bash
sudo ./deploy/install.sh                 # Prüfbereich + Menü (nur am Terminal)
sudo ./deploy/install.sh --install       # direkt installieren, ohne Menü
sudo ./deploy/install.sh --check         # nur prüfen, ändert nichts
sudo ./deploy/install.sh --restart       # Dienste neu starten
```

`--check` liefert Exit 0 nur, wenn jede Prüfzeile grün ist — jeder `fail`/`warn`/
`unknown` ergibt Exit 1, das Kommando taugt damit als Health-Check für Cron oder
Monitoring (`deploy/install.sh:113-124`). Läuft das Skript ohne Terminal (Pipe,
CI, `ssh host './install.sh'`), erscheint kein Menü — es installiert direkt
(`deploy/install.sh:356-359`).

## 4. Die acht Installationsschritte

Quelle: `deploy/install.sh:179-327` (Funktion `aktion_installieren`).

| Schritt | Kopfzeile im Skript | Was passiert |
|---|---|---|
| 1/8 | Konfiguration (`install.sh:183`) | FQDN und DB-Passwort abfragen; bestehenden `SECRET_KEY` übernehmen oder neu erzeugen; TLS-Modus aus Zertifikatslage ableiten |
| 2/8 | Service-User + App-Code (`install.sh:212`) | System-User `cmp` anlegen; `cmp/`, `requirements/`, `wheels/` nach `/opt/cmp` **spiegeln** |
| 3/8 | venv + Wheels offline (`install.sh:227`) | `python3.12 -m venv`, danach `pip install --no-index --find-links=…/wheels` |
| 4/8 | PostgreSQL-Datenbank (`install.sh:235`) | Rolle `cmp` und Datenbank `cmp_prod` anlegen bzw. Passwort aktualisieren |
| 5/8 | Umgebungsdatei (`install.sh:242`) | `/etc/cmp/cmp.env` schreiben (`DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, `CELERY_BROKER_URL` + modusabhängige Security-Zeilen) |
| 6/8 | Migrationen, Static, Superuser (`install.sh:258`) | `manage.py check --deploy`, `migrate`, `collectstatic`, `createsuperuser` (nur wenn noch keiner existiert) |
| 7/8 | systemd (`install.sh:280`) | `cmp-web.service` + `cmp-celery.service` rendern und **neu starten** |
| 8/8 | nginx + TLS (`install.sh:293`) | nginx-Conf rendern, `nginx -t`, SELinux-Booleans/Kontext, firewalld |

Details zu Schritt 8 (TLS-Modus, Ports, SELinux, firewalld) siehe Kapitel 8.3.
Details zur Provisioning-Kette (was Schritt 7 bei Celery real anschließt) siehe
Kapitel 8.4.

## 5. Wiederholbarkeit (Idempotenz)

Ein zweiter Lauf über einer bestehenden Installation soll dieselbe Installation
aktualisieren, nicht duplizieren. Drei Mechanismen sichern das:

- **`SECRET_KEY` bleibt erhalten:** `cmp_secret_key()` liest den bestehenden Wert
  aus `/etc/cmp/cmp.env`, bevor ein neuer erzeugt wird — ein neuer Key würde bei
  jedem Re-Run alle Sessions und Passwort-Reset-Tokens entwerten
  (`deploy/lib.sh:42-54`).
- **App-Ordner wird gespiegelt, nicht gemerged:** `cmp_sync_app()` löscht das Ziel
  vor dem Kopieren (`rm -rf` + `cp -a`) — ein im neuen Release gelöschtes Modul
  oder eine alte Migration bleibt sonst auf der VM liegen (`deploy/lib.sh:56-74`).
- **Dienste werden neu gestartet, nicht nur aktiviert:** `cmp_restart_services()`
  ruft `systemctl restart`, nicht nur `enable --now` — Letzteres wäre bei einer
  bereits laufenden Unit ein No-Op, nach einem Upgrade liefe sonst der alte Code
  weiter (`deploy/lib.sh:270-278`).

Rolle und Datenbank werden in Schritt 4 **getrennt** geprüft — ein Wiederanlauf
nach einem Teilfehler (Rolle vorhanden, DB fehlt) legt die Datenbank sonst nie an
(`deploy/lib.sh:218-236`).

## 6. PostgreSQL-Variante wird erkannt, nicht angenommen

PGDG- und AppStream-Pakete unterscheiden sich in Service-Name und Binärpfad:
PGDG legt `psql` unter `/usr/pgsql-16/bin/` ab (nicht im `PATH`) und nennt den
Dienst `postgresql-16.service`; AppStream nutzt `/usr/bin/psql` und
`postgresql.service`. `cmp_pg_flavor()` erkennt anhand vorhandener Binärpfade,
welche Variante installiert ist, und `cmp_pg_service()`/`cmp_psql_bin()` leiten
Service-Name und Pfad daraus ab (`deploy/lib.sh:76-118`). Findet der Preflight
keine der beiden Varianten, bricht die Installation ab (`deploy/install.sh:154-156`).

## 7. Optionale Online-Kürzel

Zwei Flags lockern die Offline-Grundregel bewusst nur auf Wunsch:

- `--with-packages` installiert PGDG-Repo, EPEL und die System-Pakete aus dem
  Netz, statt sie vorauszusetzen (`deploy/install.sh:140-147`, `deploy/lib.sh:147-159`).
- `--skip-nginx` überspringt Reverse-Proxy und TLS komplett — das Portal ist dann
  ausschließlich auf `127.0.0.1:8001` erreichbar, ohne Zugriff von außen
  (`deploy/install.sh:169-174`, `:294-295`).

Fehlt Redis und liegt kein `redis*.rpm` im Bundle-Ordner `rpms/`, bricht die
Installation ab statt später am Broker zu scheitern (`deploy/lib.sh:245-268`).

## 8. Zusammenfassung

`install.sh` installiert CMP in acht nachvollziehbaren, wiederholbar ausführbaren
Schritten vollständig offline: venv + Wheels ohne PyPI-Zugriff, PostgreSQL-Rolle
und -Datenbank, Umgebungsdatei, Migrationen, systemd-Units und optional nginx/TLS.
Drei Mechanismen — `SECRET_KEY`-Wiederverwendung, Spiegeln statt Mergen,
`restart` statt `enable --now` — machen einen zweiten Lauf zu einem Update statt
einer Dopplung. Die PostgreSQL-Variante (PGDG oder AppStream) wird zur Laufzeit
erkannt, nicht angenommen.

> Quelle: deploy/install.sh, deploy/lib.sh, docs/deployment/vm-installation-offline.md — am Code geprüft 2026-07-22
