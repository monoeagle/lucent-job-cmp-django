# ══════════════════════════════════════════════════════════════════════════════
# lib.sh — Hilfsfunktionen des CMP-Offline-Installers
#
# Wird von install.sh gesourct. Enthaelt die Logik, die darueber entscheidet,
# ob ein zweiter Lauf dasselbe Ergebnis liefert wie der erste — bewusst
# getrennt, damit sie ohne root/systemd/PostgreSQL testbar ist
# (tests/unit/test_install_lib.py).
#
# Externe Kommandos sind ueber CMP_PSQL / CMP_SYSTEMCTL injizierbar.
# ══════════════════════════════════════════════════════════════════════════════

# cmp_bundle_dir <skript-verzeichnis>
# install.sh liegt im Bundle unter deploy/; cmp/, wheels/ und requirements/
# liegen eine Ebene hoeher.
cmp_bundle_dir() {
    (cd "$1/.." && pwd)
}

# cmp_env_get <env-datei> <schluessel>
# Gibt den Wert aus, oder nichts, wenn Schluessel bzw. Datei fehlen.
# Fehlende Datei ist kein Fehler: bei der Erstinstallation gibt es sie noch nicht.
cmp_env_get() {
    local file="$1" key="$2"
    [ -f "$file" ] || return 0
    sed -n "s/^${key}=//p" "$file" | head -n1
}

# cmp_env_args <env-datei>
# Gibt jede KEY=VALUE-Zeile NUL-terminiert aus, damit der Aufrufer sie per
# `mapfile -d ''` in ein Array liest und an `env` uebergibt. NUL statt
# Wortzerlegung — sonst zerfaellt ein Wert mit Leerzeichen in zwei Argumente.
cmp_env_args() {
    local file="$1" line
    [ -f "$file" ] || return 0
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in '' | '#'*) continue ;; esac
        [[ "$line" == *=* ]] || continue
        printf '%s\0' "$line"
    done <"$file"
}

# cmp_secret_key <env-datei>
# Gibt den bestehenden SECRET_KEY zurueck, sonst einen frisch erzeugten.
# Wiederverwendung ist Pflicht: ein neuer Key entwertet bei jedem Re-Run alle
# Sessions und laufenden Passwort-Reset-Tokens.
cmp_secret_key() {
    local file="$1" existing
    existing="$(cmp_env_get "$file" SECRET_KEY)"
    if [ -n "$existing" ]; then
        printf '%s\n' "$existing"
        return 0
    fi
    "${CMP_PY:-python3.12}" -c 'import secrets;print(secrets.token_urlsafe(64))'
}

# cmp_sync_app <quelle> <ziel>
# Spiegelt <quelle> nach <ziel>. Bewusst rm -rf + cp -a statt cp -a allein:
# cp merged nur, sodass ein im neuen Release geloeschtes Modul (oder eine alte
# Migration) auf der VM liegen bliebe. rsync waere die Alternative, ist aber
# auf einer minimalen AlmaLinux-Installation nicht garantiert vorhanden.
cmp_sync_app() {
    local src="$1" dest="$2"
    [ -n "$dest" ] || {
        echo "cmp_sync_app: leeres Ziel" >&2
        return 1
    }
    [ -d "$src" ] || {
        echo "cmp_sync_app: Quelle fehlt: $src" >&2
        return 1
    }
    rm -rf "$dest"
    mkdir -p "$(dirname "$dest")"
    cp -a "$src" "$dest"
}

# ── PostgreSQL-Variante ───────────────────────────────────────────────────────
# PGDG und das AppStream-Modul unterscheiden sich in Paketname, Service-Name und
# Binary-Pfad. Nichts davon darf hart verdrahtet sein.
#
#            | PGDG                    | AppStream
#   Paket    | postgresql16-server     | postgresql-server
#   Service  | postgresql-16.service   | postgresql.service
#   Binaries | /usr/pgsql-16/bin/      | /usr/bin/
#
# CMP_PG_PREFIX verschiebt die Suche unter ein anderes Wurzelverzeichnis
# (nur fuer Tests; im Betrieb leer).

# cmp_pg_flavor  ->  "pgdg" | "appstream"; rc!=0 wenn kein PostgreSQL da ist.
cmp_pg_flavor() {
    local prefix="${CMP_PG_PREFIX:-}"
    if [ -x "${prefix}/usr/pgsql-16/bin/psql" ]; then
        echo pgdg
    elif [ -x "${prefix}/usr/bin/psql" ]; then
        echo appstream
    else
        return 1
    fi
}

# cmp_psql_bin  ->  absoluter Pfad zu psql.
# PGDG legt psql NICHT in den PATH — `command -v psql` findet es dort nicht.
cmp_psql_bin() {
    local prefix="${CMP_PG_PREFIX:-}"
    case "$(cmp_pg_flavor)" in
        pgdg) echo "${prefix}/usr/pgsql-16/bin/psql" ;;
        appstream) echo "${prefix}/usr/bin/psql" ;;
        *) return 1 ;;
    esac
}

# cmp_pg_service  ->  Name der systemd-Unit der jeweiligen Variante.
cmp_pg_service() {
    case "$(cmp_pg_flavor)" in
        pgdg) echo "postgresql-16.service" ;;
        appstream) echo "postgresql.service" ;;
        *) return 1 ;;
    esac
}

# cmp_pg_datadir  ->  Datenverzeichnis des Clusters der jeweiligen Variante.
cmp_pg_datadir() {
    local prefix="${CMP_PG_PREFIX:-}"
    case "$(cmp_pg_flavor)" in
        pgdg) echo "${prefix}/var/lib/pgsql/16/data" ;;
        appstream) echo "${prefix}/var/lib/pgsql/data" ;;
        *) return 1 ;;
    esac
}

# cmp_pg_initdb
# Initialisiert den Cluster — aber nur, wenn es noch keinen gibt. Ein zweiter
# initdb-Lauf ueber einem bestehenden Cluster scheitert und hat an vorhandenen
# Daten ohnehin nichts verloren.
cmp_pg_initdb() {
    local prefix="${CMP_PG_PREFIX:-}" datadir
    datadir="$(cmp_pg_datadir)" || return 1
    if [ -f "$datadir/PG_VERSION" ]; then
        return 0
    fi
    case "$(cmp_pg_flavor)" in
        pgdg) "${prefix}/usr/pgsql-16/bin/postgresql-16-setup" initdb ;;
        appstream) "${prefix}/usr/bin/postgresql-setup" --initdb ;;
        *) return 1 ;;
    esac
}

# cmp_install_packages
# Nur fuer `--with-packages` (Online-Modus). Richtet das PGDG-Repo ein und
# installiert die System-Pakete. Das AppStream-Modul muss vorher weg, sonst
# kollidiert es mit PGDG.
cmp_install_packages() {
    local dnf="${CMP_DNF:-dnf}"
    local repo_rpm="${CMP_PGDG_REPO_RPM:-https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm}"

    $dnf -y install "$repo_rpm"
    $dnf -y install epel-release
    $dnf -qy module disable postgresql
    $dnf -y install python3.12 postgresql16-server postgresql16 redis nginx openssl
}

# cmp_render_web_unit <user> <app-dir> <venv> <env-datei> <pg-service>
cmp_render_web_unit() {
    local user="$1" app_dir="$2" venv="$3" env_file="$4" pg_service="$5"
    cat <<UNIT
[Unit]
Description=CMP Django (gunicorn)
After=network.target ${pg_service} redis.service
Requires=${pg_service}

[Service]
User=${user}
Group=${user}
WorkingDirectory=${app_dir}/cmp
EnvironmentFile=${env_file}
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
RuntimeDirectory=cmp
ExecStart=${venv}/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8001 --workers 3 --timeout 60 --access-logfile - --error-logfile -
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

[Install]
WantedBy=multi-user.target
UNIT
}

# cmp_render_celery_unit <user> <app-dir> <venv> <env-datei> <pg-service>
cmp_render_celery_unit() {
    local user="$1" app_dir="$2" venv="$3" env_file="$4" pg_service="$5"
    cat <<UNIT
[Unit]
Description=CMP Django Celery Worker
After=network.target redis.service ${pg_service}
Requires=${pg_service}

[Service]
User=${user}
Group=${user}
WorkingDirectory=${app_dir}/cmp
EnvironmentFile=${env_file}
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
ExecStart=${venv}/bin/celery -A config worker --loglevel=info --concurrency=2
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

[Install]
WantedBy=multi-user.target
UNIT
}

# cmp_pg_ensure <rolle> <datenbank> <passwort>
# Rolle und Datenbank werden GETRENNT geprueft. Haengt die DB-Anlage an der
# Existenz der Rolle, legt ein Wiederanlauf nach Teilfehler (Rolle da, DB nicht)
# die Datenbank nie an.
cmp_pg_ensure() {
    local role="$1" db="$2" pw="$3"
    local psql="${CMP_PSQL:-sudo -u postgres psql}"

    if $psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${role}'" 2>/dev/null | grep -q 1; then
        $psql -c "ALTER ROLE ${role} WITH PASSWORD '${pw}';" >/dev/null
    else
        $psql -c "CREATE ROLE ${role} WITH LOGIN PASSWORD '${pw}';" >/dev/null
    fi

    if ! $psql -tAc "SELECT 1 FROM pg_database WHERE datname='${db}'" 2>/dev/null | grep -q 1; then
        $psql -c "CREATE DATABASE ${db} OWNER ${role} ENCODING 'UTF8' TEMPLATE template0;" >/dev/null
        $psql -c "GRANT ALL PRIVILEGES ON DATABASE ${db} TO ${role};" >/dev/null
    fi
}

# cmp_nginx_present
# Wahr, wenn nginx installiert ist. Ohne diese Pruefung lief der Installer bis
# zum letzten Schritt durch und starb dann am fehlenden /etc/nginx/conf.d/.
cmp_nginx_present() {
    command -v "${CMP_NGINX:-nginx}" >/dev/null 2>&1
}

# cmp_ensure_redis
# Startet Redis, falls installiert und gestoppt. rc!=0 nur, wenn Redis fehlt —
# eine blosse Warnung reichte nicht: Celery scheitert sonst spaeter am Broker.
cmp_ensure_redis() {
    local sc="${CMP_SYSTEMCTL:-systemctl}"
    $sc is-active --quiet redis 2>/dev/null && return 0
    $sc enable --now redis >/dev/null 2>&1 || return 1
    $sc is-active --quiet redis 2>/dev/null
}

# cmp_restart_services <unit>...
# `systemctl enable --now` startet eine bereits laufende Unit NICHT neu — nach
# einem Upgrade liefe der alte Code weiter. Daher explizit restart.
cmp_restart_services() {
    local sc="${CMP_SYSTEMCTL:-systemctl}"
    $sc daemon-reload
    $sc enable "$@"
    $sc restart "$@"
}

# cmp_cert_matches_fqdn <zertifikat> <fqdn>
# Wahr, wenn das Zertifikat existiert und den FQDN als SAN fuehrt. Eine reine
# Datei-Existenzpruefung wuerde bei geaendertem FQDN das alte Zertifikat behalten.
cmp_cert_matches_fqdn() {
    local crt="$1" fqdn="$2" sans
    [ -f "$crt" ] || return 1
    sans="$(openssl x509 -in "$crt" -noout -ext subjectAltName 2>/dev/null |
        tr ',' '\n' | sed -n 's/.*DNS://p' | tr -d '[:space:]')" || return 1
    printf '%s\n' "$sans" | grep -qxF "$fqdn"
}

# cmp_cert_is_self_signed <zertifikat>
# Wahr, wenn Issuer == Subject. Nur solche Zertifikate stammen vom Installer
# selbst und duerfen ersetzt werden — ein vom Admin eingespieltes CA-Zertifikat
# fasst der Installer nicht an.
cmp_cert_is_self_signed() {
    local crt="$1" issuer subject
    [ -f "$crt" ] || return 1
    issuer="$(openssl x509 -in "$crt" -noout -issuer 2>/dev/null | sed 's/^issuer=//')" || return 1
    subject="$(openssl x509 -in "$crt" -noout -subject 2>/dev/null | sed 's/^subject=//')" || return 1
    [ -n "$issuer" ] && [ "$issuer" = "$subject" ]
}

# ── HTTP/HTTPS-Modus ──────────────────────────────────────────────────────────
# Der Installer waehlt den Modus automatisch: liegt ein zum FQDN passendes
# Zertifikat vor, laeuft HTTPS; sonst HTTP (kein TLS). Beide Modi muessen sich
# konsistent durch env-Datei, nginx-Conf und Panel ziehen.

# cmp_env_security_lines <fqdn> <mode>
# Liefert die modus-abhaengigen Zeilen fuer /etc/cmp/cmp.env. Im http-Modus
# MUESSEN Secure-Cookies UND der SSL-Redirect aus — sonst wird ueber reines HTTP
# weder Session- noch CSRF-Cookie gesendet und der Login schlaegt fehl. HSTS
# bleibt 0 (self-signed/intern); bei einer echten CA manuell erhoehen.
cmp_env_security_lines() {
    local fqdn="$1" mode="$2"
    if [ "$mode" = "http" ]; then
        printf 'CSRF_TRUSTED_ORIGINS=http://%s\n' "$fqdn"
        printf 'SECURE_SSL_REDIRECT=False\n'
        printf 'SESSION_COOKIE_SECURE=False\n'
        printf 'CSRF_COOKIE_SECURE=False\n'
        printf 'SECURE_HSTS_SECONDS=0\n'
    else
        printf 'CSRF_TRUSTED_ORIGINS=https://%s\n' "$fqdn"
        printf 'SECURE_HSTS_SECONDS=0\n'
    fi
}

# cmp_render_nginx <fqdn> <app_dir> <mode>
# Rendert die nginx-Server-Conf fuer /etc/nginx/conf.d/cmp.conf.
#   http : nur Port 80, proxyt direkt auf gunicorn (kein TLS, KEIN Redirect —
#          ein Redirect auf 443 liefe ohne Zertifikat ins Leere).
#   https: Port 80 leitet dauerhaft auf 443 um, 443 terminiert TLS.
# nginx-eigene Variablen ($host, $scheme, …) werden mit \$ vor der Bash-
# Expansion geschuetzt; ${fqdn}/${app_dir} sind Bash-Variablen.
cmp_render_nginx() {
    local fqdn="$1" app_dir="$2" mode="$3"
    if [ "$mode" = "http" ]; then
        cat <<NGINX
server {
    listen 80; server_name ${fqdn}; client_max_body_size 25m;
    location /static/ { alias ${app_dir}/cmp/staticfiles/; access_log off; expires 30d; }
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host; proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme; proxy_redirect off;
    }
}
NGINX
    else
        cat <<NGINX
server { listen 80; server_name ${fqdn}; return 301 https://\$host\$request_uri; }
server {
    listen 443 ssl; http2 on; server_name ${fqdn};
    ssl_certificate /etc/pki/cmp/cmp.crt; ssl_certificate_key /etc/pki/cmp/cmp.key;
    ssl_protocols TLSv1.2 TLSv1.3; client_max_body_size 25m;
    location /static/ { alias ${app_dir}/cmp/staticfiles/; access_log off; expires 30d; }
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host; proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme; proxy_redirect off;
    }
}
NGINX
    fi
}

# cmp_portal_proto <nginx-conf>
# Leitet aus der TATSAECHLICH geschriebenen Conf ab, unter welchem Protokoll das
# Portal erreichbar ist — fuers Panel, damit es nicht https/443 anzeigt, waehrend
# real http/80 laeuft. Gibt "<proto> <port>" aus; ohne Conf keine Ausgabe
# (nichts erfinden).
cmp_portal_proto() {
    local conf="$1"
    [ -f "$conf" ] || return 0
    if grep -q 'listen 443' "$conf"; then
        echo "https 443"
    elif grep -q 'listen 80' "$conf"; then
        echo "http 80"
    fi
}
