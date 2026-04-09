#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
MPP_DIR="$PROJECT_DIR/mpp"
VENV_DIR="$PROJECT_DIR/venv"

# ── AppImage-Variablen ────────────────────────────────────────────────────────
APPIMAGE_DIR="$PROJECT_DIR/build/appimage"
RELEASE_DIR="$PROJECT_DIR/release"
DOCS_DIR="$PROJECT_DIR/mpp-docs"
DOCS_PORT=5063
APP_VERSION="1.0.0"
APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
APPIMAGETOOL="$PROJECT_DIR/.tools/appimagetool"

# ── Farben ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ok()     { echo -e "  ${GREEN}✓${NC} $1"; }
warn()   { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail()   { echo -e "  ${RED}✗${NC} $1"; exit 1; }
info()   { echo -e "  ${CYAN}→${NC} $1"; }
header() { echo -e "\n${BOLD}═══ $1 ═══${NC}\n"; }

_ensure_appimagetool() {
  if [ -x "$APPIMAGETOOL" ]; then return 0; fi
  info "appimagetool wird heruntergeladen..."
  mkdir -p "$(dirname "$APPIMAGETOOL")"
  curl -fsSL "$APPIMAGETOOL_URL" -o "$APPIMAGETOOL"
  chmod +x "$APPIMAGETOOL"
  ok "appimagetool installiert unter .tools/"
}

cmd_serve() {
  if [ -f "$VENV_DIR/bin/activate" ]; then
      source "$VENV_DIR/bin/activate"
  else
      echo "ERROR: venv not found at $VENV_DIR" >&2
      exit 1
  fi
  cd "$MPP_DIR"
  exec python manage.py runserver 8000
}

cmd_appimage() {
  header "MPP Django — AppImage Build"

  if [ ! -d "$VENV_DIR" ]; then
    fail "venv nicht vorhanden — bitte zuerst Setup ausfuehren"
  fi

  _ensure_appimagetool

  local appdir="$APPIMAGE_DIR/LucentMPPDjango.AppDir"

  info "AppDir vorbereiten..."
  rm -rf "$appdir"
  mkdir -p "$appdir/usr/share/icons/hicolor/256x256/apps"
  mkdir -p "$appdir/usr/share/applications"
  mkdir -p "$appdir/app"

  info "Django-Projekt kopieren..."
  cp -r "$MPP_DIR" "$appdir/app/mpp"
  [ -f "$PROJECT_DIR/requirements.txt" ] && cp "$PROJECT_DIR/requirements.txt" "$appdir/app/"

  info "Python venv kopieren (kann dauern)..."
  cp -r "$VENV_DIR" "$appdir/venv"

  cat > "$appdir/usr/share/icons/hicolor/256x256/apps/lucent-mpp-django.svg" << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="40" fill="#041208"/>
  <rect x="58" y="58" width="140" height="100" rx="10" fill="none" stroke="#092E20" stroke-width="4"/>
  <text x="128" y="118" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#092E20">MPP</text>
  <rect x="78" y="172" width="100" height="24" rx="6" fill="none" stroke="#1B5E20" stroke-width="3"/>
  <text x="128" y="190" text-anchor="middle" font-family="sans-serif" font-size="14" fill="#2E7D32">Django</text>
</svg>
SVGEOF
  cp "$appdir/usr/share/icons/hicolor/256x256/apps/lucent-mpp-django.svg" \
     "$appdir/lucent-mpp-django.svg"

  cat > "$appdir/lucent-mpp-django.desktop" << DEOF
[Desktop Entry]
Type=Application
Name=Lucent MPP Django
Comment=Marketplace Portal — Django
Exec=AppRun
Icon=lucent-mpp-django
Categories=Development;Office;
Terminal=false
DEOF
  cp "$appdir/lucent-mpp-django.desktop" "$appdir/usr/share/applications/"

  cat > "$appdir/AppRun" << 'RUNEOF'
#!/usr/bin/env bash
SELF="$(readlink -f "${BASH_SOURCE[0]}")"
HERE="$(dirname "$SELF")"
PORT=8000
for arg in "$@"; do
  case "$arg" in --port=*) PORT="${arg#--port=}";; esac
done
source "${HERE}/venv/bin/activate"
cd "${HERE}/app/mpp"
exec python manage.py runserver "$PORT"
RUNEOF
  chmod +x "$appdir/AppRun"

  local output="$PROJECT_DIR/build/Lucent-MPP-Django-${APP_VERSION}-x86_64.AppImage"
  info "AppImage erzeugen..."
  ARCH=x86_64 "$APPIMAGETOOL" "$appdir" "$output" 2>&1 | tail -3
  ok "AppImage erstellt: ${BOLD}${output}${NC}"

  mkdir -p "$RELEASE_DIR"
  cp "$output" "$RELEASE_DIR/"
  ok "Kopiert nach ${BOLD}${RELEASE_DIR}/$(basename "$output")${NC}"
}

cmd_docs_appimage() {
  header "MPP Django — Docs AppImage Build"

  if [ ! -d "$DOCS_DIR/site" ]; then
    fail "Dokumentation nicht gebaut — bitte zuerst Docs bauen"
  fi

  _ensure_appimagetool

  local appdir="$APPIMAGE_DIR/LucentMPPDjangoDocs.AppDir"

  info "Docs AppDir vorbereiten..."
  rm -rf "$appdir"
  mkdir -p "$appdir/usr/share/icons/hicolor/256x256/apps"
  mkdir -p "$appdir/usr/share/applications"

  cp -r "$DOCS_DIR/site" "$appdir/site"

  cat > "$appdir/usr/share/icons/hicolor/256x256/apps/lucent-mpp-django-docs.svg" << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="40" fill="#041208"/>
  <rect x="68" y="58" width="120" height="140" rx="8" fill="none" stroke="#092E20" stroke-width="4"/>
  <line x1="92" y1="98" x2="164" y2="98" stroke="#1B5E20" stroke-width="3"/>
  <line x1="92" y1="122" x2="164" y2="122" stroke="#1B5E20" stroke-width="3"/>
  <line x1="92" y1="146" x2="140" y2="146" stroke="#1B5E20" stroke-width="3"/>
</svg>
SVGEOF
  cp "$appdir/usr/share/icons/hicolor/256x256/apps/lucent-mpp-django-docs.svg" \
     "$appdir/lucent-mpp-django-docs.svg"

  cat > "$appdir/lucent-mpp-django-docs.desktop" << DEOF
[Desktop Entry]
Type=Application
Name=Lucent MPP Django Docs
Comment=Dokumentation fuer MPP Django
Exec=AppRun
Icon=lucent-mpp-django-docs
Categories=Documentation;
Terminal=false
DEOF
  cp "$appdir/lucent-mpp-django-docs.desktop" "$appdir/usr/share/applications/"

  cat > "$appdir/AppRun" << 'RUNEOF'
#!/usr/bin/env bash
SELF="$(readlink -f "${BASH_SOURCE[0]}")"
HERE="$(dirname "$SELF")"
PORT="${DOCS_PORT:-5063}"
for arg in "$@"; do
  case "$arg" in --port=*) PORT="${arg#--port=}";; esac
done
if ! command -v python3 &>/dev/null; then
  echo "[ERROR] python3 nicht gefunden."
  exit 1
fi
cleanup() { kill "$SERVER_PID" 2>/dev/null; exit 0; }
trap cleanup SIGTERM SIGINT
cd "${HERE}/site"
python3 -m http.server "$PORT" --bind 127.0.0.1 &
SERVER_PID=$!
echo "[Docs] http://127.0.0.1:${PORT}"
if [[ "$*" != *"--port="* ]]; then
  sleep 0.5
  xdg-open "http://127.0.0.1:${PORT}" 2>/dev/null || true
fi
wait "$SERVER_PID"
RUNEOF
  chmod +x "$appdir/AppRun"

  local output="$PROJECT_DIR/build/Lucent-MPP-Django-Docs-${APP_VERSION}-x86_64.AppImage"
  info "Docs AppImage erzeugen..."
  ARCH=x86_64 "$APPIMAGETOOL" "$appdir" "$output" 2>&1 | tail -3
  ok "Docs AppImage erstellt: ${BOLD}${output}${NC}"

  mkdir -p "$RELEASE_DIR"
  cp "$output" "$RELEASE_DIR/"
  ok "Kopiert nach ${BOLD}${RELEASE_DIR}/$(basename "$output")${NC}"
}

# ══════════════════════════════════════════════════════════════════════════════
# CLI Dispatch
# ══════════════════════════════════════════════════════════════════════════════
case "${1:-serve}" in
  serve)           cmd_serve ;;
  appimage-build)  cmd_appimage ;;
  docs-appimage)   cmd_docs_appimage ;;
  *)
    echo "Usage: $0 [serve|appimage-build|docs-appimage]"
    exit 1
    ;;
esac
