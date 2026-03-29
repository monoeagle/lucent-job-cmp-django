#!/usr/bin/env bash
# ==============================================================================
# MPP Django Marketplace Portal — Dev Launcher
# ==============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MPP_DIR="$PROJECT_DIR/mpp"
VENV_DIR="$PROJECT_DIR/venv"

DB_NAME="mpp_dev"
DB_TEST_NAME="mpp_test"
DB_USER="mpp"
DB_PASS="mpp"
DB_HOST="localhost"
DB_PORT="5432"

SERVER_PORT=8000

# ------------------------------------------------------------------------------
# Colors
# ------------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
print_header() {
    clear
    echo -e "${CYAN}${BOLD}"
    echo "  ╔══════════════════════════════════════════════════════╗"
    echo "  ║     MPP — Marketplace Portal (Django 6.0)           ║"
    echo "  ║     Dev Launcher                                    ║"
    echo "  ╚══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
print_fail() { echo -e "  ${RED}✗${NC} $1"; }
print_warn() { echo -e "  ${YELLOW}!${NC} $1"; }
print_info() { echo -e "  ${DIM}→${NC} $1"; }

wait_for_enter() {
    echo ""
    echo -e "  ${DIM}Drücke ENTER um zum Menü zurückzukehren...${NC}"
    read -r
}

activate_venv() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    else
        print_fail "Virtual Environment nicht gefunden: $VENV_DIR"
        print_info "Starte mit Menüpunkt [1] Setup"
        wait_for_enter
        return 1
    fi
}

# ------------------------------------------------------------------------------
# Status Check
# ------------------------------------------------------------------------------
check_status() {
    echo -e "\n  ${BOLD}System-Status${NC}\n"

    # Python
    if command -v python3 &>/dev/null; then
        print_ok "Python $(python3 --version 2>&1 | cut -d' ' -f2)"
    else
        print_fail "Python3 nicht gefunden"
    fi

    # Venv
    if [ -d "$VENV_DIR" ]; then
        print_ok "Virtual Environment vorhanden"
    else
        print_fail "Virtual Environment fehlt"
    fi

    # Django
    if [ -d "$VENV_DIR" ] && "$VENV_DIR/bin/python" -c "import django" 2>/dev/null; then
        local dj_ver
        dj_ver=$("$VENV_DIR/bin/python" -c "import django; print(django.VERSION[:3])" 2>/dev/null)
        print_ok "Django $dj_ver"
    else
        print_fail "Django nicht installiert"
    fi

    # PostgreSQL
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" &>/dev/null; then
        print_ok "PostgreSQL läuft auf $DB_HOST:$DB_PORT"
    else
        print_fail "PostgreSQL nicht erreichbar"
    fi

    # mpp_dev DB
    if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" &>/dev/null; then
        print_ok "Datenbank '$DB_NAME' verfügbar"
    else
        print_fail "Datenbank '$DB_NAME' nicht verfügbar"
    fi

    # mpp_test DB
    if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_TEST_NAME" -c "SELECT 1" &>/dev/null; then
        print_ok "Test-Datenbank '$DB_TEST_NAME' verfügbar"
    else
        print_fail "Test-Datenbank '$DB_TEST_NAME' nicht verfügbar"
    fi

    # Redis
    if command -v redis-cli &>/dev/null && redis-cli ping &>/dev/null; then
        print_ok "Redis läuft"
    else
        print_warn "Redis nicht verfügbar (Celery läuft im EAGER-Modus)"
    fi

    # Node.js / Tailwind
    if command -v node &>/dev/null; then
        print_ok "Node.js $(node --version 2>/dev/null)"
    else
        print_warn "Node.js nicht gefunden (CSS-Build nicht möglich)"
    fi

    # Tailwind CSS output
    if [ -f "$MPP_DIR/static/css/output.css" ]; then
        local css_size
        css_size=$(wc -c < "$MPP_DIR/static/css/output.css")
        print_ok "Tailwind CSS gebaut ($(( css_size / 1024 )) KB)"
    else
        print_fail "Tailwind CSS nicht gebaut"
    fi

    # HTMX
    if [ -f "$MPP_DIR/static/js/htmx.min.js" ]; then
        print_ok "HTMX vorhanden"
    else
        print_fail "HTMX fehlt"
    fi

    # Tests
    if [ -d "$VENV_DIR" ]; then
        local test_count
        test_count=$("$VENV_DIR/bin/python" -m pytest "$PROJECT_DIR/tests/" --co -q 2>/dev/null | tail -1 | grep -oP '\d+' | head -1 || echo "?")
        print_info "$test_count Tests registriert"
    fi

    # Dev Server
    if lsof -i :"$SERVER_PORT" &>/dev/null; then
        print_ok "Dev-Server läuft auf Port $SERVER_PORT"
    else
        print_info "Dev-Server nicht gestartet"
    fi
}

# ------------------------------------------------------------------------------
# 1. Setup (venv + deps + DB + migrate + seed)
# ------------------------------------------------------------------------------
do_setup() {
    print_header
    echo -e "  ${BOLD}[1] Vollständiges Setup${NC}\n"

    # Venv
    echo -e "  ${BOLD}Python Virtual Environment${NC}"
    if [ ! -d "$VENV_DIR" ]; then
        print_info "Erstelle venv..."
        python3 -m venv "$VENV_DIR"
        print_ok "venv erstellt"
    else
        print_ok "venv existiert bereits"
    fi
    source "$VENV_DIR/bin/activate"

    # Deps
    echo -e "\n  ${BOLD}Abhängigkeiten${NC}"
    print_info "Installiere requirements..."
    pip install -q -r "$PROJECT_DIR/requirements/dev.txt"
    print_ok "Alle Pakete installiert"

    # Node/Tailwind
    echo -e "\n  ${BOLD}Frontend (Tailwind + DaisyUI)${NC}"
    if [ -f "$PROJECT_DIR/package.json" ]; then
        if command -v npm &>/dev/null; then
            print_info "npm install..."
            (cd "$PROJECT_DIR" && npm install --silent 2>/dev/null)
            print_ok "Node-Pakete installiert"
            print_info "CSS Build..."
            (cd "$PROJECT_DIR" && npm run css:build 2>/dev/null)
            print_ok "Tailwind CSS gebaut"
        else
            print_warn "npm nicht gefunden — CSS-Build übersprungen"
        fi
    fi

    # PostgreSQL
    echo -e "\n  ${BOLD}Datenbank${NC}"
    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" &>/dev/null; then
        print_fail "PostgreSQL nicht erreichbar — bitte manuell starten"
        wait_for_enter
        return
    fi
    print_ok "PostgreSQL läuft"

    # Create DBs (may need sudo)
    for db in "$DB_NAME" "$DB_TEST_NAME"; do
        if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$db" -c "SELECT 1" &>/dev/null; then
            print_ok "Datenbank '$db' existiert"
        else
            print_info "Erstelle '$db'..."
            if PGPASSWORD="$DB_PASS" createdb -h "$DB_HOST" -U "$DB_USER" "$db" 2>/dev/null; then
                print_ok "'$db' erstellt"
            elif sudo -n -u postgres createdb "$db" -O "$DB_USER" 2>/dev/null; then
                print_ok "'$db' erstellt (via sudo)"
            else
                print_fail "'$db' konnte nicht erstellt werden"
                print_info "Bitte manuell: sudo -u postgres createdb $db -O $DB_USER"
            fi
        fi
    done

    # Migrate
    echo -e "\n  ${BOLD}Migrationen${NC}"
    print_info "Führe Migrationen aus..."
    (cd "$MPP_DIR" && python manage.py migrate --no-input 2>&1 | tail -1)
    print_ok "Migrationen angewendet"

    # Sites
    (cd "$MPP_DIR" && python manage.py shell -c "
from django.contrib.sites.models import Site
Site.objects.update_or_create(id=1, defaults={'domain': 'localhost:$SERVER_PORT', 'name': 'MPP Dev'})
" 2>/dev/null)
    print_ok "Site-Konfiguration aktualisiert"

    # Seed
    echo -e "\n  ${BOLD}Demo-Daten${NC}"
    print_info "Seed-Daten laden..."
    (cd "$MPP_DIR" && python manage.py seed)
    print_ok "Demo-Daten geladen"

    echo -e "\n  ${GREEN}${BOLD}Setup abgeschlossen!${NC}"
    wait_for_enter
}

# ------------------------------------------------------------------------------
# 2. Start Server
# ------------------------------------------------------------------------------
do_start_server() {
    print_header
    echo -e "  ${BOLD}[2] Django Dev-Server starten${NC}\n"

    activate_venv || return

    if lsof -i :"$SERVER_PORT" &>/dev/null; then
        print_warn "Port $SERVER_PORT ist bereits belegt"
        wait_for_enter
        return
    fi

    print_ok "Server startet auf http://localhost:$SERVER_PORT"
    print_info "Login: test-requester / test123"
    print_info "Admin: test-admin / test123 → http://localhost:$SERVER_PORT/admin/"
    echo -e "\n  ${DIM}Strg+C zum Beenden${NC}\n"

    (cd "$MPP_DIR" && python manage.py runserver "$SERVER_PORT")

    wait_for_enter
}

# ------------------------------------------------------------------------------
# 3. Run Tests
# ------------------------------------------------------------------------------
do_run_tests() {
    print_header
    echo -e "  ${BOLD}[3] Tests ausführen${NC}\n"

    activate_venv || return

    echo -e "  ${DIM}a) Alle Tests${NC}"
    echo -e "  ${DIM}b) Unit Tests${NC}"
    echo -e "  ${DIM}c) Integration Tests${NC}"
    echo -e "  ${DIM}d) E2E Tests${NC}"
    echo -e "  ${DIM}e) Zurück${NC}"
    echo ""
    read -rp "  Auswahl: " choice

    case "$choice" in
        a) (cd "$PROJECT_DIR" && python -m pytest tests/ -v --tb=short) ;;
        b) (cd "$PROJECT_DIR" && python -m pytest tests/unit/ -v --tb=short) ;;
        c) (cd "$PROJECT_DIR" && python -m pytest tests/integration/ -v --tb=short) ;;
        d) (cd "$PROJECT_DIR" && python -m pytest tests/e2e/ -v --tb=short) ;;
        e) return ;;
        *) print_warn "Ungültige Auswahl" ;;
    esac

    wait_for_enter
}

# ------------------------------------------------------------------------------
# 4. Migrations
# ------------------------------------------------------------------------------
do_migrations() {
    print_header
    echo -e "  ${BOLD}[4] Migrationen${NC}\n"

    activate_venv || return

    echo -e "  ${DIM}a) migrate (anwenden)${NC}"
    echo -e "  ${DIM}b) makemigrations (erstellen)${NC}"
    echo -e "  ${DIM}c) showmigrations (Status)${NC}"
    echo -e "  ${DIM}d) Zurück${NC}"
    echo ""
    read -rp "  Auswahl: " choice

    case "$choice" in
        a) (cd "$MPP_DIR" && python manage.py migrate) ;;
        b) (cd "$MPP_DIR" && python manage.py makemigrations) ;;
        c) (cd "$MPP_DIR" && python manage.py showmigrations) ;;
        d) return ;;
        *) print_warn "Ungültige Auswahl" ;;
    esac

    wait_for_enter
}

# ------------------------------------------------------------------------------
# 5. Seed Data
# ------------------------------------------------------------------------------
do_seed() {
    print_header
    echo -e "  ${BOLD}[5] Demo-Daten laden${NC}\n"

    activate_venv || return

    (cd "$MPP_DIR" && python manage.py seed)

    wait_for_enter
}

# ------------------------------------------------------------------------------
# 6. Django Shell
# ------------------------------------------------------------------------------
do_shell() {
    print_header
    echo -e "  ${BOLD}[6] Django Shell${NC}\n"
    print_info "exit() zum Beenden"
    echo ""

    activate_venv || return

    (cd "$MPP_DIR" && python manage.py shell)

    wait_for_enter
}

# ------------------------------------------------------------------------------
# 7. Django Check
# ------------------------------------------------------------------------------
do_check() {
    print_header
    echo -e "  ${BOLD}[7] Django System Check${NC}\n"

    activate_venv || return

    (cd "$MPP_DIR" && python manage.py check)

    wait_for_enter
}

# ------------------------------------------------------------------------------
# 8. CSS Build
# ------------------------------------------------------------------------------
do_css_build() {
    print_header
    echo -e "  ${BOLD}[8] Tailwind CSS Build${NC}\n"

    if ! command -v npm &>/dev/null; then
        print_fail "npm nicht gefunden"
        wait_for_enter
        return
    fi

    echo -e "  ${DIM}a) Einmalig bauen${NC}"
    echo -e "  ${DIM}b) Watch-Modus (auto-rebuild)${NC}"
    echo -e "  ${DIM}c) Zurück${NC}"
    echo ""
    read -rp "  Auswahl: " choice

    case "$choice" in
        a)
            (cd "$PROJECT_DIR" && npm run css:build)
            print_ok "CSS gebaut"
            ;;
        b)
            print_info "Strg+C zum Beenden"
            (cd "$PROJECT_DIR" && npm run css:watch)
            ;;
        c) return ;;
        *) print_warn "Ungültige Auswahl" ;;
    esac

    wait_for_enter
}

# ------------------------------------------------------------------------------
# Main Menu
# ------------------------------------------------------------------------------
main() {
    while true; do
        print_header
        check_status
        echo ""
        echo -e "  ${BOLD}Aktionen${NC}"
        echo ""
        echo -e "  ${CYAN}1${NC}  Vollständiges Setup (venv + deps + DB + migrate + seed)"
        echo -e "  ${CYAN}2${NC}  Dev-Server starten (Port $SERVER_PORT)"
        echo -e "  ${CYAN}3${NC}  Tests ausführen"
        echo -e "  ${CYAN}4${NC}  Migrationen"
        echo -e "  ${CYAN}5${NC}  Demo-Daten laden (seed)"
        echo -e "  ${CYAN}6${NC}  Django Shell"
        echo -e "  ${CYAN}7${NC}  Django System Check"
        echo -e "  ${CYAN}8${NC}  Tailwind CSS Build"
        echo -e "  ${CYAN}q${NC}  Beenden"
        echo ""
        read -rp "  Auswahl: " choice

        case "$choice" in
            1) do_setup ;;
            2) do_start_server ;;
            3) do_run_tests ;;
            4) do_migrations ;;
            5) do_seed ;;
            6) do_shell ;;
            7) do_check ;;
            8) do_css_build ;;
            q|Q) echo -e "\n  ${DIM}Bye!${NC}\n"; exit 0 ;;
            *) ;;
        esac
    done
}

main
