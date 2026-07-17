# VM-Installation — CMP Django (Produktion)

Schritt-für-Schritt-Anleitung, um das **CloudMan Portal (CMP Django)**
dezidiert auf einer frischen **Rocky Linux 9 / AlmaLinux 9**-VM in einer
**produktionssicheren** Konfiguration zu installieren:

```
Internet ──TLS──▶ nginx (80/443) ──HTTP──▶ gunicorn (127.0.0.1:8001) ──▶ Django (WSGI)
                     │                                                      │
                     └─ /static/ (collectstatic)            ┌───────────────┤
                                                            ▼               ▼
                                                       PostgreSQL 16     Redis 7
                                                            ▲               ▲
                                                            └── Celery-Worker (systemd)
```

> **Zielbild:** dedizierter Service-User, env-basierte Settings
> (`config.settings.production`), gunicorn + Celery als systemd-Units, nginx als
> TLS-terminierender Reverse-Proxy, SELinux *enforcing*, firewalld aktiv.

> **Ohne Internetzugang auf der VM?** Siehe die air-gapped Variante
> [`vm-installation-offline.md`](vm-installation-offline.md) — alle Quellen werden
> auf einem Staging-Host eingesammelt und als Bundle auf die VM transportiert.

---

## Inhalt

1. [Voraussetzungen](#1-voraussetzungen)
2. [VM-Grundkonfiguration](#2-vm-grundkonfiguration)
3. [System-Pakete](#3-system-pakete-python-312-build-tools-nginx)
4. [PostgreSQL 16](#4-postgresql-16)
5. [Redis](#5-redis)
6. [Service-User & Verzeichnisse](#6-service-user--verzeichnisse)
7. [Code, venv & Abhängigkeiten](#7-code-venv--abhängigkeiten)
8. [Umgebungsdatei (Secrets)](#8-umgebungsdatei-secrets)
9. [Migrationen, Static Files, Admin-User](#9-migrationen-static-files-admin-user)
10. [gunicorn als systemd-Service](#10-gunicorn-als-systemd-service)
11. [Celery-Worker als systemd-Service](#11-celery-worker-als-systemd-service)
12. [nginx Reverse-Proxy](#12-nginx-reverse-proxy)
13. [SELinux & firewalld](#13-selinux--firewalld)
14. [TLS mit Let's Encrypt](#14-tls-mit-lets-encrypt)
15. [Verifikation (Smoke-Test)](#15-verifikation-smoke-test)
16. [Updates & Re-Deploy](#16-updates--re-deploy)
17. [Betrieb: Logs, Backups, Health](#17-betrieb-logs-backups-health)
18. [Troubleshooting](#18-troubleshooting)
19. [Sicherheits-Checkliste](#19-sicherheits-checkliste)

---

## 1. Voraussetzungen

| Komponente | Version / Wert |
|---|---|
| OS | Rocky Linux 9 oder AlmaLinux 9 (x86_64), frisch installiert |
| RAM | min. 2 GB (4 GB empfohlen) |
| Python | **3.12** (Django 6.0 erfordert ≥ 3.12) |
| PostgreSQL | 16 (PGDG-Repo) |
| Redis | 7 (AppStream) |
| Zugang | sudo-fähiger User, SSH |
| DNS | A-Record `cmp.example.com` → öffentliche IP der VM (für TLS) |

In dieser Anleitung verwendete Platzhalter — überall konsequent ersetzen:

| Platzhalter | Beispiel |
|---|---|
| `cmp.example.com` | euer FQDN |
| `/opt/cmp` | Installationswurzel |
| DB-Name / -User / -Passwort | `cmp_prod` / `cmp` / `<DB-PASSWORT>` |

> **Konvention:** Befehle mit `sudo` laufen als Admin. Befehle nach
> `sudo -iu cmp` laufen als **Service-User** `cmp` (siehe Schritt 6).

---

## 2. VM-Grundkonfiguration

```bash
# System aktuell halten
sudo dnf -y upgrade --refresh

# Basis-Werkzeuge
sudo dnf -y install vim git curl policycoreutils-python-utils

# Hostname & Zeitzone (Projekt nutzt Europe/Berlin)
sudo hostnamectl set-hostname cmp.example.com
sudo timedatectl set-timezone Europe/Berlin

# Zeitsynchronisation
sudo systemctl enable --now chronyd
```

---

## 3. System-Pakete (Python 3.12, Build-Tools, nginx)

Rocky/Alma 9 liefert standardmäßig Python 3.9. CMP benötigt **3.12** aus dem
AppStream:

```bash
# Python 3.12 + venv + dev-Header (für psycopg / native Builds)
sudo dnf -y install python3.12 python3.12-devel python3.12-pip

# Compiler & Bibliotheken für native Wheels
sudo dnf -y install gcc make libpq-devel

# nginx
sudo dnf -y install nginx

# Prüfen
python3.12 --version   # erwartet: Python 3.12.x
```

> `libpq-devel` wird nur gebraucht, falls `psycopg[binary]` einmal aus Quelle
> baut. Mit den Binär-Wheels (Default) ist es harmlos vorinstalliert zu haben.

---

## 4. PostgreSQL 16

Das offizielle **PGDG**-Repo liefert PostgreSQL 16 (neuer als der AppStream):

```bash
# PGDG-Repo + AppStream-Modul deaktivieren (sonst Paketkonflikt)
sudo dnf -y install https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm
sudo dnf -qy module disable postgresql

# Server + Client
sudo dnf -y install postgresql16-server postgresql16

# Datencluster initialisieren und Dienst starten
sudo /usr/pgsql-16/bin/postgresql-16-setup initdb
sudo systemctl enable --now postgresql-16
```

Datenbank und Rolle anlegen:

```bash
sudo -u postgres psql <<'SQL'
CREATE ROLE cmp WITH LOGIN PASSWORD '<DB-PASSWORT>';
CREATE DATABASE cmp_prod OWNER cmp ENCODING 'UTF8' LC_COLLATE 'de_DE.UTF-8' LC_CTYPE 'de_DE.UTF-8' TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE cmp_prod TO cmp;
SQL
```

Lokale Passwort-Authentifizierung (`scram-sha-256`) für die App freischalten:

```bash
# In pg_hba.conf für IPv4-localhost scram-sha-256 erzwingen
sudo sed -i 's/^host\s\+all\s\+all\s\+127.0.0.1\/32\s\+ident/host    all             all             127.0.0.1\/32            scram-sha-256/' \
  /var/lib/pgsql/16/data/pg_hba.conf
sudo systemctl restart postgresql-16

# Verbindung testen (Passwort aus obigem CREATE ROLE)
psql "postgres://cmp:<DB-PASSWORT>@127.0.0.1:5432/cmp_prod" -c '\conninfo'
```

> Die VM hält DB, Redis und App auf demselben Host. Liegt PostgreSQL auf einem
> separaten Server, dort `listen_addresses` und `pg_hba.conf` für das App-Netz
> öffnen und in `DATABASE_URL` den richtigen Host eintragen.

---

## 5. Redis

```bash
sudo dnf -y install redis
sudo systemctl enable --now redis

# Absichern: nur lokal lauschen (Default in RHEL 9 bereits 127.0.0.1),
# zur Sicherheit prüfen:
grep -E '^bind' /etc/redis/redis.conf    # sollte 127.0.0.1 enthalten

# Test
redis-cli ping    # -> PONG
```

> Redis bindet hier nur an `127.0.0.1`. Wird Redis von einem anderen Host
> erreicht, zwingend `requirepass` + Firewall setzen und die `redis://`-URL in
> der Umgebungsdatei um das Passwort ergänzen.

---

## 6. Service-User & Verzeichnisse

Die App läuft als **unprivilegierter** System-User ohne Login-Shell:

```bash
# Dedizierter Service-User
sudo useradd --system --create-home --home-dir /opt/cmp --shell /usr/sbin/nologin cmp

# Verzeichnis für die Umgebungsdatei (Secrets)
sudo mkdir -p /etc/cmp

# Laufzeitverzeichnis (Socket/PID) — wird zusätzlich per systemd RuntimeDirectory gepflegt
sudo install -d -o cmp -g cmp /run/cmp
```

---

## 7. Code, venv & Abhängigkeiten

```bash
# Als Service-User arbeiten
sudo -iu cmp

# Repository holen (oder per CI-Artefakt/rsync ausrollen)
git clone <REPO-URL> /opt/cmp/app
cd /opt/cmp/app

# venv mit Python 3.12
python3.12 -m venv /opt/cmp/venv
/opt/cmp/venv/bin/python -m pip install --upgrade pip

# Produktions-Abhängigkeiten (zieht requirements/base.txt + gunicorn)
/opt/cmp/venv/bin/pip install -r requirements/production.txt

# zurück zum Admin
exit
```

Verzeichnis-Layout danach:

```
/opt/cmp/
├── app/                 # Git-Checkout (Repo-Wurzel)
│   ├── cmp/             # Django-Projekt (manage.py, config/, apps/)
│   └── requirements/
└── venv/                # virtualenv (Python 3.12)
/etc/cmp/cmp.env         # Secrets (Schritt 8)
```

> **Pfad-Hinweis:** `manage.py` und das `config`-Paket liegen unter
> `/opt/cmp/app/cmp`. Alle Django-Kommandos laufen daher aus diesem Verzeichnis
> (so findet Python das Top-Level-Paket `config`).

---

## 8. Umgebungsdatei (Secrets)

`config.settings.production` liest alle sensiblen Werte aus der Umgebung
(django-environ). Vorlage ist `.env.example` im Repo.

```bash
# SECRET_KEY erzeugen
/opt/cmp/venv/bin/python -c "import secrets; print(secrets.token_urlsafe(64))"

# Umgebungsdatei aus der Vorlage anlegen
sudo cp /opt/cmp/app/.env.example /etc/cmp/cmp.env
sudo vim /etc/cmp/cmp.env
```

Mindestens setzen — `/etc/cmp/cmp.env`:

```ini
SECRET_KEY=<erzeugter-token>
ALLOWED_HOSTS=cmp.example.com
DATABASE_URL=postgres://cmp:<DB-PASSWORT>@127.0.0.1:5432/cmp_prod
CSRF_TRUSTED_ORIGINS=https://cmp.example.com
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
DEBUG=False
```

Rechte restriktiv setzen (nur root liest, Gruppe cmp liest):

```bash
sudo chown root:cmp /etc/cmp/cmp.env
sudo chmod 640 /etc/cmp/cmp.env
```

> **`DEBUG=True` in Produktion ist FATAL.** Der Default in `production.py` ist
> `False`; setze es niemals auf `True`.

---

## 9. Migrationen, Static Files, Admin-User

Alle Kommandos mit Produktions-Settings und geladener Umgebungsdatei. Praktisch
ist ein Wrapper, der `cmp.env` einliest:

```bash
sudo -iu cmp bash
cd /opt/cmp/app/cmp
set -a; source /etc/cmp/cmp.env; set +a
export DJANGO_SETTINGS_MODULE=config.settings.production
PY=/opt/cmp/venv/bin/python

# Konfiguration prüfen (sollte 0 Issues melden)
$PY manage.py check --deploy

# Datenbank-Schema
$PY manage.py migrate

# Static Files einsammeln -> /opt/cmp/app/cmp/staticfiles
$PY manage.py collectstatic --noinput

# Admin anlegen (Self-Service-Signup ist deaktiviert — Admin erstellt User)
$PY manage.py createsuperuser

exit
```

> `manage.py check --deploy` muss **ohne Sicherheitswarnungen** durchlaufen —
> die Hardening-Flags in `production.py` sind genau darauf ausgelegt.

---

## 10. gunicorn als systemd-Service

`/etc/systemd/system/cmp-web.service`:

```ini
[Unit]
Description=CMP Django (gunicorn)
After=network.target postgresql-16.service redis.service
Requires=postgresql-16.service

[Service]
User=cmp
Group=cmp
WorkingDirectory=/opt/cmp/app/cmp
EnvironmentFile=/etc/cmp/cmp.env
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
RuntimeDirectory=cmp
ExecStart=/opt/cmp/venv/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8001 \
    --workers 3 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
Restart=on-failure
RestartSec=5

# Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cmp-web
sudo systemctl status cmp-web --no-pager
```

> **Worker-Faustregel:** `(2 × CPU-Kerne) + 1`. Bei 1 Kern also 3.

---

## 11. Celery-Worker als systemd-Service

`/etc/systemd/system/cmp-celery.service`:

```ini
[Unit]
Description=CMP Django Celery Worker
After=network.target redis.service postgresql-16.service
Requires=redis.service

[Service]
User=cmp
Group=cmp
WorkingDirectory=/opt/cmp/app/cmp
EnvironmentFile=/etc/cmp/cmp.env
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=/opt/cmp/venv/bin/celery -A config worker \
    --loglevel=info \
    --concurrency=2
Restart=on-failure
RestartSec=5

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cmp-celery
sudo systemctl status cmp-celery --no-pager
```

> Die Celery-App ist `config.celery` → Aufruf mit `-A config`. In Produktion ist
> `CELERY_TASK_ALWAYS_EAGER=False`, Tasks laufen also echt asynchron über Redis.

---

## 12. nginx Reverse-Proxy

Zunächst HTTP (Port 80); TLS kommt in Schritt 14 dazu.
`/etc/nginx/conf.d/cmp.conf`:

```nginx
server {
    listen 80;
    server_name cmp.example.com;

    client_max_body_size 25m;

    # Static Files direkt von nginx
    location /static/ {
        alias /opt/cmp/app/cmp/staticfiles/;
        access_log off;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

```bash
sudo nginx -t                 # Konfiguration prüfen
sudo systemctl enable --now nginx
```

> `X-Forwarded-Proto` ist entscheidend: `production.py` setzt
> `SECURE_PROXY_SSL_HEADER`, damit Django hinter dem TLS-terminierenden nginx
> weiß, dass die Verbindung sicher ist.

---

## 13. SELinux & firewalld

Rocky/Alma laufen SELinux *enforcing*. Ohne die folgenden Schritte blockiert
SELinux den Proxy-Zugriff und nginx kann die Static Files nicht lesen.

```bash
# nginx darf zu gunicorn (TCP 8001) verbinden
sudo setsebool -P httpd_can_network_connect on

# Korrekten SELinux-Kontext für die Static Files setzen
sudo semanage fcontext -a -t httpd_sys_content_t "/opt/cmp/app/cmp/staticfiles(/.*)?"
sudo restorecon -Rv /opt/cmp/app/cmp/staticfiles

# Firewall: HTTP + HTTPS öffnen
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

> Liefert nginx weiter `403`, prüfe mit `sudo ausearch -m avc -ts recent` die
> SELinux-Denials und passe den Kontext an.

---

## 14. TLS mit Let's Encrypt

```bash
# certbot aus EPEL
sudo dnf -y install epel-release
sudo dnf -y install certbot python3-certbot-nginx

# Zertifikat holen und nginx automatisch konfigurieren
sudo certbot --nginx -d cmp.example.com --redirect --agree-tos -m admin@example.com

# Automatische Erneuerung (certbot bringt einen systemd-Timer mit)
sudo systemctl enable --now certbot-renew.timer
sudo certbot renew --dry-run
```

certbot ergänzt den `listen 443 ssl`-Block und einen 80→443-Redirect in
`cmp.conf`. Danach erzwingt zusätzlich Django (`SECURE_SSL_REDIRECT=True`,
HSTS) HTTPS.

---

## 15. Verifikation (Smoke-Test)

```bash
# Dienste laufen?
systemctl is-active cmp-web cmp-celery nginx postgresql-16 redis

# HTTP -> sollte auf HTTPS umleiten
curl -I http://cmp.example.com

# HTTPS -> 200/302 mit Sicherheits-Headern (HSTS)
curl -I https://cmp.example.com

# Admin-Login erreichbar
curl -sI https://cmp.example.com/admin/login/ | head -n1
```

Erwartung: `http://` → `301/302` nach `https://`, `https://` liefert eine
Antwort mit `Strict-Transport-Security`-Header, der Login ist erreichbar.

---

## 16. Updates & Re-Deploy

Neue Version ausrollen:

```bash
sudo -iu cmp bash
cd /opt/cmp/app
git pull --ff-only
/opt/cmp/venv/bin/pip install -r requirements/production.txt

cd /opt/cmp/app/cmp
set -a; source /etc/cmp/cmp.env; set +a
export DJANGO_SETTINGS_MODULE=config.settings.production
/opt/cmp/venv/bin/python manage.py migrate
/opt/cmp/venv/bin/python manage.py collectstatic --noinput
exit

# Dienste neu starten
sudo systemctl restart cmp-web cmp-celery
```

> Nach Änderungen an Static Files erneut `restorecon` laufen lassen (Schritt 13),
> falls neue Dateien ohne korrekten SELinux-Kontext erscheinen.

---

## 17. Betrieb: Logs, Backups, Health

**Logs** (gunicorn/Celery loggen nach journald):

```bash
sudo journalctl -u cmp-web -f
sudo journalctl -u cmp-celery -f
sudo tail -f /var/log/nginx/{access,error}.log
```

**Datenbank-Backup** (z.B. täglich per cron/systemd-Timer):

```bash
sudo -u postgres pg_dump -Fc cmp_prod > /var/backups/cmp_prod_$(date +%F).dump
```

**Health-Indikatoren:**

| Prüfung | Befehl |
|---|---|
| Web aktiv | `systemctl is-active cmp-web` |
| Worker aktiv | `systemctl is-active cmp-celery` |
| DB erreichbar | `psql "$DATABASE_URL" -c 'SELECT 1'` |
| Redis | `redis-cli ping` |
| Migrationen | `manage.py migrate --check` |

---

## 18. Troubleshooting

| Symptom | Ursache / Lösung |
|---|---|
| `502 Bad Gateway` | gunicorn down (`systemctl status cmp-web`) oder SELinux blockiert TCP → `setsebool -P httpd_can_network_connect on` |
| `403` auf `/static/` | falscher SELinux-Kontext → `restorecon -Rv .../staticfiles`; collectstatic gelaufen? |
| `DisallowedHost` | FQDN fehlt in `ALLOWED_HOSTS` (`/etc/cmp/cmp.env`) → ergänzen, `cmp-web` neu starten |
| `CSRF verification failed` | Origin fehlt in `CSRF_TRUSTED_ORIGINS` (mit `https://`!) |
| gunicorn startet nicht | `ModuleNotFoundError: config` → `WorkingDirectory` muss `/opt/cmp/app/cmp` sein |
| `psycopg.OperationalError` | DB-Passwort/`pg_hba.conf` falsch; `DATABASE_URL` prüfen |
| Tasks laufen nicht | `cmp-celery` down oder Redis nicht erreichbar; `journalctl -u cmp-celery` |
| TLS-Redirect-Loop | `SECURE_PROXY_SSL_HEADER` greift nur, wenn nginx `X-Forwarded-Proto` setzt (Schritt 12) |

Optionale Container-Variante ist mit AP-11 (Docker-Setup) vorgesehen; diese
Anleitung beschreibt die native VM-Installation.

---

## 19. Sicherheits-Checkliste

- [ ] `DEBUG=False` (Default) — niemals `True` in Produktion
- [ ] `SECRET_KEY` zufällig erzeugt, nicht der `change-me`-Default
- [ ] `/etc/cmp/cmp.env` mit `chmod 640`, Eigentümer `root:cmp`
- [ ] `ALLOWED_HOSTS` exakt auf den/die FQDN gesetzt
- [ ] `manage.py check --deploy` ohne Warnungen
- [ ] TLS aktiv, HTTP → HTTPS-Redirect, HSTS-Header vorhanden
- [ ] SELinux *enforcing* (`getenforce` → `Enforcing`)
- [ ] firewalld aktiv, nur 80/443 (+SSH) offen
- [ ] PostgreSQL/Redis nur auf `127.0.0.1` erreichbar
- [ ] `ACCOUNT_SIGNUP_ENABLED=False` (Default) — User legt der Admin an
- [ ] DB-Backups eingerichtet und wiederherstellbar getestet

---

*Stand: 2026-06-18 · Stack: Django 6.0.3 · Python 3.12 · PostgreSQL 16 · Redis 7 · Rocky/AlmaLinux 9*
