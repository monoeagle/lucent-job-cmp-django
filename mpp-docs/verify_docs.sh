#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# verify_docs.sh — Doku-Abnahme-Gate (TDD) für MPP Django
#
# Setzt docs-release-sync.pattern §G um: Doku gilt NUR als fertig, wenn ALLE
# Regeln grün sind. Pro Regel ✓/✗; exit 0 nur bei null ✗, sonst exit 1.
# Läuft gegen das real gebaute site/-Artefakt (R-BUILD baut es strict neu).
#
#   ./verify_docs.sh            # voller Gate (inkl. strict Build via --ci)
#   ./verify_docs.sh --no-build # Build überspringen, nur Regeln gegen vorhandenes site/
# ══════════════════════════════════════════════════════════════════════════════
set -u

DOCS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$DOCS_DIR")"
PROJECTS_ROOT="$(dirname "$PROJECT_DIR")"
SITE="$DOCS_DIR/site"
JS_DIR="$DOCS_DIR/docs/javascripts"
HUB_YML="$PROJECT_DIR/lucent-hub.yml"
PY="$DOCS_DIR/.venv-docs/bin/python3"

DISPLAY_NAME="MPP-Django"
JS_FILES=(icon-rail.js activity-heatmap.js hub-stop.js mermaid.min.js mermaid-init.js palette-init.js lightbox.js)

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
FAILS=0
pass() { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; FAILS=$((FAILS+1)); }
rule() { echo -e "\n${CYAN}▸ $1${NC}"; }

NO_BUILD=false
[ "${1:-}" = "--no-build" ] && NO_BUILD=true

echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   MPP Django — Doku-Gate (TDD §G)       ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"

# ── R-BUILD ───────────────────────────────────────────────────────────────────
rule "R-BUILD — strict Build (build_docs.py --ci) Exit 0"
if $NO_BUILD; then
  echo "    (--no-build: übersprungen)"
elif [ ! -x "$PY" ] && [ ! -f "$PY" ]; then
  fail "R-BUILD: $PY nicht gefunden"
else
  if (cd "$DOCS_DIR" && "$PY" build_docs.py --ci >/tmp/mpp_docs_build.log 2>&1); then
    pass "R-BUILD: Build strict grün"
  else
    fail "R-BUILD: build_docs.py --ci Exit ≠ 0 (siehe /tmp/mpp_docs_build.log)"
  fi
fi

# ── R-PFLICHT ─────────────────────────────────────────────────────────────────
rule "R-PFLICHT — Pflichtdateien (lucent-docs.pattern §15)"
for f in zensical.toml build_docs.py run_mpp_docs.sh \
         tools/extract_mermaid_blocks.py tools/render_mermaid.sh tools/generate_project_activity.py; do
  [ -f "$DOCS_DIR/$f" ] && pass "$f" || fail "fehlt: $f"
done
for j in "${JS_FILES[@]}"; do
  [ -f "$JS_DIR/$j" ] && pass "javascripts/$j" || fail "fehlt: javascripts/$j"
done
css_lines=$(wc -l < "$DOCS_DIR/docs/stylesheets/extra.css" 2>/dev/null || echo 0)
[ "$css_lines" -gt 1000 ] && pass "extra.css Vollversion ($css_lines Z.)" || fail "extra.css zu klein ($css_lines Z., Platzhalter?)"

# ── R-VERSION ─────────────────────────────────────────────────────────────────
rule "R-VERSION — zensical.toml == lucent-hub.yml == icon-rail.js"
v_zen=$(grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' "$DOCS_DIR/zensical.toml" | head -1 | tr -d v)
v_hub=$(grep -E '^version:' "$HUB_YML" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
v_rail=$(grep -oE "APP_VERSION[^']*'[0-9]+\.[0-9]+\.[0-9]+'" "$JS_DIR/icon-rail.js" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
echo "    zensical=$v_zen  hub=$v_hub  rail=$v_rail"
if [ -n "$v_zen" ] && [ "$v_zen" = "$v_hub" ] && [ "$v_zen" = "$v_rail" ]; then
  pass "Version konsistent ($v_zen)"
else
  fail "Versions-Divergenz"
fi

# ── R-APPLOOK ─────────────────────────────────────────────────────────────────
rule "R-APPLOOK — extra_javascript (7 JS), keine Tabs, JS im site/"
for j in "${JS_FILES[@]}"; do
  grep -q "javascripts/$j" "$DOCS_DIR/zensical.toml" && pass "eingebunden: $j" || fail "nicht in extra_javascript: $j"
done
if grep -qE '^[^#]*"navigation\.tabs' "$DOCS_DIR/zensical.toml"; then
  fail "navigation.tabs/.tabs.sticky noch vorhanden"
else
  pass "keine navigation.tabs"
fi
for j in "${JS_FILES[@]}"; do
  [ -f "$SITE/javascripts/$j" ] && pass "site/javascripts/$j" || fail "fehlt im site/: $j"
done

# ── R-HOME ────────────────────────────────────────────────────────────────────
rule "R-HOME — Startseite ist NUR Home-Layout"
idx="$SITE/index.html"
if [ -f "$idx" ]; then
  grep -q 'data-adb-activity-heatmap' "$idx" && pass "Heatmap-Hook" || fail "kein data-adb-activity-heatmap"
  grep -q 'data-adb-activity-stats'   "$idx" && pass "Insights-Hook" || fail "kein data-adb-activity-stats"
  grep -qE 'images/mermaid/[^"]+\.svg' "$idx" && pass "Hero-<img>" || fail "kein Hero-SVG-<img>"
  if grep -qE 'Tech-Stack|Was kann|Was ist MPP' "$idx"; then
    fail "Fremdinhalt auf Startseite (Tech-Stack/Was-kann gehört auf eigene Seite)"
  else
    pass "kein ausgelagerter Fließtext auf Startseite"
  fi
else
  fail "site/index.html fehlt"
fi

# ── R-DIAGRAMME ───────────────────────────────────────────────────────────────
rule "R-DIAGRAMME — Hero-Flowchart + Gantt, valide, referenziert, Badge aktiv"
# Hero-SVG (aus index.html referenziert)
hero=$(grep -oE 'images/mermaid/[a-z0-9-]+\.svg' "$idx" 2>/dev/null | head -1)
if [ -n "$hero" ] && head -c 60 "$SITE/$hero" 2>/dev/null | grep -q '<svg'; then
  pass "Hero-SVG valide ($hero)"
else
  fail "Hero-SVG fehlt/invalide ($hero)"
fi
# Gantt-SVG (aus roadmapSvgUrl in icon-rail.js)
gantt=$(grep -oE "images/mermaid/[A-Za-z0-9_-]+\.svg" "$JS_DIR/icon-rail.js" | head -1)
if [ -n "$gantt" ] && ! echo "$gantt" | grep -q '__ROADMAP_GANTT__' && head -c 60 "$DOCS_DIR/docs/$gantt" 2>/dev/null | grep -q '<svg'; then
  pass "Gantt-SVG valide ($gantt)"
else
  fail "Gantt-SVG fehlt/Platzhalter ($gantt)"
fi
# addRoadmapBadge aktiv (nicht auskommentiert)
if grep -qE '^[^/]*addRoadmapBadge\(\);' "$JS_DIR/icon-rail.js"; then
  pass "addRoadmapBadge() aktiv"
else
  fail "addRoadmapBadge() auskommentiert/fehlt"
fi

# ── R-NO-PLACEHOLDER ──────────────────────────────────────────────────────────
rule "R-NO-PLACEHOLDER — keine ADAPT/__PROJEKT__/0.0.0-Reste in JS"
if grep -rEl '__PROJEKT__|__ROADMAP_GANTT__|ADAPT:|APP_VERSION[^=]*=[^=]*.0\.0\.0.' "$JS_DIR" >/dev/null 2>&1; then
  grep -rEn '__PROJEKT__|__ROADMAP_GANTT__|ADAPT:' "$JS_DIR" | head -5
  fail "Platzhalter-Reste in docs/javascripts/"
else
  pass "keine Platzhalter"
fi

# ── R-NO-CDN ──────────────────────────────────────────────────────────────────
rule "R-NO-CDN — kein externes script/link im site/"
if grep -rEl '<(script|link)[^>]*(src|href)="https?://' "$SITE" >/dev/null 2>&1; then
  grep -rEn '<(script|link)[^>]*(src|href)="https?://' "$SITE" | head -5
  fail "externe CDN-Referenz im site/"
else
  pass "alle Assets lokal"
fi

# ── R-STALE ───────────────────────────────────────────────────────────────────
rule "R-STALE — keine Alt-Version/Alt-Testzahl im site/"
# nur Content-HTML; vendored Libs (mermaid.min.js) + Changelog/Aktivität/Suche ausgenommen
stale=$(grep -rlE '228 Test|244 Test|Tests \| (228|244)|"testCount": (228|244)' "$SITE" --include=*.html 2>/dev/null | grep -vE 'changelog|project-activity|search' || true)
if [ -n "$stale" ]; then
  echo "$stale" | head -5
  fail "Alt-Zahl (228/244) im site/"
else
  pass "keine Alt-Zahlen"
fi

# ── R-APPIMAGE ────────────────────────────────────────────────────────────────
rule "R-APPIMAGE — frisch & byte-gleich in build/ release/ AppImages/"
AI="Lucent-${DISPLAY_NAME}-Docs-${v_zen}-x86_64.AppImage"
b="$PROJECT_DIR/build/$AI"; r="$PROJECT_DIR/release/$AI"; g="$PROJECTS_ROOT/AppImages/$AI"
if [ -f "$b" ] && [ -f "$r" ] && [ -f "$g" ] && cmp -s "$b" "$r" && cmp -s "$r" "$g"; then
  pass "build == release == AppImages ($AI)"
else
  fail "AppImage fehlt oder nicht byte-gleich (build/release/AppImages)"
fi

# ── R-AP-SYNC ─────────────────────────────────────────────────────────────────
rule "R-AP-SYNC — letztes AP in arbeitspakete.md == letztes AP in todo*"
AP_PAGE="$DOCS_DIR/docs/entwicklung/arbeitspakete.md"
TODO="$PROJECT_DIR/todo.md"; TODO_DONE="$PROJECT_DIR/todo-erledigt.md"
max_in() { grep -hoE 'AP[- ]?[0-9]+' "$@" 2>/dev/null | grep -oE '[0-9]+' | sort -n | tail -1; }
if [ -f "$AP_PAGE" ] && { [ -f "$TODO" ] || [ -f "$TODO_DONE" ]; }; then
  ap_page=$(max_in "$AP_PAGE")
  ap_todo=$(max_in "$TODO" "$TODO_DONE")
  echo "    arbeitspakete=$ap_page  todo*=$ap_todo"
  if [ -n "$ap_page" ] && [ "$ap_page" = "$ap_todo" ]; then
    pass "AP-Mirror konsistent (max AP $ap_page)"
  else
    fail "AP-Mirror divergiert"
  fi
else
  fail "arbeitspakete.md oder todo.md/todo-erledigt.md fehlt"
fi

# ── R-APPRUN ──────────────────────────────────────────────────────────────────
rule "R-APPRUN — Docs-AppImage-Laufzeit (§H): Ephemeral-Port + isolierter Browser"
RUNSH="$PROJECT_DIR/run.sh"
if [ -f "$RUNSH" ]; then
  grep -q 'pick_free_port'                 "$RUNSH" && pass "Ephemeral-Port (bind 0)"      || fail "kein Ephemeral-Port (fixer Port?)"
  grep -q -- '--app=' "$RUNSH" && grep -q 'user-data-dir' "$RUNSH" && pass "isolierte Browser-App-Instanz" || fail "keine isolierte Chromium-App-Instanz"
  grep -q -- '--no-browser'                "$RUNSH" && pass "--no-browser-Flag"            || fail "kein --no-browser-Flag"
  if grep -qE 'PORT="\$\{DOCS_PORT:-[0-9]+\}"' "$RUNSH"; then fail "fixer Default-Port im Standalone (§H verletzt)"; else pass "kein fixer Default-Port im Standalone"; fi
else
  fail "run.sh nicht gefunden"
fi

# ── Ergebnis ──────────────────────────────────────────────────────────────────
echo ""
if [ "$FAILS" -eq 0 ]; then
  echo -e "${GREEN}══ DOKU-GATE GRÜN — alle Regeln bestanden ══${NC}"
  exit 0
else
  echo -e "${RED}══ DOKU-GATE ROT — $FAILS Regel(n) gefallen → Doku NICHT fertig ══${NC}"
  exit 1
fi
