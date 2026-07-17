#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# verify_docs.sh — Doku-Abnahme-Gate (TDD) für CMP Django
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

DISPLAY_NAME="CMP-Django"
JS_FILES=(icon-rail.js activity-heatmap.js hub-stop.js mermaid.min.js mermaid-init.js palette-init.js lightbox.js)

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
FAILS=0
pass() { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; FAILS=$((FAILS+1)); }
rule() { echo -e "\n${CYAN}▸ $1${NC}"; }

NO_BUILD=false
[ "${1:-}" = "--no-build" ] && NO_BUILD=true

echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   CMP Django — Doku-Gate (TDD §G)       ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"

# ── R-BUILD ───────────────────────────────────────────────────────────────────
rule "R-BUILD — strict Build (build_docs.py --ci) Exit 0"
if $NO_BUILD; then
  echo "    (--no-build: übersprungen)"
elif [ ! -x "$PY" ] && [ ! -f "$PY" ]; then
  fail "R-BUILD: $PY nicht gefunden"
else
  if (cd "$DOCS_DIR" && "$PY" build_docs.py --ci >/tmp/cmp_docs_build.log 2>&1); then
    pass "R-BUILD: Build strict grün"
  else
    fail "R-BUILD: build_docs.py --ci Exit ≠ 0 (siehe /tmp/cmp_docs_build.log)"
  fi
fi

# ── R-PFLICHT ─────────────────────────────────────────────────────────────────
rule "R-PFLICHT — Pflichtdateien (lucent-docs.pattern §15)"
for f in zensical.toml build_docs.py run_cmp_docs.sh \
         tools/extract_mermaid_blocks.py tools/render_mermaid.sh tools/generate_project_activity.py; do
  [ -f "$DOCS_DIR/$f" ] && pass "$f" || fail "fehlt: $f"
done
for j in "${JS_FILES[@]}"; do
  [ -f "$JS_DIR/$j" ] && pass "javascripts/$j" || fail "fehlt: javascripts/$j"
done
css_lines=$(wc -l < "$DOCS_DIR/docs/stylesheets/extra.css" 2>/dev/null || echo 0)
[ "$css_lines" -gt 1000 ] && pass "extra.css Vollversion ($css_lines Z.)" || fail "extra.css zu klein ($css_lines Z., Platzhalter?)"

# ── R-VERSION ─────────────────────────────────────────────────────────────────
# run.sh gehört dazu: die Datei hatte APP_VERSION hartkodiert und stand auf
# 1.1.0, während lucent-hub.yml schon 1.2.0 sagte — die Regel prüfte diese
# Stelle nicht und meldete grün. Der AppImage-Dateiname kommt von dort.
rule "R-VERSION — zensical.toml == lucent-hub.yml == icon-rail.js == run.sh"
v_zen=$(grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' "$DOCS_DIR/zensical.toml" | head -1 | tr -d v)
v_hub=$(grep -E '^version:' "$HUB_YML" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
v_rail=$(grep -oE "APP_VERSION[^']*'[0-9]+\.[0-9]+\.[0-9]+'" "$JS_DIR/icon-rail.js" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
# Hartkodierten Wert vergleichen; leitet run.sh dagegen aus lucent-hub.yml ab,
# ist es per Konstruktion identisch (bevorzugte Form — keine vierte Stelle).
v_run=$(grep -oE 'APP_VERSION="[0-9]+\.[0-9]+\.[0-9]+"' "$PROJECT_DIR/run.sh" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
if [ -z "$v_run" ] && grep -q 'APP_VERSION=.*lucent-hub\.yml' "$PROJECT_DIR/run.sh"; then
  v_run="$v_hub"
fi
echo "    zensical=$v_zen  hub=$v_hub  rail=$v_rail  run.sh=$v_run"
if [ -n "$v_zen" ] && [ "$v_zen" = "$v_hub" ] && [ "$v_zen" = "$v_rail" ] && [ "$v_zen" = "$v_run" ]; then
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
  if grep -qE 'Tech-Stack|Was kann|Was ist CMP' "$idx"; then
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
# Vergleicht gegen die FRISCH erhobene Testzahl (pytest), nicht gegen
# hartkodierte Alt-Konstanten — die alte Regel suchte nach "228|244" aus einem
# längst vergangenen Release und prüfte nur *.html. Dadurch konnte im
# Header-Badge unbemerkt "239 Tests grün" stehen, während die Suite 317 zählte.
rule "R-STALE — Testzahl: pytest == icon-rail.js == site/ (HTML+JS)"
t_real=$("$PROJECT_DIR/venv/bin/python3" -m pytest --collect-only -q 2>/dev/null \
         | grep -oE '[0-9]+ tests? collected' | grep -oE '[0-9]+' | head -1)
t_rail=$(grep -oE 'TEST_COUNT[[:space:]]*=[[:space:]]*[0-9]+' "$JS_DIR/icon-rail.js" 2>/dev/null \
         | grep -oE '[0-9]+' | head -1)
echo "    pytest=${t_real:-?}  icon-rail.js=${t_rail:-?}"
if [ -z "$t_real" ]; then
  # Nicht still durchwinken: ohne Wahrheit kann die Regel nichts prüfen.
  fail "Testzahl nicht ermittelbar (pytest --collect-only) — Regel konnte nicht prüfen"
elif [ "$t_real" != "$t_rail" ]; then
  fail "icon-rail.js sagt ${t_rail:-?} Tests, pytest zählt $t_real"
else
  pass "Testzahl konsistent ($t_real)"
fi

if [ -n "$t_real" ]; then
  # Gebautes site/ gegen die Wahrheit prüfen — HTML *und* JS.
  # Ausgenommen, weil dort historische Zahlen korrekt sind: Changelog,
  # Aktivitätsdaten (Commit-Betreffs), Suchindex, Erkenntnisse; dazu vendored Libs.
  stale=$("$PY" - "$SITE" "$t_real" <<'PYEOF'
import re, sys, pathlib
site, want = pathlib.Path(sys.argv[1]), sys.argv[2]
SKIP = ('changelog', 'project-activity', 'search', 'mermaid.min',
        'insight', 'erkenntnis')
pat = re.compile(r'(\d+)\s+Tests?\s+(?:gr[üu]n|green)'
                 r'|TEST_COUNT\s*=\s*(\d+)'
                 r'|Tests</td><td>(\d+)')
bad = []
for p in sorted(site.rglob('*')):
    if not p.is_file() or p.suffix not in ('.html', '.js'):
        continue
    rel = str(p.relative_to(site))
    if any(s in rel.lower() for s in SKIP):
        continue
    for m in pat.finditer(p.read_text(errors='replace')):
        n = next(g for g in m.groups() if g)
        if n != want:
            bad.append(f"{rel}: '{m.group(0).strip()[:44]}' — pytest sagt {want}")
for b in bad[:5]:
    print(b)
PYEOF
)
  if [ -n "$stale" ]; then
    echo "$stale" | sed 's/^/    /'
    fail "Alt-Testzahl im site/ (HTML/JS)"
  else
    pass "site/ ohne Alt-Testzahlen"
  fi
fi

# ── R-DOCS-ZIP ────────────────────────────────────────────────────────────────
# Primäres Doku-Auslieferungsformat ist das statische HTML-ZIP (Windows-tauglich,
# offline: entpacken, index.html öffnen). Das Docs-AppImage ist nur noch optionale
# Linux-Variante (./run.sh docs-appimage) und wird hier NICHT mehr erzwungen.
# Die Version im Dateinamen erzwingt bei jedem Bump ein frisches ZIP.
rule "R-DOCS-ZIP — HTML-ZIP in release/, aktuelle Version, mit index.html"
ZIP="$PROJECT_DIR/release/Lucent-${DISPLAY_NAME}-Docs-${v_zen}-html.zip"
if [ ! -f "$ZIP" ]; then
  fail "HTML-ZIP fehlt: release/$(basename "$ZIP") — bauen mit ./run.sh docs-zip"
elif "$PY" -c "import zipfile,sys; sys.exit(0 if 'index.html' in zipfile.ZipFile(sys.argv[1]).namelist() else 1)" "$ZIP" 2>/dev/null; then
  pass "HTML-ZIP vollständig ($(basename "$ZIP"))"
else
  fail "HTML-ZIP ohne index.html an der Wurzel: $(basename "$ZIP")"
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
