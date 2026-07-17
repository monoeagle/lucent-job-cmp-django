#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# install.sh — CMP Django OFFLINE-Installer für AlmaLinux/Rocky 9
#
# Installiert das Marketplace Portal aus diesem Release-Bundle OHNE Internet:
# venv + Wheels (--no-index), DB-Anlage, env, Migrationen, Static, systemd,
# nginx + TLS. Spiegelt docs/vm-installation-offline.md (single source of truth).
#
# Aufruf auf der Ziel-VM (im entpackten Bundle-Ordner), als root:
#     sudo ./deploy/install.sh                 # Menü (am Terminal)
#     sudo ./deploy/install.sh --install       # direkt installieren, ohne Menü
#     sudo ./deploy/install.sh --check         # nur prüfen, ändert nichts
#     sudo ./deploy/install.sh --restart       # Dienste neu starten
#
# Optionen:
#     --with-packages   System-Pakete aus dem Netz installieren (PGDG + EPEL).
#                       Bewusst KEIN Default — das Bundle muss air-gapped laufen.
#     --skip-nginx      Reverse-Proxy/TLS überspringen.
#
# Ohne Terminal (Pipe, CI, `ssh host './install.sh'`) läuft direkt die
# Installation — bestehende Automatisierung bleibt damit gültig.
#
# Wiederholt ausführbar (idempotent): ein zweiter Lauf aktualisiert die
# Installation, behält SECRET_KEY und Daten und startet die Dienste mit dem
# neuen Code neu. Logik in lib.sh, Panel in ui.sh (beide unit-getestet).
#
# PostgreSQL wird in beiden Varianten unterstützt (PGDG und AppStream-Modul);
# Service-Name und psql-Pfad werden erkannt, nicht geraten.
#
# Voraussetzungen auf der VM (siehe START-HIER.txt / Doku §7–§8):
#   - AlmaLinux/Rocky 9, x86_64
#   - python3.12, postgresql16-server, redis, nginx installiert & gestartet
#     (Online: dnf install …; Offline: aus rpms/ — siehe Doku §2/§7)
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"
# shellcheck source=ui.sh
source "$SCRIPT_DIR/ui.sh"

BUNDLE_DIR="$(cmp_bundle_dir "$SCRIPT_DIR")"
APP_ROOT="/opt/cmp"
APP_DIR="$APP_ROOT/app"
VENV="$APP_ROOT/venv"
ENV_FILE="/etc/cmp/cmp.env"
NGINX_CONF="/etc/nginx/conf.d/cmp.conf"
SVC_USER="cmp"
PY="python3.12"

C_OK=$'\e[0;32m'; C_INFO=$'\e[0;36m'; C_WARN=$'\e[1;33m'; C_ERR=$'\e[0;31m'; C_NC=$'\e[0m'
ok()   { echo "${C_OK}  ✓${C_NC} $1"; }
info() { echo "${C_INFO}  →${C_NC} $1"; }
warn() { echo "${C_WARN}  ⚠${C_NC} $1"; }
die()  { echo "${C_ERR}  ✗${C_NC} $1" >&2; exit 1; }
hdr()  { echo; echo "${C_INFO}═══ $1 ═══${C_NC}"; }

# ── Argumente ─────────────────────────────────────────────────────────────────
ACTION="menu"
WITH_PACKAGES=0
SKIP_NGINX=0
for arg in "$@"; do
  case "$arg" in
    --install)       ACTION="install" ;;
    --check)         ACTION="check" ;;
    --restart)       ACTION="restart" ;;
    --with-packages) WITH_PACKAGES=1 ;;
    --skip-nginx)    SKIP_NGINX=1 ;;
    -h|--help) sed -n '3,32p' "${BASH_SOURCE[0]}" | sed -e 's/^# \{0,1\}//' -e 's/^═\{10,\}$//'; exit 0 ;;
    *) die "Unbekannte Option: $arg (siehe --help)" ;;
  esac
done

[ "$(id -u)" -eq 0 ] || die "Bitte als root ausführen:  sudo ./deploy/install.sh"

BUNDLE_VERSION="$([ -f "$BUNDLE_DIR/VERSION" ] && head -n1 "$BUNDLE_DIR/VERSION" | tr -d '[:space:]' || true)"

# ── Erkennung (weich) ─────────────────────────────────────────────────────────
# Setzt die PostgreSQL-Variablen, wenn PostgreSQL da ist — bricht aber NICHT ab.
# Der Prüfbereich muss auch auf einer nackten VM etwas anzeigen können.
PG_FLAVOR=""; PSQL_BIN=""; PG_SERVICE=""
erkennung_weich() {
  PG_FLAVOR="$(cmp_pg_flavor 2>/dev/null || true)"
  if [ -n "$PG_FLAVOR" ]; then
    PSQL_BIN="$(cmp_psql_bin)"
    PG_SERVICE="$(cmp_pg_service)"
    export CMP_PSQL="sudo -u postgres $PSQL_BIN"
  fi
}

# ── Prüfbereich ───────────────────────────────────────────────────────────────
status_sammeln() {
  printf 'S|SYSTEM\n'
  CMP_PY="$PY" cmp_status_python
  cmp_status_postgres
  cmp_status_redis
  cmp_status_nginx
  printf 'S|INSTALLATION\n'
  cmp_status_app "$APP_DIR"
  cmp_status_database cmp cmp_prod
  cmp_status_service cmp-web
  cmp_status_service cmp-celery
  cmp_status_links "$ENV_FILE" "$NGINX_CONF"
}

panel_zeigen() {
  local titel="CMP Django · Installer"
  [ -n "$BUNDLE_VERSION" ] && titel="CMP Django · Installer v${BUNDLE_VERSION}"
  status_sammeln | cmp_ui_render "$titel"
}

# ── Aktion: nur prüfen ────────────────────────────────────────────────────────
# Exit 0 nur, wenn alles grün ist — damit taugt `--check` als Health-Check für
# Monitoring/Cron. Jedes warn/fail/unknown ergibt Exit 1.
aktion_pruefen() {
  local daten titel="CMP Django · Prüfbereich"
  daten="$(status_sammeln)"
  printf '%s\n' "$daten" | cmp_ui_render "$titel"
  if printf '%s\n' "$daten" | grep -qE '^R\|(fail|warn|unknown)\|'; then
    return 1
  fi
  return 0
}

# ── Aktion: Dienste neu starten ───────────────────────────────────────────────
aktion_dienste_neustarten() {
  hdr "Dienste neu starten"
  cmp_restart_services cmp-web cmp-celery
  ok "cmp-web + cmp-celery neu gestartet"
}

# ── Preflight (hart, nur vor der Installation) ────────────────────────────────
preflight() {
  hdr "0/8  Preflight"
  [ -d "$BUNDLE_DIR/cmp" ]      || die "cmp/ fehlt im Bundle (falsches Verzeichnis?)"
  [ -d "$BUNDLE_DIR/wheels" ]   || die "wheels/ fehlt im Bundle"
  [ -f "$BUNDLE_DIR/requirements/production.txt" ] || die "requirements/production.txt fehlt"

  if [ "$WITH_PACKAGES" -eq 1 ]; then
    info "--with-packages: System-Pakete werden aus dem Netz installiert (PGDG + EPEL)"
    cmp_install_packages || die "Paket-Installation fehlgeschlagen — Netzzugang/Repos prüfen"
    cmp_pg_initdb        || die "PostgreSQL-Cluster konnte nicht initialisiert werden"
    erkennung_weich
    systemctl enable --now "$PG_SERVICE" redis
    ok "System-Pakete installiert, PostgreSQL initialisiert"
  fi

  command -v "$PY" >/dev/null || die "$PY nicht gefunden — zuerst python3.12 installieren (Doku §7) oder --with-packages nutzen"
  "$PY" -c 'import sys; assert sys.version_info[:2]==(3,12)' 2>/dev/null \
    || warn "$PY ist nicht 3.12 — Wheels sind für 3.12 gebaut, Mismatch möglich"

  erkennung_weich
  [ -n "$PG_FLAVOR" ] \
    || die "Kein PostgreSQL gefunden (weder PGDG unter /usr/pgsql-16/bin/ noch AppStream unter /usr/bin/) — Doku §8, oder --with-packages nutzen"
  ok "PostgreSQL erkannt: $PG_FLAVOR ($PSQL_BIN, $PG_SERVICE)"

  systemctl is-active --quiet "$PG_SERVICE" 2>/dev/null \
    || die "$PG_SERVICE läuft nicht (systemctl enable --now $PG_SERVICE)"

  # Redis starten; fehlt es, offline aus dem Bundle (rpms/) nachziehen — Celery
  # scheitert sonst später am Broker.
  cmp_ensure_redis "$BUNDLE_DIR/rpms" \
    || die "Redis fehlt und kein redis-RPM im Bundle (rpms/) — Redis-RPM ins Bundle legen (Doku §2) oder --with-packages (online) nutzen"
  ok "Redis läuft"

  # nginx JETZT prüfen, nicht erst im letzten Schritt: sonst läuft der Installer
  # komplett durch und stirbt am Ende an /etc/nginx/conf.d/.
  if [ "$SKIP_NGINX" -eq 1 ]; then
    info "--skip-nginx: TLS/Reverse-Proxy wird übersprungen"
  elif ! cmp_nginx_present; then
    SKIP_NGINX=1
    warn "nginx nicht installiert — Schritt 8 wird übersprungen. Das Portal ist dann NUR auf 127.0.0.1:8001 erreichbar, ohne TLS. Nachinstallieren: dnf install nginx, danach install.sh erneut ausführen."
  fi
  ok "Bundle vollständig, $PY vorhanden"
}

# ── Aktion: Installieren / Aktualisieren ──────────────────────────────────────
aktion_installieren() {
  preflight

  # ── 1. Eingaben ─────────────────────────────────────────────────────────────
  hdr "1/8  Konfiguration"
  read -rp "  FQDN der VM (z.B. cmp.internal.example.com): " FQDN
  [ -n "$FQDN" ] || die "FQDN ist Pflicht"
  read -rsp "  Passwort für DB-User 'cmp' (leer = zufällig): " DBPW; echo
  [ -n "$DBPW" ] || { DBPW="$("$PY" -c 'import secrets;print(secrets.token_urlsafe(24))')"; info "DB-Passwort generiert"; }

  # Bestehenden SECRET_KEY uebernehmen — ein neuer Key wuerde bei jedem Re-Run
  # alle Sessions und Passwort-Reset-Tokens entwerten.
  export CMP_PY="$PY"
  SECRET="$(cmp_secret_key "$ENV_FILE")"
  if [ -n "$(cmp_env_get "$ENV_FILE" SECRET_KEY)" ]; then
    info "Bestehender SECRET_KEY aus $ENV_FILE übernommen"
  else
    info "SECRET_KEY generiert"
  fi
  ok "Konfiguration erfasst"

  # HTTP/HTTPS automatisch waehlen: liegt ein zum FQDN passendes Zertifikat vor,
  # laeuft HTTPS; sonst HTTP (kein TLS, KEIN self-signed). Ohne nginx ist ohnehin
  # kein TLS moeglich -> http, sonst blockieren SSL-Redirect + Secure-Cookies
  # sogar den lokalen Zugriff.
  if [ "$SKIP_NGINX" -eq 0 ] && cmp_cert_matches_fqdn /etc/pki/cmp/cmp.crt "$FQDN"; then
    MODE="https"; info "Zertifikat für ${FQDN} vorhanden — HTTPS-Modus"
  else
    MODE="http"
    [ "$SKIP_NGINX" -eq 0 ] && warn "Kein Zertifikat für ${FQDN} unter /etc/pki/cmp/cmp.crt — Portal läuft über UNVERSCHLÜSSELTES HTTP. Für Produktion ein Zertifikat (cmp.crt + cmp.key) dort einspielen und install.sh erneut ausführen."
  fi

  # ── 2. Service-User + App-Code ──────────────────────────────────────────────
  hdr "2/8  Service-User + App-Code"
  id "$SVC_USER" &>/dev/null || useradd --system --create-home --home-dir "$APP_ROOT" --shell /usr/sbin/nologin "$SVC_USER"
  mkdir -p "$APP_DIR" /etc/cmp
  # Spiegeln statt mergen: cp -a allein liesse im neuen Release geloeschte Module
  # und alte Migrationen auf der VM zurueck.
  cmp_sync_app "$BUNDLE_DIR/cmp"          "$APP_DIR/cmp"
  cmp_sync_app "$BUNDLE_DIR/requirements" "$APP_DIR/requirements"
  cmp_sync_app "$BUNDLE_DIR/wheels"       "$APP_ROOT/wheels"
  # Versionsmarker mitinstallieren — sonst kann der Prüfbereich die installierte
  # Version nicht anzeigen (lucent-hub.yml ist nicht im Bundle).
  [ -f "$BUNDLE_DIR/VERSION" ] && cp "$BUNDLE_DIR/VERSION" "$APP_DIR/VERSION"
  chown -R "$SVC_USER:$SVC_USER" "$APP_ROOT"
  ok "App nach $APP_DIR gespiegelt"

  # ── 3. venv + Wheels offline ────────────────────────────────────────────────
  hdr "3/8  venv + Wheels (offline, --no-index)"
  sudo -u "$SVC_USER" "$PY" -m venv "$VENV"
  sudo -u "$SVC_USER" "$VENV/bin/pip" install --no-index --find-links="$APP_ROOT/wheels" --upgrade pip setuptools wheel
  sudo -u "$SVC_USER" "$VENV/bin/pip" install --no-index --find-links="$APP_ROOT/wheels" -r "$APP_DIR/requirements/production.txt"
  sudo -u "$SVC_USER" "$VENV/bin/python" -c "import django,gunicorn,environ,psycopg,celery,redis; print('Imports OK')"
  ok "Abhängigkeiten offline installiert"

  # ── 4. Datenbank ────────────────────────────────────────────────────────────
  hdr "4/8  PostgreSQL-Datenbank"
  # Rolle und Datenbank werden getrennt geprueft — sonst legt ein Wiederanlauf
  # nach Teilfehler (Rolle da, DB nicht) die Datenbank nie an.
  cmp_pg_ensure cmp cmp_prod "$DBPW"
  ok "Rolle 'cmp' + DB 'cmp_prod' vorhanden (Passwort gesetzt)"

  # ── 5. Umgebungsdatei ───────────────────────────────────────────────────────
  hdr "5/8  Umgebungsdatei $ENV_FILE"
  cat > "$ENV_FILE" <<ENV
DEBUG=False
SECRET_KEY=${SECRET}
ALLOWED_HOSTS=${FQDN}
DATABASE_URL=postgres://cmp:${DBPW}@127.0.0.1:5432/cmp_prod
CELERY_BROKER_URL=redis://localhost:6379/0
ENV
  # Modus-abhaengige Security-Zeilen (CSRF-Origin, SSL-Redirect, Secure-Cookies,
  # HSTS) anhaengen — im http-Modus MUESSEN die Secure-Cookies aus, sonst Login
  # ueber HTTP unmoeglich.
  cmp_env_security_lines "$FQDN" "$MODE" >> "$ENV_FILE"
  chown root:"$SVC_USER" "$ENV_FILE"; chmod 640 "$ENV_FILE"
  ok "$ENV_FILE geschrieben (Modus: $MODE; HSTS=0, bei gültigem CA-Zertifikat erhöhen)"

  # ── 6. Migrationen + Static + Admin ─────────────────────────────────────────
  hdr "6/8  Migrationen, Static, Superuser"
  # Env-Zeilen NUL-getrennt einlesen — die fruehere $(...)-Expansion zerlegte
  # Werte mit Leerzeichen (z.B. ein DB-Passwort) in mehrere Argumente.
  local ENV_ARGS
  mapfile -d '' -t ENV_ARGS < <(cmp_env_args "$ENV_FILE")
  run_mgmt() { sudo -u "$SVC_USER" env DJANGO_SETTINGS_MODULE=config.settings.production \
    "${ENV_ARGS[@]}" \
    "$VENV/bin/python" "$APP_DIR/cmp/manage.py" "$@"; }
  run_mgmt check --deploy || warn "check --deploy meldete Hinweise (oben prüfen)"
  run_mgmt migrate
  run_mgmt collectstatic --noinput
  if run_mgmt shell -c 'import sys
from django.contrib.auth import get_user_model
sys.exit(0 if get_user_model().objects.filter(is_superuser=True).exists() else 1)' 2>/dev/null; then
    info "Superuser existiert bereits — createsuperuser übersprungen"
  else
    info "Bitte jetzt einen Admin-Account anlegen:"
    run_mgmt createsuperuser || warn "createsuperuser übersprungen — später nachholen"
  fi
  ok "DB migriert, Static gesammelt"

  # ── 7. systemd-Units ────────────────────────────────────────────────────────
  hdr "7/8  systemd (gunicorn + Celery)"
  # Units haengen per Requires= am ERKANNTEN PostgreSQL-Service — ein hart
  # verdrahtetes postgresql-16.service liefe auf einer AppStream-VM ins Leere.
  cmp_render_web_unit    "$SVC_USER" "$APP_DIR" "$VENV" "$ENV_FILE" "$PG_SERVICE" \
    > /etc/systemd/system/cmp-web.service
  cmp_render_celery_unit "$SVC_USER" "$APP_DIR" "$VENV" "$ENV_FILE" "$PG_SERVICE" \
    > /etc/systemd/system/cmp-celery.service
  # restart statt `enable --now`: letzteres ist auf einer bereits laufenden Unit
  # ein No-Op — nach einem Upgrade liefe sonst der alte Code weiter.
  cmp_restart_services cmp-web cmp-celery
  ok "cmp-web + cmp-celery aktiv (mit aktuellem Code neu gestartet)"

  # ── 8. nginx + TLS + firewalld/SELinux ──────────────────────────────────────
  hdr "8/8  nginx + TLS"
  if [ "$SKIP_NGINX" -eq 1 ]; then
    warn "Übersprungen — kein Reverse-Proxy, kein TLS. Portal nur auf 127.0.0.1:8001."
  else
    # Modus (http/https) wurde in Schritt 1 aus der Zertifikats-Situation
    # bestimmt. KEIN self-signed mehr: fehlt ein passendes Zertifikat, laeuft
    # HTTP. Ein vom Admin eingespieltes Zertifikat wird nie angetastet.
    cmp_render_nginx "$FQDN" "$APP_DIR" "$MODE" > "$NGINX_CONF"
    nginx -t && systemctl enable --now nginx && systemctl reload nginx
    if command -v setsebool >/dev/null; then
      setsebool -P httpd_can_network_connect on || true
      semanage fcontext -a -t httpd_sys_content_t "$APP_DIR/cmp/staticfiles(/.*)?" 2>/dev/null || true
      restorecon -Rv "$APP_DIR/cmp/staticfiles" >/dev/null 2>&1 || true
    fi
    if command -v firewall-cmd >/dev/null; then
      # http immer oeffnen; https nur, wenn TLS wirklich laeuft.
      firewall-cmd --permanent --add-service=http >/dev/null 2>&1 || true
      if [ "$MODE" = "https" ]; then
        firewall-cmd --permanent --add-service=https >/dev/null 2>&1 || true
      fi
      firewall-cmd --reload >/dev/null 2>&1 || true
    fi
    ok "nginx (${MODE}) + firewalld/SELinux konfiguriert"
  fi

  hdr "FERTIG"
  panel_zeigen
  if [ "$SKIP_NGINX" -eq 1 ]; then
    echo "  ${C_WARN}Kein nginx konfiguriert — für den Zugriff von außen fehlt der"
    echo "  Reverse-Proxy inkl. TLS. Nach 'dnf install nginx' install.sh erneut"
    echo "  ausführen (das Skript ist idempotent).${C_NC}"
  fi
  [ -n "${DBPW:-}" ] && echo "  ${C_WARN}DB-Passwort steht in $ENV_FILE (chmod 640).${C_NC}"
  return 0
}

# ── Menü ──────────────────────────────────────────────────────────────────────
menue() {
  local wahl
  while true; do
    echo
    panel_zeigen
    echo "  1) Installieren / Aktualisieren"
    echo "  2) Nur prüfen (nichts ändern)"
    echo "  3) Dienste neu starten"
    echo "  q) Beenden"
    read -rp "> " wahl
    case "$wahl" in
      1) aktion_installieren ;;
      2) aktion_pruefen || true ;;
      3) aktion_dienste_neustarten ;;
      q|Q) exit 0 ;;
      *) warn "Ungültige Auswahl: $wahl" ;;
    esac
  done
}

# ── Einstieg ──────────────────────────────────────────────────────────────────
erkennung_weich
case "$ACTION" in
  install) aktion_installieren ;;
  check)   aktion_pruefen ;;
  restart) aktion_dienste_neustarten ;;
  menu)
    # Ohne Terminal nicht auf eine Eingabe warten, die nie kommt — dann
    # verhaelt sich der Aufruf wie bisher und installiert direkt durch.
    if [ -t 0 ]; then menue; else aktion_installieren; fi
    ;;
esac
