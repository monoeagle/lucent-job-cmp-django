# VM-Installation OFFLINE / Air-Gapped — CMP Django (Produktion)

Schritt-für-Schritt-Anleitung, um CMP Django auf einer **Rocky/AlmaLinux 9**-VM
**ohne Internetzugang** produktionssicher zu installieren. Alle Quellen
(System-RPMs, Python-Wheels, App-Code) werden auf einem verbundenen
**Staging-Host** eingesammelt, als Bundle auf die **Ziel-VM** transportiert und
dort offline installiert.

> **Online-Variante:** Hat die VM Internetzugang, nutze stattdessen
> [`vm-installation.md`](vm-installation.md). Diese Offline-Anleitung teilt deren
> Zielarchitektur — sie ersetzt nur die *Beschaffung* (Repos/PyPI → lokales
> Bundle) und **TLS** (Let's Encrypt → internes/self-signed Zertifikat, da ACME
> ohne Internet nicht funktioniert).

```
┌─ Staging-Host (mit Internet, Rocky 9 / x86_64) ─┐        ┌─ Ziel-VM (air-gapped) ─┐
│  RPMs (dnf download)                            │  scp/  │  lokales RPM-Repo      │
│  Python-Wheels (pip download)        ──Bundle──▶│  USB   │  pip --no-index        │
│  App-Source (git archive)                       │        │  systemd + nginx + TLS │
└─────────────────────────────────────────────────┘        └────────────────────────┘
```

---

## 🚀 Schnellstart über das fertige Release (empfohlen, „idiotensicher")

Das **GitHub-Release** bringt ein Offline-Bundle mit, das **alle Python-Pakete als
Wheels** enthält — die Ziel-VM braucht für die App **kein Internet**. Der Weg für
eine air-gapped VM in drei Schritten:

```
┌─ Internet-Rechner ─────────┐        ┌─ Ziel-VM (ohne Internet) ───────────────┐
│ 1. Release-ZIP ziehen      │  scp/  │ 3. entpacken + sudo ./deploy/install.sh │
│    (GitHub Releases)       │──USB──▶│    → App wird offline installiert       │
└────────────────────────────┘        └─────────────────────────────────────────┘
              2. transferieren (scp oder USB-Stick)
```

### Schritt 1 — Release auf einem Rechner **mit** Internet ziehen

Vom GitHub-Release das Offline-ZIP herunterladen — per `gh` CLI:

```bash
gh release download v1.1.0 \
  --repo monoeagle/lucent-job-MPP_Django \
  --pattern '*-almalinux9-offline.zip'
sha256sum *-almalinux9-offline.zip      # Prüfsumme notieren (für Schritt 2)
```

…oder ohne `gh` direkt von der Releases-Seite:
`https://github.com/monoeagle/lucent-job-MPP_Django/releases` → Asset
`Lucent-CMP-Django-<version>-almalinux9-offline.zip`.

### Schritt 2 — Auf die Ziel-VM transferieren (kein Internet)

```bash
# per SSH (falls erlaubt) …
scp Lucent-CMP-Django-*-almalinux9-offline.zip admin@cmp-vm:/var/tmp/
# … oder per USB-Medium kopieren.
```

Auf der VM die Integrität prüfen (Prüfsumme aus Schritt 1):

```bash
cd /var/tmp && sha256sum -c <<< "<sha256> Lucent-CMP-Django-<version>-almalinux9-offline.zip"
```

### Schritt 3 — Auf der Ziel-VM entpacken + Setup ausführen

```bash
unzip Lucent-CMP-Django-<version>-almalinux9-offline.zip
cd Lucent-CMP-Django-<version>-almalinux9-offline
sudo ./deploy/install.sh        # zeigt Prüfbereich + Menü
```

**Das war's — die App wird installiert.** `install.sh` erledigt offline aus dem
Bundle: venv + Wheels (`pip --no-index`), DB-Anlage, `.env` (SECRET_KEY auto),
Migrationen, `collectstatic`, Superuser, systemd (gunicorn + Celery), nginx,
firewalld/SELinux.

> **HTTP/HTTPS wird automatisch gewählt.** Liegt unter `/etc/pki/cmp/cmp.crt`
> ein zum FQDN passendes Zertifikat, läuft das Portal über **HTTPS** (`:443`);
> fehlt es, über **HTTP** (`:80`) — mit einer deutlichen Warnung. Der Installer
> erzeugt **kein** self-signed Zertifikat mehr. Für HTTPS in Produktion ein
> CA-Zertifikat einspielen (`cmp.crt` + `cmp.key` nach `/etc/pki/cmp/`) und
> `install.sh` erneut ausführen (idempotent — er erkennt das Zert und schaltet
> auf HTTPS). Der Prüfbereich zeigt die **tatsächliche** URL/Port.
>
> Der **FQDN muss im Client-Netz auflösbar** sein (DNS oder `hosts`-Eintrag) —
> sonst greift `ALLOWED_HOSTS` und Django antwortet mit **400 Bad Request**.

Am Terminal startet das Skript mit einem **Prüfbereich** (Ist-Zustand von
python3.12, PostgreSQL inkl. erkannter Variante, Redis, nginx, Installation,
Datenbank, Diensten) samt **Links & Ports**, gefolgt von einem Menü:

```
╔═ CMP Django · Installer v1.1.0 ════════════╗
║ SYSTEM                                     ║
║   ✓ python3.12      3.12.4                 ║
║   ✓ PostgreSQL      PGDG 16 · aktiv        ║
║   ✓ Redis           aktiv                  ║
║   ✗ nginx           nicht installiert      ║
║ INSTALLATION                               ║
║   ✓ /opt/cmp/app    v1.1.0                 ║
║   ✓ Datenbank       cmp_prod               ║
║   ✗ cmp-web         inaktiv                ║
║ LINKS & PORTS                              ║
║   Portal       https://cmp.intern/  :443   ║
║   gunicorn     127.0.0.1:8001  :8001       ║
╚════════════════════════════════════════════╝
  1) Installieren / Aktualisieren
  2) Nur prüfen (nichts ändern)
  3) Dienste neu starten
  q) Beenden
```

| Aufruf | Wirkung |
|---|---|
| `sudo ./deploy/install.sh` | Prüfbereich + Menü (nur am Terminal) |
| `sudo ./deploy/install.sh --install` | Direkt installieren/aktualisieren, ohne Menü |
| `sudo ./deploy/install.sh --check` | Nur prüfen, ändert nichts. **Exit 0 nur, wenn alles grün ist** — taugt als Health-Check für Monitoring/Cron |
| `sudo ./deploy/install.sh --restart` | `cmp-web` + `cmp-celery` neu starten |

**Ohne Terminal** (Pipe, CI, `ssh host './install.sh'`) erscheint kein Menü —
dann läuft direkt die Installation, wie bisher. Bestehende Automatisierung
bleibt damit gültig.

> **Voraussetzung auf der VM (einmalig):** die **System-Pakete** `python3.12`,
> `postgresql16-server`, `redis`, `nginx`, `openssl` müssen installiert sein —
> diese stecken **nicht** im ZIP (nur die Python-Wheels).
> ```bash
> sudo dnf install -y python3.12 postgresql16-server postgresql16 redis nginx openssl
> sudo /usr/pgsql-16/bin/postgresql-16-setup initdb
> sudo systemctl enable --now postgresql-16 redis
> ```
> **Hat die VM Netzzugang zu PGDG + EPEL**, nimmt `install.sh` diesen Schritt auf
> Wunsch selbst ab:
> ```bash
> sudo ./deploy/install.sh --with-packages
> ```
> Das richtet das PGDG-Repo ein, deaktiviert das kollidierende AppStream-Modul,
> installiert die Pakete, initialisiert den Cluster (nur falls noch keiner
> existiert) und startet `postgresql-16` + `redis`. **Bewusst kein Default** —
> das Bundle muss auch auf air-gapped VMs funktionieren.
>
> Hat die VM **gar kein** Internet (auch nicht für diese RPMs), bring die RPMs
> separat als Bundle mit → **Teil A–C** unten. Der `install.sh` deckt den
> Python-/App-/Dienste-Teil ab; die RPM-Beschaffung bleibt Teil A.
>
> **PostgreSQL-Variante:** Der Installer unterstützt **beide** Ursprünge und
> erkennt sie selbst — er rät nicht. PGDG legt `psql` nach `/usr/pgsql-16/bin/`
> (**nicht** im PATH) und nennt die Unit `postgresql-16.service`; das
> AppStream-Modul nutzt `/usr/bin/psql` und `postgresql.service`. Service-Name
> und `psql`-Pfad werden daraus abgeleitet, auch für die `Requires=`-Abhängigkeit
> der `cmp-web`/`cmp-celery`-Units. Findet der Preflight **kein** PostgreSQL,
> bricht er ab (statt wie früher nur zu warnen und später an der DB-Anlage zu
> scheitern).

### Release selbst bauen (für Updates / eigene Stände)

Statt das GitHub-Release zu ziehen, lässt sich das Bundle reproduzierbar bauen
(Linux-Host mit Python 3.12 + Internet):

```bash
./run.sh release      # lädt Wheels (falls leer) + baut release/…-almalinux9-offline.zip
# entspricht: pip download … (wheels/) + python3 tools/build_release.py
```

---

## Inhalt

- **Teil A — Staging-Host (Artefakte einsammeln)**
  1. [Voraussetzungen Staging](#1-voraussetzungen-staging-host)
  2. [System-RPMs herunterladen](#2-system-rpms-herunterladen)
  3. [Python-Wheels herunterladen](#3-python-wheels-herunterladen)
  4. [App-Source paketieren](#4-app-source-paketieren)
  5. [Bundle schnüren + Prüfsummen](#5-bundle-schnüren--prüfsummen)
- **Teil B — Transport**
  6. [Bundle auf die VM bringen + verifizieren](#6-bundle-auf-die-vm-bringen--verifizieren)
- **Teil C — Ziel-VM (offline installieren)**
  7. [System-Pakete aus lokalem Bundle](#7-system-pakete-aus-lokalem-bundle)
  8. [PostgreSQL 16 / Redis / Service-User](#8-postgresql-16--redis--service-user)
  9. [Code + venv + Wheels offline](#9-code--venv--wheels-offline)
  10. [Settings, Migrationen, Static, Admin](#10-settings-migrationen-static-admin)
  11. [systemd-Units (gunicorn + Celery)](#11-systemd-units-gunicorn--celery)
  12. [nginx + internes TLS (ohne Let's Encrypt)](#12-nginx--internes-tls-ohne-lets-encrypt)
  13. [SELinux & firewalld](#13-selinux--firewalld)
  14. [Verifikation](#14-verifikation)
  15. [Offline-Updates](#15-offline-updates-re-deploy)
  16. [Troubleshooting + Sicherheits-Checkliste](#16-troubleshooting--sicherheits-checkliste)

---

## ⚠️ Grundregel: Staging-Host == Ziel-VM

Binärartefakte (RPMs, kompilierte Wheels wie `psycopg-binary`) sind an OS,
Architektur und Python-Version gebunden. Der Staging-Host **muss** matchen:

| Merkmal | Wert (dieses Projekt) |
|---|---|
| OS | Rocky Linux 9 / AlmaLinux 9 |
| Architektur | x86_64 |
| Python | 3.12 |

> Ideal ist ein Staging-Host mit *identischem* OS-Minor-Release. Notfalls eine
> Wegwerf-VM/Container mit Rocky 9 + Internet aufsetzen, Bundle bauen, verwerfen.

---

# Teil A — Staging-Host (Artefakte einsammeln)

## 1. Voraussetzungen Staging-Host

```bash
# Arbeitsverzeichnis fürs Bundle
mkdir -p ~/cmp-bundle/{rpms,wheelhouse,src}
cd ~/cmp-bundle

# Download-Plugins + PGDG-Repo (liefert PostgreSQL 16)
sudo dnf -y install dnf-plugins-core
sudo dnf -y install https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm
sudo dnf -qy module disable postgresql

# EPEL (für evtl. Zusatzpakete)
sudo dnf -y install epel-release
```

## 2. System-RPMs herunterladen

`--resolve --alldeps` zieht **alle** Abhängigkeiten mit, auch solche, die auf dem
Staging-Host schon installiert sind (sonst fehlen sie auf der frischen Ziel-VM):

```bash
cd ~/cmp-bundle
sudo dnf download --resolve --alldeps --destdir ./rpms \
  python3.12 python3.12-devel python3.12-pip \
  gcc make libpq-devel \
  postgresql16-server postgresql16 \
  redis \
  nginx \
  openssl \
  policycoreutils-python-utils \
  firewalld chrony

echo "Anzahl RPMs:"; ls ./rpms/*.rpm | wc -l
```

> **Hinweis:** Eine *minimal* installierte Rocky-9-VM hat die meisten Basis-Libs
> bereits. Sind beim Offline-Install dennoch Pakete „missing", auf dem Staging
> die fehlenden Namen ergänzen und Schritt 2 wiederholen.

## 3. Python-Wheels herunterladen

Wheels passend zu **Python 3.12 / x86_64**. Am robustesten in einem frischen
venv auf dem Staging-Host:

```bash
cd ~/cmp-bundle
# App-Source wird in Schritt 4 geholt; requirements brauchen wir hier schon:
# (entweder aus dem Repo kopieren oder requirements/*.txt einzeln bereitstellen)

python3.12 -m venv /tmp/dlvenv
/tmp/dlvenv/bin/pip install --upgrade pip

# Alle Produktions-Abhängigkeiten als Wheels (inkl. transitiver Deps)
/tmp/dlvenv/bin/pip download \
  -r /pfad/zum/repo/requirements/production.txt \
  -d ./wheelhouse

# pip selbst mitnehmen (für späteres Upgrade im Ziel-venv, optional)
/tmp/dlvenv/bin/pip download pip setuptools wheel -d ./wheelhouse

echo "Wheels:"; ls ./wheelhouse | wc -l
```

> Erwartet werden u.a. `Django`, `psycopg`, `psycopg_binary` (manylinux-Wheel),
> `gunicorn`, `celery`, `redis`, `django_environ`, `django_allauth`, `django_htmx`,
> `PyYAML`. Tauchen `.tar.gz`-sdists statt `.whl` auf, fehlen Build-Tools — dann
> `--only-binary=:all:` erzwingen und prüfen, welches Paket kein Wheel hat.

## 4. App-Source paketieren

Reproduzierbar aus dem Git-Stand (ohne `.git`-Historie → klein):

```bash
cd /pfad/zum/repo
git archive --format=tar.gz --prefix=app/ -o ~/cmp-bundle/src/cmp-app.tar.gz HEAD
# Version/Commit dokumentieren:
git rev-parse HEAD > ~/cmp-bundle/src/COMMIT.txt
```

> Alternativ ein voller Klon als `git bundle create cmp.bundle --all`, falls die
> Historie auf der VM gebraucht wird. Für reines Deployment reicht `git archive`.

## 5. Bundle schnüren + Prüfsummen

```bash
cd ~
# Prüfsummen über alle Artefakte
( cd cmp-bundle && find . -type f -exec sha256sum {} \; > SHA256SUMS )
# Ein Transport-Archiv
tar -czf cmp-offline-bundle.tar.gz -C cmp-bundle .
sha256sum cmp-offline-bundle.tar.gz > cmp-offline-bundle.tar.gz.sha256

ls -lh cmp-offline-bundle.tar.gz*
```

---

# Teil B — Transport

## 6. Bundle auf die VM bringen + verifizieren

Per `scp` (falls SSH erlaubt) oder USB-Medium:

```bash
# Beispiel scp (vom Staging-Host)
scp cmp-offline-bundle.tar.gz* admin@cmp-vm:/var/tmp/
```

Auf der **Ziel-VM** integrität prüfen und entpacken:

```bash
cd /var/tmp
sha256sum -c cmp-offline-bundle.tar.gz.sha256      # -> OK

sudo mkdir -p /opt/cmp-offline
sudo tar -xzf cmp-offline-bundle.tar.gz -C /opt/cmp-offline
cd /opt/cmp-offline

# Datei-Prüfsummen verifizieren
sha256sum -c SHA256SUMS | grep -v ': OK$' || echo "Alle Artefakte OK"
```

---

# Teil C — Ziel-VM (offline installieren)

> Ab hier ist die VM **air-gapped**. Kein `dnf`/`pip` greift aufs Internet.

## 7. System-Pakete aus lokalem Bundle

Direkt aus den lokalen RPMs installieren (kein Online-Repo, DNF löst innerhalb
des lokalen Satzes auf):

```bash
sudo dnf install -y --disablerepo='*' /opt/cmp-offline/rpms/*.rpm

# Grundkonfiguration (offline-fähig)
sudo hostnamectl set-hostname cmp.internal.example.com
sudo timedatectl set-timezone Europe/Berlin
sudo systemctl enable --now chronyd
python3.12 --version    # erwartet 3.12.x
```

> **Reusable-Repo-Alternative:** Ist `createrepo_c` im Bundle, lässt sich ein
> dauerhaftes lokales Repo bauen:
> `createrepo_c /opt/cmp-offline/rpms` und eine `.repo`-Datei mit
> `baseurl=file:///opt/cmp-offline/rpms` unter `/etc/yum.repos.d/` anlegen.

## 8. PostgreSQL 16 / Redis / Service-User

Identisch zur Online-Anleitung — die Pakete kommen jetzt aber lokal:

```bash
# PostgreSQL initialisieren
sudo /usr/pgsql-16/bin/postgresql-16-setup initdb
sudo systemctl enable --now postgresql-16

sudo -u postgres psql <<'SQL'
CREATE ROLE cmp WITH LOGIN PASSWORD '<DB-PASSWORT>';
CREATE DATABASE cmp_prod OWNER cmp ENCODING 'UTF8' TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE cmp_prod TO cmp;
SQL

# scram-sha-256 für localhost erzwingen, dann neu starten
sudo sed -i 's/^host\s\+all\s\+all\s\+127.0.0.1\/32\s\+ident/host    all             all             127.0.0.1\/32            scram-sha-256/' \
  /var/lib/pgsql/16/data/pg_hba.conf
sudo systemctl restart postgresql-16

# Redis
sudo systemctl enable --now redis
redis-cli ping     # -> PONG

# Dedizierter Service-User + Verzeichnisse
sudo useradd --system --create-home --home-dir /opt/cmp --shell /usr/sbin/nologin cmp
sudo mkdir -p /etc/cmp
```

Details zu DB-Härtung/Redis siehe [Online-Anleitung §4–§6](vm-installation.md#4-postgresql-16).

## 9. Code + venv + Wheels offline

```bash
sudo -iu cmp bash

# App-Source entpacken nach /opt/cmp/app
mkdir -p /opt/cmp/app
tar -xzf /opt/cmp-offline/src/cmp-app.tar.gz -C /opt/cmp --strip-components=0
# -> /opt/cmp/app/ (prefix "app/")
cat /opt/cmp-offline/src/COMMIT.txt   # deployter Commit

# venv mit Python 3.12
python3.12 -m venv /opt/cmp/venv

# pip OHNE Internet — ausschließlich aus dem wheelhouse
/opt/cmp/venv/bin/pip install --no-index --find-links=/opt/cmp-offline/wheelhouse \
  -r /opt/cmp/app/requirements/production.txt

# Prüfen, dass nichts nachgeladen werden wollte (sollte fehlerfrei sein)
/opt/cmp/venv/bin/python -c "import django, gunicorn, environ, psycopg, celery; print('Imports OK')"
exit
```

> `--no-index` schaltet PyPI komplett ab; `--find-links` zeigt auf das lokale
> Wheelhouse. Schlägt die Installation mit „No matching distribution" fehl, fehlt
> ein (transitives) Wheel im Bundle → auf dem Staging-Host nachziehen.

## 10. Settings, Migrationen, Static, Admin

Wie in der Online-Anleitung — env-basiertes `config.settings.production`:

```bash
# SECRET_KEY erzeugen (lokal, kein Internet nötig)
/opt/cmp/venv/bin/python -c "import secrets; print(secrets.token_urlsafe(64))"

sudo cp /opt/cmp/app/.env.example /etc/cmp/cmp.env
sudo vim /etc/cmp/cmp.env          # SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL, CSRF_TRUSTED_ORIGINS
sudo chown root:cmp /etc/cmp/cmp.env && sudo chmod 640 /etc/cmp/cmp.env

# Migrationen / Static / Admin
sudo -iu cmp bash
cd /opt/cmp/app/cmp
set -a; source /etc/cmp/cmp.env; set +a
export DJANGO_SETTINGS_MODULE=config.settings.production
PY=/opt/cmp/venv/bin/python
$PY manage.py check --deploy
$PY manage.py migrate
$PY manage.py collectstatic --noinput
$PY manage.py createsuperuser
exit
```

`.env`-Felder im Detail: siehe [Online-Anleitung §8](vm-installation.md#8-umgebungsdatei-secrets)
und [`.env.example`](../../.env.example). `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`
auf den **internen** FQDN setzen (z.B. `cmp.internal.example.com`).

## 11. systemd-Units (gunicorn + Celery)

**Identisch zur Online-Anleitung** — keine Internet-Abhängigkeit.
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
    --bind 127.0.0.1:8001 --workers 3 --timeout 60 \
    --access-logfile - --error-logfile -
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

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
ExecStart=/opt/cmp/venv/bin/celery -A config worker --loglevel=info --concurrency=2
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
sudo systemctl enable --now cmp-web cmp-celery
sudo systemctl status cmp-web cmp-celery --no-pager
```

## 12. nginx + internes TLS (ohne Let's Encrypt)

**Wichtigster Unterschied zur Online-Anleitung:** ACME/Let's Encrypt scheidet
air-gapped aus. Stattdessen ein **internes CA-** oder **self-signed Zertifikat**.

### Variante A — Zertifikat von der internen Unternehmens-CA
Wenn vorhanden, `cmp.crt` (inkl. Zwischen-CA-Kette) + `cmp.key` von der internen
PKI ausstellen lassen und nach `/etc/pki/cmp/` legen. Clients vertrauen der
internen Root-CA bereits → keine Browser-Warnung. **Empfohlen.**

### Variante B — Self-signed (Test/kleine Umgebung)

```bash
sudo mkdir -p /etc/pki/cmp
sudo openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
  -keyout /etc/pki/cmp/cmp.key -out /etc/pki/cmp/cmp.crt \
  -subj "/CN=cmp.internal.example.com" \
  -addext "subjectAltName=DNS:cmp.internal.example.com"
sudo chmod 600 /etc/pki/cmp/cmp.key
```

> Die `cmp.crt` muss in den **Trust-Store der Clients** importiert werden
> (Browser/OS), sonst Zertifikatswarnung.

`/etc/nginx/conf.d/cmp.conf`:

```nginx
server {
    listen 80;
    server_name cmp.internal.example.com;
    return 301 https://$host$request_uri;   # HTTP -> HTTPS
}

server {
    listen 443 ssl;
    http2 on;
    server_name cmp.internal.example.com;

    ssl_certificate     /etc/pki/cmp/cmp.crt;
    ssl_certificate_key /etc/pki/cmp/cmp.key;
    ssl_protocols       TLSv1.2 TLSv1.3;

    client_max_body_size 25m;

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
sudo nginx -t
sudo systemctl enable --now nginx
```

> **HSTS-Hinweis:** Bei *self-signed* Zertifikaten kann ein langer
> `SECURE_HSTS_SECONDS` Clients aussperren. Für interne/Test-Umgebungen ggf. in
> `/etc/cmp/cmp.env` `SECURE_HSTS_SECONDS=0` setzen (Default produktiv: 1 Jahr).
> Bei vertrauenswürdiger interner CA (Variante A) HSTS regulär lassen.

## 13. SELinux & firewalld

Vollständig offline-fähig (keine Internet-Calls):

```bash
sudo setsebool -P httpd_can_network_connect on
sudo semanage fcontext -a -t httpd_sys_content_t "/opt/cmp/app/cmp/staticfiles(/.*)?"
sudo restorecon -Rv /opt/cmp/app/cmp/staticfiles

sudo firewall-cmd --permanent --add-service=http --add-service=https
sudo firewall-cmd --reload
```

## 14. Verifikation

```bash
systemctl is-active cmp-web cmp-celery nginx postgresql-16 redis

# HTTPS lokal testen (-k akzeptiert self-signed)
curl -kI https://cmp.internal.example.com
curl -ksI https://cmp.internal.example.com/admin/login/ | head -n1
```

Optional die App-Tests im Ziel-venv (PostgreSQL muss erreichbar sein):

```bash
sudo -iu cmp bash
cd /opt/cmp/app
/opt/cmp/venv/bin/python -m pytest -q   # erwartet: alle grün
exit
```

## 15. Offline-Updates (Re-Deploy)

> **Der einfachste Weg: `install.sh` erneut ausführen.** Das Skript ist
> **idempotent** — ein zweiter Lauf über einem neuen Bundle aktualisiert die
> bestehende Installation, statt sie zu duplizieren:
>
> - der **`SECRET_KEY` bleibt erhalten** (aus `/etc/cmp/cmp.env` übernommen) —
>   angemeldete Nutzer bleiben angemeldet;
> - **Rolle und Datenbank** werden getrennt geprüft, vorhandene Daten bleiben;
> - der App-Ordner wird **gespiegelt**, nicht gemerged — im neuen Release
>   gelöschte Module und alte Migrationen verschwinden auch auf der VM;
> - `cmp-web` und `cmp-celery` werden **neu gestartet**, laufen also mit dem
>   neuen Code;
> - ein vorhandenes **CA-signiertes Zertifikat** wird nie überschrieben.
>
> Beim Re-Run werden FQDN und DB-Passwort erneut abgefragt; ein leer gelassenes
> DB-Passwort wird neu vergeben (Rolle und `cmp.env` bleiben dabei konsistent).

Alternativ — oder wenn nur einzelne Artefakte getauscht werden sollen — der
manuelle Weg: pro Update auf dem Staging-Host ein **neues Bundle** bauen
(Teil A), typischerweise nur geänderte Wheels (`pip download` lädt nur Neues) +
frisches `git archive`. Auf der VM:

```bash
# Neue Artefakte entpacken (Teil B), dann:
sudo -iu cmp bash
tar -xzf /opt/cmp-offline/src/cmp-app.tar.gz -C /opt/cmp        # App aktualisieren
/opt/cmp/venv/bin/pip install --no-index --find-links=/opt/cmp-offline/wheelhouse \
  -r /opt/cmp/app/requirements/production.txt --upgrade
cd /opt/cmp/app/cmp
set -a; source /etc/cmp/cmp.env; set +a
export DJANGO_SETTINGS_MODULE=config.settings.production
/opt/cmp/venv/bin/python manage.py migrate
/opt/cmp/venv/bin/python manage.py collectstatic --noinput
exit
sudo systemctl restart cmp-web cmp-celery
sudo restorecon -Rv /opt/cmp/app/cmp/staticfiles   # neue Static-Dateien
```

## 16. Troubleshooting + Sicherheits-Checkliste

**Offline-spezifische Stolpersteine:**

| Symptom | Ursache / Lösung |
|---|---|
| `dnf … No match for argument` | RPM (oder Dep) fehlt im Bundle → Staging Schritt 2 mit `--alldeps` ergänzen |
| `pip … No matching distribution` | Wheel fehlt/falsche Plattform → Staging-Host muss Rocky 9 + Py 3.12 sein; Schritt 3 wiederholen |
| `psycopg`-Importfehler | `psycopg-binary`-Wheel fehlt oder Architektur-Mismatch (nicht x86_64) |
| Zertifikatswarnung im Browser | interne CA-/self-signed `cmp.crt` nicht im Client-Trust-Store |
| HSTS sperrt Client aus | self-signed + langer HSTS → `SECURE_HSTS_SECONDS=0` (siehe §12) |
| `sha256sum -c` schlägt fehl | Bundle-Transport korrupt → erneut übertragen |
| Zeit/Token-Fehler beim Login | NTP/`chronyd` ohne Zeitserver → internen NTP-Server konfigurieren |
| **Portal aus dem Subnetz nicht erreichbar** | Meist: nginx fehlte (Portal nur auf `127.0.0.1:8001`), firewalld blockt `:80`/`:443`, oder Zugriff per **IP statt FQDN** (→ `ALLOWED_HOSTS` → 400). Diagnose unten. |

### Portal aus dem Netz nicht erreichbar — Diagnose

**Auf der Ziel-VM (Linux):**

```bash
sudo ss -tlnp | grep -E ':(80|443|8001)'   # was lauscht worauf? :8001 ist NUR lokal (gunicorn)
sudo systemctl status nginx cmp-web cmp-celery redis --no-pager
curl -kI https://localhost/                 # bzw. curl -I http://localhost/ im HTTP-Modus
sudo firewall-cmd --list-all                # sind http/https offen? in welcher Zone liegt das Interface?
getenforce                                  # SELinux Enforcing?
ip -br addr                                 # IP der VM
```

**Vom Windows-Client (PowerShell):**

```powershell
Test-NetConnection -ComputerName <FQDN> -Port 443    # im HTTP-Modus: -Port 80
nslookup <FQDN>                                       # kennt das Netz den FQDN? (sonst nicht erreichbar / 400)
curl.exe -vk https://<FQDN>/                          # 400 = ALLOWED_HOSTS-Falle → per FQDN zugreifen, nicht per IP
```

Auswertung:

- Lauscht **nur** `127.0.0.1:8001` und kein `:80`/`:443` → **nginx fehlte** bei der Installation. `sudo dnf install nginx`, dann `install.sh` erneut (idempotent).
- `TcpTestSucceeded: False` trotz laufendem nginx → **firewalld/Zone**: `sudo firewall-cmd --permanent --add-service=http --add-service=https && sudo firewall-cmd --reload`.
- TCP klappt, aber **400 Bad Request** → per **FQDN** statt IP zugreifen und den FQDN im Client-Netz auflösbar machen (DNS/`hosts`).

**Sicherheits-Checkliste** (zusätzlich zur
[Online-Liste §19](vm-installation.md#19-sicherheits-checkliste)):

- [ ] Bundle-Prüfsummen (`SHA256SUMS`) auf der VM verifiziert
- [ ] Staging-Host == Ziel-VM (OS/Arch/Python) bestätigt
- [ ] `pip install --no-index` lief ohne Internet-Fallback durch
- [ ] TLS-Zertifikat von interner CA **oder** self-signed in Client-Trust importiert
- [ ] HSTS passend zur Zertifikatsvertrauensstellung gesetzt
- [ ] interner NTP-Server konfiguriert (Zeit für CSRF/Sessions/TLS)
- [ ] deployter Commit (`COMMIT.txt`) dokumentiert

---

*Stand: 2026-06-19 · air-gapped · Stack: Django 6.0.3 · Python 3.12 · PostgreSQL 16 · Redis 7 · Rocky/AlmaLinux 9*
