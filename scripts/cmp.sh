#!/bin/bash
# ==============================================================================
# CloudMan Portal (Django) — Dev Launcher
# Unified menu for starting backend, CSS watch, docs, or all.
# Oriented on the Flask MPP launcher (lucent-app-mpp-TDD/scripts/mpp.sh)
# ==============================================================================

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CMP_DIR="$PROJECT_DIR/cmp"
VENV_DIR="$PROJECT_DIR/venv"

DB_NAME="cmp_django_dev"
DB_TEST_NAME="cmp_django_test"
DB_USER="cmp"
DB_PASS="cmp"
DB_HOST="localhost"
DB_PORT="5432"

SERVER_PORT=8000
DOCS_PORT=5078

BACKEND_PID=""
CSS_PID=""
DOCS_PID=""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ── Cleanup ───────────────────────────────────────────────────

cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping services...${NC}"
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null && echo "  Backend stopped."
    [ -n "$CSS_PID" ] && kill "$CSS_PID" 2>/dev/null && echo "  CSS Watch stopped."
    [ -n "$DOCS_PID" ] && kill "$DOCS_PID" 2>/dev/null && echo "  Docs stopped."
    BACKEND_PID=""
    CSS_PID=""
    DOCS_PID=""
}

trap cleanup EXIT

wait_for_enter() {
    echo ""
    echo -e "${DIM}Druecke ENTER um zum Menue zurueckzukehren...${NC}"
    read -r
}

# ── Prereq Checks ────────────────────────────────────────────

check_postgres() {
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -q 2>/dev/null; then
        echo -e "  PostgreSQL:  ${GREEN}running${NC}"
        return 0
    else
        echo -e "  PostgreSQL:  ${RED}not running${NC}"
        return 1
    fi
}

check_venv() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        echo -e "  Python venv: ${GREEN}found${NC}"
        return 0
    else
        echo -e "  Python venv: ${RED}not found${NC}"
        echo -e "  ${YELLOW}Erstelle venv...${NC}"
        python3 -m venv "$VENV_DIR" && \
            source "$VENV_DIR/bin/activate" && \
            pip install -r "$PROJECT_DIR/requirements/dev.txt" -q
        if [ $? -eq 0 ]; then
            echo -e "  Python venv: ${GREEN}erstellt${NC}"
            return 0
        else
            echo -e "  Python venv: ${RED}Installation fehlgeschlagen${NC}"
            return 1
        fi
    fi
}

check_node() {
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    if command -v node &>/dev/null; then
        echo -e "  Node.js:     ${GREEN}$(node --version)${NC}"
        return 0
    elif nvm use 22 >/dev/null 2>&1; then
        echo -e "  Node.js:     ${GREEN}$(node --version)${NC}"
        return 0
    else
        echo -e "  Node.js:     ${RED}not available${NC}"
        return 1
    fi
}

check_node_modules() {
    if [ -d "$PROJECT_DIR/node_modules" ]; then
        echo -e "  node_modules:${GREEN} found${NC}"
        return 0
    else
        echo -e "  node_modules:${YELLOW} not found — installiere...${NC}"
        cd "$PROJECT_DIR" && npm install --silent 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "  node_modules:${GREEN} installiert${NC}"
            return 0
        else
            echo -e "  node_modules:${RED} Installation fehlgeschlagen${NC}"
            return 1
        fi
    fi
}

check_docs_venv() {
    local DOCS_VENV="$PROJECT_DIR/cmp-docs/.venv-docs"
    if [ -f "$DOCS_VENV/bin/activate" ]; then
        echo -e "  Docs venv:   ${GREEN}found${NC}"
        return 0
    else
        echo -e "  Docs venv:   ${YELLOW}not found — erstelle...${NC}"
        python3 -m venv "$DOCS_VENV" && \
            source "$DOCS_VENV/bin/activate" && \
            pip install zensical -q 2>&1
        if [ $? -eq 0 ]; then
            echo -e "  Docs venv:   ${GREEN}erstellt + zensical installiert${NC}"
            deactivate 2>/dev/null
            return 0
        else
            echo -e "  Docs venv:   ${RED}Installation fehlgeschlagen${NC}"
            return 1
        fi
    fi
}

# ── Status ────────────────────────────────────────────────────

status_line() {
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "  Backend:     ${GREEN}running${NC} (PID $BACKEND_PID) -> http://localhost:$SERVER_PORT"
    else
        BACKEND_PID=""
        echo -e "  Backend:     ${RED}stopped${NC}"
    fi
    if [ -n "$CSS_PID" ] && kill -0 "$CSS_PID" 2>/dev/null; then
        echo -e "  CSS Watch:   ${GREEN}running${NC} (PID $CSS_PID)"
    else
        CSS_PID=""
        echo -e "  CSS Watch:   ${RED}stopped${NC}"
    fi
    if [ -n "$DOCS_PID" ] && kill -0 "$DOCS_PID" 2>/dev/null; then
        echo -e "  Docs:        ${GREEN}running${NC} (PID $DOCS_PID) -> http://localhost:$DOCS_PORT"
    else
        DOCS_PID=""
        echo -e "  Docs:        ${RED}stopped${NC}"
    fi
}

# ── Backend ───────────────────────────────────────────────────

start_backend() {
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "${YELLOW}Backend laeuft bereits (PID $BACKEND_PID).${NC}"
        wait_for_enter
        return
    fi

    echo -e "${CYAN}Backend starten...${NC}"
    cd "$PROJECT_DIR"

    if ! check_venv; then wait_for_enter; return; fi
    if ! check_postgres; then
        echo -e "${RED}PostgreSQL muss laufen. Bitte starten: sudo systemctl start postgresql${NC}"
        wait_for_enter; return
    fi

    source "$VENV_DIR/bin/activate"
    export DJANGO_SETTINGS_MODULE=config.settings.development

    echo "  Migrationen pruefen..."
    (cd "$CMP_DIR" && python manage.py migrate --no-input 2>&1 | tail -3) || {
        echo -e "${RED}Migration fehlgeschlagen!${NC}"
        wait_for_enter; return
    }

    echo "  Demo-Daten laden..."
    (cd "$CMP_DIR" && python manage.py seed 2>&1)

    echo "  Django starten auf Port $SERVER_PORT..."
    (cd "$CMP_DIR" && python manage.py runserver "$SERVER_PORT") > "$PROJECT_DIR/logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    sleep 2

    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "${GREEN}Backend gestartet (PID $BACKEND_PID)${NC}"
        echo -e "  URL:    ${BOLD}http://localhost:$SERVER_PORT${NC}"
        echo -e "  Admin:  ${BOLD}http://localhost:$SERVER_PORT/admin/${NC}"
        echo -e "  Log:    tail -f logs/backend.log"
    else
        echo -e "${RED}Backend konnte nicht gestartet werden!${NC}"
        echo "  Log-Ausgabe:"
        cat "$PROJECT_DIR/logs/backend.log" 2>/dev/null
        BACKEND_PID=""
    fi
    wait_for_enter
}

stop_backend() {
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null
        echo -e "${YELLOW}Backend gestoppt.${NC}"
        BACKEND_PID=""
    else
        echo -e "${YELLOW}Backend laeuft nicht.${NC}"
    fi
    wait_for_enter
}

# ── CSS Watch ─────────────────────────────────────────────────

start_css_watch() {
    if [ -n "$CSS_PID" ] && kill -0 "$CSS_PID" 2>/dev/null; then
        echo -e "${YELLOW}CSS Watch laeuft bereits (PID $CSS_PID).${NC}"
        wait_for_enter
        return
    fi

    echo -e "${CYAN}CSS Watch starten...${NC}"
    cd "$PROJECT_DIR"

    if ! check_node; then wait_for_enter; return; fi
    if ! check_node_modules; then wait_for_enter; return; fi

    echo "  Tailwind Watch starten..."
    npm run css:watch > "$PROJECT_DIR/logs/css.log" 2>&1 &
    CSS_PID=$!
    sleep 1

    if kill -0 "$CSS_PID" 2>/dev/null; then
        echo -e "${GREEN}CSS Watch gestartet (PID $CSS_PID)${NC}"
        echo -e "  Log:    tail -f logs/css.log"
    else
        echo -e "${RED}CSS Watch konnte nicht gestartet werden!${NC}"
        cat "$PROJECT_DIR/logs/css.log" 2>/dev/null
        CSS_PID=""
    fi
    wait_for_enter
}

stop_css_watch() {
    if [ -n "$CSS_PID" ] && kill -0 "$CSS_PID" 2>/dev/null; then
        kill "$CSS_PID" 2>/dev/null
        echo -e "${YELLOW}CSS Watch gestoppt.${NC}"
        CSS_PID=""
    else
        echo -e "${YELLOW}CSS Watch laeuft nicht.${NC}"
    fi
    wait_for_enter
}

# ── Docs ──────────────────────────────────────────────────────

start_docs() {
    if [ -n "$DOCS_PID" ] && kill -0 "$DOCS_PID" 2>/dev/null; then
        echo -e "${YELLOW}Docs laeuft bereits (PID $DOCS_PID).${NC}"
        wait_for_enter
        return
    fi

    echo -e "${CYAN}Dokumentation starten...${NC}"
    cd "$PROJECT_DIR"

    if ! check_docs_venv; then wait_for_enter; return; fi

    cd cmp-docs
    source .venv-docs/bin/activate

    echo "  Zensical starten auf Port $DOCS_PORT..."
    python -m zensical serve --dev-addr 0.0.0.0:$DOCS_PORT > "$PROJECT_DIR/logs/docs.log" 2>&1 &
    DOCS_PID=$!
    sleep 2

    if kill -0 "$DOCS_PID" 2>/dev/null; then
        echo -e "${GREEN}Docs gestartet (PID $DOCS_PID)${NC}"
        echo -e "  URL:    ${BOLD}http://localhost:$DOCS_PORT${NC}"
        echo -e "  Log:    tail -f logs/docs.log"
    else
        echo -e "${RED}Docs konnten nicht gestartet werden!${NC}"
        cat "$PROJECT_DIR/logs/docs.log" 2>/dev/null
        DOCS_PID=""
    fi
    deactivate 2>/dev/null
    wait_for_enter
}

stop_docs() {
    if [ -n "$DOCS_PID" ] && kill -0 "$DOCS_PID" 2>/dev/null; then
        kill "$DOCS_PID" 2>/dev/null
        echo -e "${YELLOW}Docs gestoppt.${NC}"
        DOCS_PID=""
    else
        echo -e "${YELLOW}Docs laeuft nicht.${NC}"
    fi
    wait_for_enter
}

# ── Alles starten ─────────────────────────────────────────────

start_all() {
    echo -e "${CYAN}Backend + CSS Watch + Docs starten...${NC}"
    echo ""

    # Backend
    if [ -z "$BACKEND_PID" ] || ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        cd "$PROJECT_DIR"
        if check_venv && check_postgres; then
            source "$VENV_DIR/bin/activate"
            export DJANGO_SETTINGS_MODULE=config.settings.development
            (cd "$CMP_DIR" && python manage.py migrate --no-input > /dev/null 2>&1)
            (cd "$CMP_DIR" && python manage.py seed 2>/dev/null)
            (cd "$CMP_DIR" && python manage.py runserver "$SERVER_PORT") > "$PROJECT_DIR/logs/backend.log" 2>&1 &
            BACKEND_PID=$!; sleep 2
            if kill -0 "$BACKEND_PID" 2>/dev/null; then
                echo -e "  Backend:   ${GREEN}gestartet${NC} (PID $BACKEND_PID)"
            else
                echo -e "  Backend:   ${RED}fehlgeschlagen${NC} — siehe logs/backend.log"
                BACKEND_PID=""
            fi
        fi
    else echo -e "  Backend:   ${GREEN}laeuft bereits${NC}"; fi

    # CSS Watch
    if [ -z "$CSS_PID" ] || ! kill -0 "$CSS_PID" 2>/dev/null; then
        cd "$PROJECT_DIR"
        if check_node > /dev/null 2>&1; then
            check_node_modules > /dev/null 2>&1
            npm run css:watch > "$PROJECT_DIR/logs/css.log" 2>&1 &
            CSS_PID=$!; sleep 1
            if kill -0 "$CSS_PID" 2>/dev/null; then
                echo -e "  CSS Watch: ${GREEN}gestartet${NC} (PID $CSS_PID)"
            else
                echo -e "  CSS Watch: ${RED}fehlgeschlagen${NC} — siehe logs/css.log"
                CSS_PID=""
            fi
        fi
    else echo -e "  CSS Watch: ${GREEN}laeuft bereits${NC}"; fi

    # Docs
    if [ -z "$DOCS_PID" ] || ! kill -0 "$DOCS_PID" 2>/dev/null; then
        cd "$PROJECT_DIR"
        if check_docs_venv > /dev/null 2>&1; then
            cd cmp-docs && source .venv-docs/bin/activate
            python -m zensical serve --dev-addr 0.0.0.0:$DOCS_PORT > "$PROJECT_DIR/logs/docs.log" 2>&1 &
            DOCS_PID=$!; sleep 2
            deactivate 2>/dev/null
            if kill -0 "$DOCS_PID" 2>/dev/null; then
                echo -e "  Docs:      ${GREEN}gestartet${NC} (PID $DOCS_PID)"
            else
                echo -e "  Docs:      ${RED}fehlgeschlagen${NC} — siehe logs/docs.log"
                DOCS_PID=""
            fi
        fi
    else echo -e "  Docs:      ${GREEN}laeuft bereits${NC}"; fi

    echo ""
    echo -e "${BOLD}Portal:    http://localhost:$SERVER_PORT${NC}  (Login: test-requester / test123)"
    echo -e "${BOLD}Admin:     http://localhost:$SERVER_PORT/admin/${NC}  (Login: test-admin / test123)"
    echo -e "${BOLD}Docs:      http://localhost:$DOCS_PORT${NC}"
    wait_for_enter
}

# ── Logs ──────────────────────────────────────────────────────

show_logs() {
    echo -e "${CYAN}=== Backend Log (letzte 20 Zeilen) ===${NC}"
    tail -20 "$PROJECT_DIR/logs/backend.log" 2>/dev/null || echo "  (kein Log)"
    echo ""
    echo -e "${CYAN}=== CSS Watch Log (letzte 10 Zeilen) ===${NC}"
    tail -10 "$PROJECT_DIR/logs/css.log" 2>/dev/null || echo "  (kein Log)"
    echo ""
    echo -e "${CYAN}=== Docs Log (letzte 10 Zeilen) ===${NC}"
    tail -10 "$PROJECT_DIR/logs/docs.log" 2>/dev/null || echo "  (kein Log)"
    wait_for_enter
}

# ── Tests ─────────────────────────────────────────────────────

run_tests() {
    echo -e "${CYAN}Tests ausfuehren...${NC}"
    echo ""
    echo "  [1] Alle Tests"
    echo "  [2] Unit Tests"
    echo "  [3] Integration Tests"
    echo "  [4] E2E Tests"
    echo "  [0] Zurueck"
    echo ""
    read -rp "Wahl: " test_choice

    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate" 2>/dev/null || { echo -e "${RED}venv nicht gefunden${NC}"; wait_for_enter; return; }

    case $test_choice in
        1) python -m pytest tests/ --tb=short -q 2>&1 ;;
        2) python -m pytest tests/unit/ --tb=short -q 2>&1 ;;
        3) python -m pytest tests/integration/ --tb=short -q 2>&1 ;;
        4) python -m pytest tests/e2e/ --tb=short -q 2>&1 ;;
        0) return ;;
    esac
    wait_for_enter
}

# ── DB Reset ──────────────────────────────────────────────────

reset_database() {
    echo -e "${RED}+================================================+${NC}"
    echo -e "${RED}|  ACHTUNG: Datenbank wird komplett geloescht!    |${NC}"
    echo -e "${RED}+================================================+${NC}"
    echo ""
    echo "  Dies loescht ALLE Daten (Orders, Templates, Subscriptions, etc.)"
    echo "  und spielt die Demo-Daten neu ein."
    echo ""
    read -rp "  Wirklich fortfahren? (j/N) " -n 1
    echo ""

    if [[ ! $REPLY =~ ^[jJyY]$ ]]; then
        echo "  Abgebrochen."
        wait_for_enter
        return
    fi

    # Stop backend if running
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "  ${YELLOW}Backend wird gestoppt...${NC}"
        kill "$BACKEND_PID" 2>/dev/null
        BACKEND_PID=""
        sleep 1
    fi

    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate" 2>/dev/null || { echo -e "${RED}venv nicht gefunden${NC}"; wait_for_enter; return; }

    if ! check_postgres > /dev/null 2>&1; then
        echo -e "${RED}PostgreSQL muss laufen.${NC}"
        wait_for_enter; return
    fi

    export DJANGO_SETTINGS_MODULE=config.settings.development

    echo ""
    echo -e "  ${YELLOW}Loesche Datenbank-Inhalt...${NC}"
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" 2>&1 || {
        echo -e "  ${RED}DB-Drop fehlgeschlagen. Versuche dropdb/createdb...${NC}"
        PGPASSWORD="$DB_PASS" dropdb -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" 2>/dev/null
        PGPASSWORD="$DB_PASS" createdb -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" 2>/dev/null
    }

    echo -e "  ${YELLOW}Migrationen ausfuehren...${NC}"
    (cd "$CMP_DIR" && python manage.py migrate --no-input 2>&1 | tail -3)

    echo -e "  ${YELLOW}Site-Konfiguration...${NC}"
    (cd "$CMP_DIR" && python manage.py shell -c "
from django.contrib.sites.models import Site
Site.objects.update_or_create(id=1, defaults={'domain': 'localhost:$SERVER_PORT', 'name': 'CMP Dev'})
" 2>/dev/null)

    echo -e "  ${YELLOW}Demo-Daten laden...${NC}"
    (cd "$CMP_DIR" && python manage.py seed 2>&1)

    echo ""
    echo -e "  ${GREEN}Datenbank zurueckgesetzt und neu befuellt!${NC}"
    wait_for_enter
}

# ── Migrationen ───────────────────────────────────────────────

run_migrations() {
    echo -e "${CYAN}Migrationen${NC}"
    echo ""
    echo "  [1] migrate (anwenden)"
    echo "  [2] makemigrations (erstellen)"
    echo "  [3] showmigrations (Status)"
    echo "  [0] Zurueck"
    echo ""
    read -rp "Wahl: " mig_choice

    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate" 2>/dev/null || { echo -e "${RED}venv nicht gefunden${NC}"; wait_for_enter; return; }
    export DJANGO_SETTINGS_MODULE=config.settings.development

    case $mig_choice in
        1) (cd "$CMP_DIR" && python manage.py migrate) ;;
        2) (cd "$CMP_DIR" && python manage.py makemigrations) ;;
        3) (cd "$CMP_DIR" && python manage.py showmigrations) ;;
        0) return ;;
    esac
    wait_for_enter
}

# ── Django Shell ──────────────────────────────────────────────

run_shell() {
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate" 2>/dev/null || { echo -e "${RED}venv nicht gefunden${NC}"; wait_for_enter; return; }
    export DJANGO_SETTINGS_MODULE=config.settings.development
    echo -e "${DIM}exit() zum Beenden${NC}"
    echo ""
    (cd "$CMP_DIR" && python manage.py shell)
    wait_for_enter
}

# ── CSS einmalig bauen ────────────────────────────────────────

build_css() {
    cd "$PROJECT_DIR"
    if ! check_node > /dev/null 2>&1; then
        echo -e "${RED}Node.js nicht gefunden${NC}"
        wait_for_enter; return
    fi
    check_node_modules > /dev/null 2>&1
    echo -e "${CYAN}Tailwind CSS bauen...${NC}"
    npm run css:build 2>&1
    echo -e "${GREEN}CSS gebaut.${NC}"
    wait_for_enter
}

# ── Main ──────────────────────────────────────────────────────

mkdir -p "$PROJECT_DIR/logs"

while true; do
    clear
    echo -e "${BOLD}+======================================================+${NC}"
    echo -e "${BOLD}|   CloudMan Portal (Django) — Dev Launcher          |${NC}"
    echo -e "${BOLD}+======================================================+${NC}"
    echo ""
    echo -e "${CYAN}Status:${NC}"
    status_line
    echo ""
    echo -e "${CYAN}Starten:${NC}"
    echo "  [1] Backend       (Django :$SERVER_PORT)"
    echo "  [2] CSS Watch     (Tailwind auto-rebuild)"
    echo "  [3] Dokumentation (Zensical :$DOCS_PORT)"
    echo "  [4] Alles starten"
    echo ""
    echo -e "${CYAN}Stoppen:${NC}"
    echo "  [5] Backend stoppen"
    echo "  [6] CSS Watch stoppen"
    echo "  [7] Docs stoppen"
    echo ""
    echo -e "${CYAN}Tools:${NC}"
    echo "  [8] Logs anzeigen"
    echo "  [9] Tests ausfuehren"
    echo "  [m] Migrationen"
    echo "  [c] CSS einmalig bauen"
    echo "  [i] Django Shell"
    echo -e "  [r] ${RED}DB Reset + Neu-Seed${NC}"
    echo ""
    echo -e "${CYAN}Demo-Zugaenge:${NC}"
    echo -e "  test-requester   ${YELLOW}Besteller${NC}"
    echo -e "  test-approver    ${YELLOW}Genehmiger${NC}"
    echo -e "  test-admin       ${YELLOW}Administrator${NC}"
    echo -e "  test-multi       ${YELLOW}Alle Rollen${NC}"
    echo -e "  test-superadmin  ${YELLOW}Super Admin${NC}"
    echo -e "  ${BOLD}Passwort: test123${NC}"
    echo ""
    echo "  [q] Beenden"
    echo ""
    read -rp "Wahl: " choice

    case $choice in
        1) start_backend ;;
        2) start_css_watch ;;
        3) start_docs ;;
        4) start_all ;;
        5) stop_backend ;;
        6) stop_css_watch ;;
        7) stop_docs ;;
        8) show_logs ;;
        9) run_tests ;;
        m|M) run_migrations ;;
        c|C) build_css ;;
        i|I) run_shell ;;
        r|R) reset_database ;;
        q|Q) echo -e "${YELLOW}Bye!${NC}"; exit 0 ;;
        *) echo -e "${RED}Ungueltige Eingabe.${NC}"; sleep 1 ;;
    esac
done
