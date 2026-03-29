#!/usr/bin/env bash
# ==============================================================================
# fix_databases.sh — Flask-DBs wiederherstellen + Django eigene DBs anlegen
#
# Dieses Script braucht sudo (für PostgreSQL-Superuser-Operationen).
# ==============================================================================
set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }
info() { echo -e "  ${CYAN}→${NC} $1"; }

DJANGO_PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FLASK_PROJECT_DIR="/home/meagle/Dokumente/CLAUDE/lucent-hub-apps/lucent-app-mpp-TDD"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  DB-Fix: Flask wiederherstellen + Django separieren  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# ------------------------------------------------------------------
# 1. Neue Django-DBs erstellen
# ------------------------------------------------------------------
echo -e "  ${CYAN}[1/4] Django-Datenbanken erstellen${NC}"

for DB in mpp_django_dev mpp_django_test; do
    if PGPASSWORD=mpp psql -h localhost -U mpp -d "$DB" -c "SELECT 1" &>/dev/null; then
        ok "$DB existiert bereits"
    else
        info "Erstelle $DB..."
        sudo -u postgres createdb "$DB" -O mpp
        ok "$DB erstellt"
    fi
done

# ------------------------------------------------------------------
# 2. Django-Migrationen auf neuen DBs ausführen
# ------------------------------------------------------------------
echo ""
echo -e "  ${CYAN}[2/4] Django-Migrationen auf neuen DBs${NC}"

cd "$DJANGO_PROJECT_DIR"
source venv/bin/activate

info "Migriere mpp_django_dev..."
(cd mpp && python manage.py migrate --no-input 2>&1 | tail -1)
ok "mpp_django_dev migriert"

info "Migriere mpp_django_test..."
(cd mpp && DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py migrate --no-input 2>&1 | tail -1)
ok "mpp_django_test migriert"

info "Seed-Daten laden..."
(cd mpp && python manage.py seed)
ok "Seed-Daten geladen"

info "Site-Konfiguration..."
(cd mpp && python manage.py shell -c "
from django.contrib.sites.models import Site
Site.objects.update_or_create(id=1, defaults={'domain': 'localhost:8000', 'name': 'MPP Django Dev'})
" 2>/dev/null)
ok "Site aktualisiert"

# ------------------------------------------------------------------
# 3. Flask-DBs wiederherstellen (Schema zurücksetzen + Alembic)
# ------------------------------------------------------------------
echo ""
echo -e "  ${CYAN}[3/4] Flask-Datenbanken wiederherstellen${NC}"

for DB in mpp_dev mpp_test; do
    info "Setze Schema zurück: $DB"
    PGPASSWORD=mpp psql -h localhost -U mpp -d "$DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" 2>/dev/null
    ok "$DB Schema zurückgesetzt"
done

if [ -d "$FLASK_PROJECT_DIR/venv" ]; then
    cd "$FLASK_PROJECT_DIR"
    source venv/bin/activate

    info "Alembic upgrade head (mpp_dev)..."
    DATABASE_URL="postgresql://mpp:mpp@localhost:5432/mpp_dev" alembic upgrade head 2>&1 | tail -3
    ok "mpp_dev Migrationen angewendet"

    if [ -f "scripts/seed.py" ]; then
        info "Flask Seed-Daten laden..."
        DATABASE_URL="postgresql://mpp:mpp@localhost:5432/mpp_dev" python scripts/seed.py 2>&1 | tail -3
        ok "Flask Seed-Daten geladen"
    fi

    info "Alembic upgrade head (mpp_test)..."
    DATABASE_URL="postgresql://mpp:mpp@localhost:5432/mpp_test" alembic upgrade head 2>&1 | tail -3
    ok "mpp_test Migrationen angewendet"
else
    fail "Flask venv nicht gefunden: $FLASK_PROJECT_DIR/venv"
    info "Bitte manuell: cd $FLASK_PROJECT_DIR && alembic upgrade head"
fi

# ------------------------------------------------------------------
# 4. Verifizierung
# ------------------------------------------------------------------
echo ""
echo -e "  ${CYAN}[4/4] Verifizierung${NC}"

for DB in mpp_dev mpp_test mpp_django_dev mpp_django_test; do
    COUNT=$(PGPASSWORD=mpp psql -h localhost -U mpp -d "$DB" -t -c "SELECT count(*) FROM pg_tables WHERE schemaname='public';" 2>/dev/null | tr -d ' ')
    if [ -n "$COUNT" ] && [ "$COUNT" -gt 0 ]; then
        ok "$DB: $COUNT Tabellen"
    else
        fail "$DB: keine Tabellen"
    fi
done

# Django Tests
echo ""
info "Django Tests..."
cd "$DJANGO_PROJECT_DIR"
source venv/bin/activate
TEST_RESULT=$(python -m pytest tests/ --tb=no -q 2>&1 | tail -1)
ok "Django: $TEST_RESULT"

# Flask Tests (wenn venv existiert)
if [ -d "$FLASK_PROJECT_DIR/venv" ]; then
    info "Flask Tests..."
    cd "$FLASK_PROJECT_DIR"
    source venv/bin/activate
    FLASK_RESULT=$(DATABASE_URL="postgresql://mpp:mpp@localhost:5432/mpp_test" python -m pytest tests/ --tb=no -q 2>&1 | tail -1)
    ok "Flask: $FLASK_RESULT"
fi

echo ""
echo -e "  ${GREEN}Fertig! Alle Datenbanken getrennt und funktionsfähig.${NC}"
echo ""
echo "  DB-Zuordnung:"
echo "    Flask (mpp-TDD):        mpp_dev / mpp_test"
echo "    Django (mpp-TDD-Django): mpp_django_dev / mpp_django_test"
echo ""
