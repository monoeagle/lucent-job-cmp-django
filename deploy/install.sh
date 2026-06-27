#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# install.sh — MPP Django OFFLINE-Installer für AlmaLinux/Rocky 9
#
# Installiert das Marketplace Portal aus diesem Release-Bundle OHNE Internet:
# venv + Wheels (--no-index), DB-Anlage, env, Migrationen, Static, systemd,
# nginx + TLS. Spiegelt docs/vm-installation-offline.md (single source of truth).
#
# Aufruf auf der Ziel-VM (im entpackten Bundle-Ordner), als root:
#     sudo ./install.sh
#
# Voraussetzungen auf der VM (siehe START-HIER.txt / Doku §7–§8):
#   - AlmaLinux/Rocky 9, x86_64
#   - python3.12, postgresql16-server, redis, nginx installiert & gestartet
#     (Online: dnf install …; Offline: aus rpms/ — siehe Doku §2/§7)
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

BUNDLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="/opt/mpp"
APP_DIR="$APP_ROOT/app"
VENV="$APP_ROOT/venv"
ENV_FILE="/etc/mpp/mpp.env"
SVC_USER="mpp"
PY="python3.12"

C_OK=$'\e[0;32m'; C_INFO=$'\e[0;36m'; C_WARN=$'\e[1;33m'; C_ERR=$'\e[0;31m'; C_NC=$'\e[0m'
ok()   { echo "${C_OK}  ✓${C_NC} $1"; }
info() { echo "${C_INFO}  →${C_NC} $1"; }
warn() { echo "${C_WARN}  ⚠${C_NC} $1"; }
die()  { echo "${C_ERR}  ✗${C_NC} $1" >&2; exit 1; }
hdr()  { echo; echo "${C_INFO}═══ $1 ═══${C_NC}"; }

[ "$(id -u)" -eq 0 ] || die "Bitte als root ausführen:  sudo ./install.sh"

# ── 0. Preflight ──────────────────────────────────────────────────────────────
hdr "0/8  Preflight"
[ -d "$BUNDLE_DIR/mpp" ]      || die "mpp/ fehlt im Bundle (falsches Verzeichnis?)"
[ -d "$BUNDLE_DIR/wheels" ]   || die "wheels/ fehlt im Bundle"
[ -f "$BUNDLE_DIR/requirements/production.txt" ] || die "requirements/production.txt fehlt"
command -v "$PY" >/dev/null   || die "$PY nicht gefunden — zuerst python3.12 installieren (Doku §7)"
"$PY" -c 'import sys; assert sys.version_info[:2]==(3,12)' 2>/dev/null \
  || warn "$PY ist nicht 3.12 — Wheels sind für 3.12 gebaut, Mismatch möglich"
command -v psql >/dev/null    || warn "psql nicht gefunden — ist PostgreSQL installiert? (Doku §8)"
systemctl is-active --quiet redis 2>/dev/null || warn "redis läuft nicht (systemctl enable --now redis)"
ok "Bundle vollständig, $PY vorhanden"

# ── 1. Eingaben ───────────────────────────────────────────────────────────────
hdr "1/8  Konfiguration"
read -rp "  FQDN der VM (z.B. mpp.internal.example.com): " FQDN
[ -n "$FQDN" ] || die "FQDN ist Pflicht"
read -rsp "  Passwort für DB-User 'mpp' (leer = zufällig): " DBPW; echo
[ -n "$DBPW" ] || { DBPW="$("$PY" -c 'import secrets;print(secrets.token_urlsafe(24))')"; info "DB-Passwort generiert"; }
SECRET="$("$PY" -c 'import secrets;print(secrets.token_urlsafe(64))')"
ok "Konfiguration erfasst (SECRET_KEY generiert)"

# ── 2. Service-User + App-Code ────────────────────────────────────────────────
hdr "2/8  Service-User + App-Code"
id "$SVC_USER" &>/dev/null || useradd --system --create-home --home-dir "$APP_ROOT" --shell /usr/sbin/nologin "$SVC_USER"
mkdir -p "$APP_DIR" /etc/mpp
cp -a "$BUNDLE_DIR/mpp" "$APP_DIR/"
cp -a "$BUNDLE_DIR/requirements" "$APP_DIR/"
cp -a "$BUNDLE_DIR/wheels" "$APP_ROOT/"
chown -R "$SVC_USER:$SVC_USER" "$APP_ROOT"
ok "App nach $APP_DIR kopiert"

# ── 3. venv + Wheels offline ──────────────────────────────────────────────────
hdr "3/8  venv + Wheels (offline, --no-index)"
sudo -u "$SVC_USER" "$PY" -m venv "$VENV"
sudo -u "$SVC_USER" "$VENV/bin/pip" install --no-index --find-links="$APP_ROOT/wheels" --upgrade pip setuptools wheel
sudo -u "$SVC_USER" "$VENV/bin/pip" install --no-index --find-links="$APP_ROOT/wheels" -r "$APP_DIR/requirements/production.txt"
sudo -u "$SVC_USER" "$VENV/bin/python" -c "import django,gunicorn,environ,psycopg,celery,redis; print('Imports OK')"
ok "Abhängigkeiten offline installiert"

# ── 4. Datenbank ──────────────────────────────────────────────────────────────
hdr "4/8  PostgreSQL-Datenbank"
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='mpp'" 2>/dev/null | grep -q 1; then
  sudo -u postgres psql -c "ALTER ROLE mpp WITH PASSWORD '${DBPW}';" >/dev/null
  info "Rolle 'mpp' existierte — Passwort aktualisiert"
else
  sudo -u postgres psql >/dev/null <<SQL
CREATE ROLE mpp WITH LOGIN PASSWORD '${DBPW}';
CREATE DATABASE mpp_prod OWNER mpp ENCODING 'UTF8' TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE mpp_prod TO mpp;
SQL
  ok "DB 'mpp_prod' + Rolle 'mpp' angelegt"
fi

# ── 5. Umgebungsdatei ─────────────────────────────────────────────────────────
hdr "5/8  Umgebungsdatei $ENV_FILE"
cat > "$ENV_FILE" <<ENV
DEBUG=False
SECRET_KEY=${SECRET}
ALLOWED_HOSTS=${FQDN}
CSRF_TRUSTED_ORIGINS=https://${FQDN}
DATABASE_URL=postgres://mpp:${DBPW}@127.0.0.1:5432/mpp_prod
CELERY_BROKER_URL=redis://localhost:6379/0
SECURE_HSTS_SECONDS=0
ENV
chown root:"$SVC_USER" "$ENV_FILE"; chmod 640 "$ENV_FILE"
ok "$ENV_FILE geschrieben (HSTS=0 für self-signed; bei interner CA erhöhen)"

# ── 6. Migrationen + Static + Admin ───────────────────────────────────────────
hdr "6/8  Migrationen, Static, Superuser"
run_mgmt() { sudo -u "$SVC_USER" env DJANGO_SETTINGS_MODULE=config.settings.production \
  $(grep -v '^#' "$ENV_FILE" | sed 's/^/ /' | tr '\n' ' ') \
  "$VENV/bin/python" "$APP_DIR/mpp/manage.py" "$@"; }
run_mgmt check --deploy || warn "check --deploy meldete Hinweise (oben prüfen)"
run_mgmt migrate
run_mgmt collectstatic --noinput
info "Bitte jetzt einen Admin-Account anlegen:"
sudo -u "$SVC_USER" env DJANGO_SETTINGS_MODULE=config.settings.production \
  $(grep -v '^#' "$ENV_FILE" | sed 's/^/ /' | tr '\n' ' ') \
  "$VENV/bin/python" "$APP_DIR/mpp/manage.py" createsuperuser || warn "createsuperuser übersprungen — später nachholen"
ok "DB migriert, Static gesammelt"

# ── 7. systemd-Units ──────────────────────────────────────────────────────────
hdr "7/8  systemd (gunicorn + Celery)"
cat > /etc/systemd/system/mpp-web.service <<UNIT
[Unit]
Description=MPP Django (gunicorn)
After=network.target postgresql-16.service redis.service
[Service]
User=$SVC_USER
Group=$SVC_USER
WorkingDirectory=$APP_DIR/mpp
EnvironmentFile=$ENV_FILE
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
RuntimeDirectory=mpp
ExecStart=$VENV/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8001 --workers 3 --timeout 60 --access-logfile - --error-logfile -
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
[Install]
WantedBy=multi-user.target
UNIT
cat > /etc/systemd/system/mpp-celery.service <<UNIT
[Unit]
Description=MPP Django Celery Worker
After=network.target redis.service postgresql-16.service
[Service]
User=$SVC_USER
Group=$SVC_USER
WorkingDirectory=$APP_DIR/mpp
EnvironmentFile=$ENV_FILE
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=$VENV/bin/celery -A config worker --loglevel=info --concurrency=2
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now mpp-web mpp-celery
ok "mpp-web + mpp-celery aktiv"

# ── 8. nginx + TLS + firewalld/SELinux ────────────────────────────────────────
hdr "8/8  nginx + TLS"
if [ ! -f /etc/pki/mpp/mpp.crt ]; then
  mkdir -p /etc/pki/mpp
  openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
    -keyout /etc/pki/mpp/mpp.key -out /etc/pki/mpp/mpp.crt \
    -subj "/CN=${FQDN}" -addext "subjectAltName=DNS:${FQDN}" 2>/dev/null
  chmod 600 /etc/pki/mpp/mpp.key
  warn "Self-signed Zertifikat erzeugt — für Produktion internes CA-Zertifikat einspielen"
fi
cat > /etc/nginx/conf.d/mpp.conf <<NGINX
server { listen 80; server_name ${FQDN}; return 301 https://\$host\$request_uri; }
server {
    listen 443 ssl; http2 on; server_name ${FQDN};
    ssl_certificate /etc/pki/mpp/mpp.crt; ssl_certificate_key /etc/pki/mpp/mpp.key;
    ssl_protocols TLSv1.2 TLSv1.3; client_max_body_size 25m;
    location /static/ { alias $APP_DIR/mpp/staticfiles/; access_log off; expires 30d; }
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host; proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme; proxy_redirect off;
    }
}
NGINX
nginx -t && systemctl enable --now nginx && systemctl reload nginx
if command -v setsebool >/dev/null; then
  setsebool -P httpd_can_network_connect on || true
  semanage fcontext -a -t httpd_sys_content_t "$APP_DIR/mpp/staticfiles(/.*)?" 2>/dev/null || true
  restorecon -Rv "$APP_DIR/mpp/staticfiles" >/dev/null 2>&1 || true
fi
if command -v firewall-cmd >/dev/null; then
  firewall-cmd --permanent --add-service=http --add-service=https >/dev/null 2>&1 || true
  firewall-cmd --reload >/dev/null 2>&1 || true
fi
ok "nginx + TLS + firewalld/SELinux konfiguriert"

hdr "FERTIG"
echo "  Portal:   ${C_OK}https://${FQDN}/${C_NC}"
echo "  Admin:    https://${FQDN}/admin/"
echo "  Status:   systemctl status mpp-web mpp-celery nginx --no-pager"
echo "  Test:     curl -kI https://${FQDN}"
[ -n "${DBPW:-}" ] && echo "  ${C_WARN}DB-Passwort steht in $ENV_FILE (chmod 640).${C_NC}"
