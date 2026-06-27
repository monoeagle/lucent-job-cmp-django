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
APP_VERSION="1.1.0"
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

_bundle_python_standalone() {
  local appdir="$1"
  local venv_dir="$2"

  local py_ver
  py_ver=$("$venv_dir/bin/python3" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  local real_py
  real_py="$(readlink -f "$venv_dir/bin/python3")"
  local py_base
  py_base=$("$venv_dir/bin/python3" -c 'import sys; print(sys.base_prefix)')

  info "Python ${py_ver} standalone buendeln..."

  mkdir -p "$appdir/python/bin"
  mkdir -p "$appdir/python/lib/python${py_ver}"

  cp "$real_py" "$appdir/python/bin/python3"
  chmod +x "$appdir/python/bin/python3"
  ln -sf python3 "$appdir/python/bin/python"

  info "Python stdlib kopieren..."
  cp -r "${py_base}/lib/python${py_ver}/"* "$appdir/python/lib/python${py_ver}/" 2>/dev/null || true

  info "Site-packages kopieren..."
  if [ -d "$venv_dir/lib/python${py_ver}/site-packages" ]; then
    cp -r "$venv_dir/lib/python${py_ver}/site-packages" "$appdir/python/lib/python${py_ver}/"
  fi

  for pattern in \
    "/usr/lib/x86_64-linux-gnu/libpython${py_ver}"*.so* \
    "/usr/lib/libpython${py_ver}"*.so* \
    "${py_base}/lib/libpython${py_ver}"*.so*; do
    for lib in $pattern; do
      [ -f "$lib" ] && cp -L "$lib" "$appdir/python/lib/" 2>/dev/null
    done
  done

  info "System-Bibliotheken buendeln..."
  for libname in libssl libcrypto libffi libz libsqlite3 libncurses libtinfo libreadline libbz2 liblzma libexpat libmpdec; do
    for f in /usr/lib/x86_64-linux-gnu/${libname}*.so*; do
      [ -f "$f" ] && cp -L "$f" "$appdir/python/lib/" 2>/dev/null
    done
  done


  # ALL shared library dependencies (automatic ldd scan)
  info "Shared-Library-Abhaengigkeiten scannen (ldd)..."
  local _deplist
  _deplist=$(find "$appdir/python" -name "*.so*" -type f -exec ldd {} 2>/dev/null \; | grep "=> /" | awk '{print $3}' | sort -u)
  local _copied=0
  for dep in $_deplist; do
    [ -f "$dep" ] || continue
    local _bn
    _bn=$(basename "$dep")
    # System-kritische Libs NICHT buendeln
    case "$_bn" in
      libc.so*|libm.so*|libdl.so*|librt.so*|libpthread.so*) continue ;;
      ld-linux*|libgcc_s.so*|libstdc++.so*) continue ;;
      libnss_*|libresolv.so*|libnsl.so*|libutil.so*) continue ;;
      linux-vdso.so*) continue ;;
    esac
    if [ ! -f "$appdir/python/lib/$_bn" ]; then
      cp -L "$dep" "$appdir/python/lib/" 2>/dev/null && _copied=$((_copied + 1))
    fi
  done
  # Bereits faelschlich kopierte System-Libs entfernen
  for _syslib in libc.so* libm.so* libdl.so* librt.so* libpthread.so* ld-linux* libgcc_s.so* libstdc++.so* libnss_* libresolv.so* libnsl.so* libutil.so*; do
    rm -f "$appdir/python/lib/"$_syslib 2>/dev/null
  done
  info "$_copied zusaetzliche Shared Libraries gebundelt"
  ok "Python ${py_ver} standalone gebundelt"
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

  _bundle_python_standalone "$appdir" "$VENV_DIR"

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
export PYTHONHOME="${HERE}/python"
export PATH="${HERE}/python/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/python/lib:${LD_LIBRARY_PATH:-}"
PY_VER=$(ls -1 "${HERE}/python/lib/" | grep "^python3\." | head -1 | sed "s/python//")
export PYTHONPATH="${HERE}/python/lib/python${PY_VER}/site-packages"
export DJANGO_SETTINGS_MODULE=config.settings.development

cd "${HERE}/app/mpp"

# Beim ersten Start: Migrationen + Seed
STAMP="${HOME}/.lucent-mpp-django-seeded"
if [ ! -f "$STAMP" ]; then
  echo "[MPP-Django] Erststart: Datenbank initialisieren..."
  PGPASSWORD=mpp createdb -h localhost -U mpp mpp_django_dev 2>/dev/null || true
  echo "[MPP-Django] Migrationen..."
  "${HERE}/python/bin/python3" manage.py migrate --noinput 2>&1 | tail -5
  echo "[MPP-Django] Seed-Daten..."
  "${HERE}/python/bin/python3" manage.py seed 2>&1 | tail -5
  touch "$STAMP"
  echo "[MPP-Django] Datenbank bereit."
fi

# Browser oeffnen (nur ohne --port)
if [[ "$*" != *"--port="* ]]; then
  (sleep 2 && xdg-open "http://127.0.0.1:${PORT}" 2>/dev/null) &
fi

echo "[MPP-Django] http://127.0.0.1:${PORT}"
exec "${HERE}/python/bin/python3" manage.py runserver "$PORT"
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
# Standalone-Docs-AppImage-Laufzeit (docs-release-sync.pattern §H):
#  --port=NNNN        fixer Port (Hub-Modus) → KEIN Browser
#  --port-prefer=NNNN Wunschport, sonst zufaelliger Ephemeral-Port
#  --no-browser       nur Server, kein Browser
# Standalone: OS-vergebener Ephemeral-Port (nie Kollision) + isolierte Chromium-App-Instanz.
SELF="$(readlink -f "${BASH_SOURCE[0]}")"
HERE="$(dirname "$SELF")"

PORT=""; PREFER=""; NO_BROWSER=0; HUB_MODE=0
for arg in "$@"; do
  case "$arg" in
    --port=*)        PORT="${arg#--port=}"; HUB_MODE=1 ;;
    --port-prefer=*) PREFER="${arg#--port-prefer=}" ;;
    --no-browser)    NO_BROWSER=1 ;;
  esac
done

if ! command -v python3 &>/dev/null; then
  echo "[ERROR] python3 nicht gefunden."; exit 1
fi

pick_free_port() {
  python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()'
}
port_in_use() { (echo >"/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1; }

# Port waehlen: Hub=fix; sonst Wunschport (falls frei), sonst Ephemeral.
if [ -z "$PORT" ]; then
  if [ -n "$PREFER" ] && ! port_in_use "$PREFER"; then PORT="$PREFER"; else PORT="$(pick_free_port)"; fi
fi

PROFILE=""
cleanup() {
  kill "$SERVER_PID" 2>/dev/null
  [ -n "$PROFILE" ] && rm -rf "$PROFILE" 2>/dev/null
  exit 0
}
trap cleanup SIGTERM SIGINT EXIT

cd "${HERE}/site"
python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &
SERVER_PID=$!
URL="http://127.0.0.1:${PORT}"
echo "[Docs] $URL"

# Browser nur im Standalone (Hub oeffnet selbst, --no-browser unterdrueckt).
if [ "$HUB_MODE" -eq 0 ] && [ "$NO_BROWSER" -eq 0 ]; then
  sleep 0.5
  CHROME=""
  for c in chromium chromium-browser google-chrome google-chrome-stable chrome brave-browser; do
    if command -v "$c" &>/dev/null; then CHROME="$c"; break; fi
  done
  if [ -n "$CHROME" ]; then
    PROFILE="$(mktemp -d)"
    "$CHROME" --user-data-dir="$PROFILE" --no-first-run --no-default-browser-check \
              --new-window --app="$URL" >/dev/null 2>&1 &
  else
    xdg-open "$URL" >/dev/null 2>&1 || true   # Fallback, wenn kein Chromium/Chrome
  fi
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

cmd_release() {
  header "MPP Django — Offline-Release (AlmaLinux 9)"
  local wheels_dir="$PROJECT_DIR/wheels"
  if [ -z "$(ls "$wheels_dir"/*.whl 2>/dev/null)" ]; then
    info "Wheelhouse leer — Wheels für AlmaLinux 9 / Py3.12 laden..."
    "$VENV_DIR/bin/python3" -m pip download \
      -r "$PROJECT_DIR/requirements/production.txt" --dest "$wheels_dir" \
      --only-binary=:all: --python-version 312 --implementation cp --abi cp312 \
      --platform manylinux2014_x86_64 --platform manylinux_2_17_x86_64 --platform manylinux_2_28_x86_64
    "$VENV_DIR/bin/python3" -m pip download pip setuptools wheel --dest "$wheels_dir" --only-binary=:all:
  fi
  "$VENV_DIR/bin/python3" "$PROJECT_DIR/tools/build_release.py"
}

# ══════════════════════════════════════════════════════════════════════════════
# CLI Dispatch
# ══════════════════════════════════════════════════════════════════════════════
case "${1:-serve}" in
  serve)           cmd_serve ;;
  appimage-build)  cmd_appimage ;;
  docs-appimage)   cmd_docs_appimage ;;
  release)         cmd_release ;;
  *)
    echo "Usage: $0 [serve|appimage-build|docs-appimage|release]"
    exit 1
    ;;
esac
