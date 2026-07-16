# ══════════════════════════════════════════════════════════════════════════════
# ui.sh — Pruefbereich, Links/Ports und Menue-Panel des MPP-Installers
#
# Strikt getrennt von der Erhebung: mpp_ui_render bekommt seine Daten ueber
# stdin und weiss nichts davon, wie sie zustande kamen. Dadurch ist das Panel
# gegen beliebige Zustaende testbar, ohne dass etwas installiert sein muss.
#
# Datenformat (eine Zeile je Eintrag):
#   S|<Ueberschrift>                  Sektion
#   R|<zustand>|<name>|<detail>       Zeile mit Statussymbol
#                                     zustand: ok | warn | fail | unknown
#   P|<name>|<detail>                 Zeile ohne Symbol (Links/Ports)
#
# Zwei Fallstricke, die hier bewusst behandelt werden:
#   * `printf %-20s` polstert nach BYTES. "✓" ist 1 Zeichen, aber 3 Bytes —
#     damit waere die Box schief. Deshalb wird ueber ${#s} (Zeichen) gepolstert.
#   * Ohne UTF-8-Locale (LANG=C, auf VMs ueblich) wuerden ✓/═ als Muell
#     erscheinen. Dann ASCII.
# ══════════════════════════════════════════════════════════════════════════════

MPP_UI_WIDTH="${MPP_UI_WIDTH:-46}"

# mpp_ui_unicode_ok — wahr, wenn die Locale UTF-8 kann.
mpp_ui_unicode_ok() {
    case "${LC_ALL:-${LC_CTYPE:-${LANG:-}}}" in
        *UTF-8* | *utf8* | *UTF8* | *utf-8*) return 0 ;;
        *) return 1 ;;
    esac
}

# mpp_ui_symbol <zustand>
mpp_ui_symbol() {
    if mpp_ui_unicode_ok; then
        case "$1" in
            ok) printf '✓' ;;
            warn) printf '⚠' ;;
            fail) printf '✗' ;;
            *) printf '?' ;;
        esac
    else
        case "$1" in
            ok) printf '[OK]' ;;
            warn) printf '[!!]' ;;
            fail) printf '[XX]' ;;
            *) printf '[??]' ;;
        esac
    fi
}

_mpp_ui_color() {
    [ -n "${NO_COLOR:-}" ] && return 0
    case "$1" in
        ok) printf '\033[0;32m' ;;
        warn) printf '\033[1;33m' ;;
        fail) printf '\033[0;31m' ;;
        unknown) printf '\033[0;36m' ;;
        reset) printf '\033[0m' ;;
    esac
}

# _mpp_ui_ascii <text> — Inhalt nach ASCII bringen.
# Noetig, weil ${#s} ohne UTF-8-Locale BYTES zaehlt: "PGDG 16 · aktiv" ergibt
# dort 16 statt 15 und die Box waere eine Spalte schief.
_mpp_ui_ascii() {
    local t="$1"
    t="${t//·/-}"
    t="${t//→/->}"
    t="${t//✓/OK}"
    t="${t//⚠/!}"
    t="${t//✗/X}"
    printf '%s' "$t" | LC_ALL=C tr -cd '\11\40-\176'
}

# _mpp_ui_text <text> — Inhalt passend zur Locale aufbereiten.
_mpp_ui_text() {
    if mpp_ui_unicode_ok; then
        printf '%s' "$1"
    else
        _mpp_ui_ascii "$1"
    fi
}

# _mpp_ui_pad <text> <breite> — auf <breite> ZEICHEN polstern oder kuerzen.
# WICHTIG: explizites `return 0`. Mit `[ $pad -gt 0 ] && printf ...` als letztem
# Befehl liefert die Funktion bei pad==0 eine 1 zurueck — unter `set -e` (das
# install.sh nutzt) reisst das den ganzen Installer mit.
_mpp_ui_pad() {
    local text="$1" width="$2"
    if [ "${#text}" -gt "$width" ]; then
        # Kuerzen mit Auslassung, damit die Box nie gesprengt wird.
        if [ "$width" -ge 2 ]; then
            text="${text:0:$((width - 2))}.."
        else
            text="${text:0:$width}"
        fi
    fi
    local pad=$((width - ${#text}))
    printf '%s' "$text"
    if [ "$pad" -gt 0 ]; then
        printf '%*s' "$pad" ''
    fi
    return 0
}

# _mpp_ui_line <inhalt> — eine Rahmenzeile mit gepolstertem Inhalt.
_mpp_ui_line() {
    local v_border h_inner
    if mpp_ui_unicode_ok; then v_border='║'; else v_border='|'; fi
    h_inner=$((MPP_UI_WIDTH - 4))
    printf '%s ' "$v_border"
    _mpp_ui_pad "$1" "$h_inner"
    printf ' %s\n' "$v_border"
}

# ══════════════════════════════════════════════════════════════════════════════
# Status-Erhebung — liefert NUR Daten im Render-Format, keine Ausgabe.
# Getrennt vom Rendering, damit das Panel gegen erfundene Zustaende testbar ist.
# ══════════════════════════════════════════════════════════════════════════════

# mpp_status_python
mpp_status_python() {
    local py="${MPP_PY:-python3.12}" ver
    if ! command -v "$py" >/dev/null 2>&1; then
        printf 'R|fail|%s|nicht gefunden\n' "$py"
        return 0
    fi
    ver="$("$py" -c 'import sys;print("%d.%d.%d"%sys.version_info[:3])' 2>/dev/null)" || ver=""
    if [ -z "$ver" ]; then
        printf 'R|unknown|%s|Version nicht ermittelbar\n' "$py"
    else
        printf 'R|ok|%s|%s\n' "$py" "$ver"
    fi
}

# mpp_status_postgres — zeigt die erkannte Variante, nicht eine geratene.
mpp_status_postgres() {
    local sc="${MPP_SYSTEMCTL:-systemctl}" flavor label svc
    if ! flavor="$(mpp_pg_flavor 2>/dev/null)"; then
        printf 'R|fail|PostgreSQL|nicht installiert\n'
        return 0
    fi
    case "$flavor" in
        pgdg) label="PGDG 16" ;;
        appstream) label="AppStream" ;;
        *) label="$flavor" ;;
    esac
    svc="$(mpp_pg_service 2>/dev/null)" || svc=""
    if [ -n "$svc" ] && $sc is-active --quiet "$svc" 2>/dev/null; then
        printf 'R|ok|PostgreSQL|%s · aktiv\n' "$label"
    else
        printf 'R|warn|PostgreSQL|%s · inaktiv\n' "$label"
    fi
}

# mpp_status_redis
mpp_status_redis() {
    local sc="${MPP_SYSTEMCTL:-systemctl}"
    if $sc is-active --quiet redis 2>/dev/null; then
        printf 'R|ok|Redis|aktiv\n'
    else
        printf 'R|warn|Redis|inaktiv\n'
    fi
}

# mpp_status_nginx
mpp_status_nginx() {
    if mpp_nginx_present; then
        printf 'R|ok|nginx|installiert\n'
    else
        printf 'R|fail|nginx|nicht installiert\n'
    fi
}

# mpp_status_service <unit>
mpp_status_service() {
    local sc="${MPP_SYSTEMCTL:-systemctl}" unit="$1"
    if $sc is-active --quiet "$unit" 2>/dev/null; then
        printf 'R|ok|%s|aktiv\n' "$unit"
    else
        printf 'R|fail|%s|inaktiv\n' "$unit"
    fi
}

# mpp_status_app <app-verzeichnis>
# Die Version kommt aus der VERSION-Datei, die der Release-Build ins Bundle legt
# und install.sh mitinstalliert. Fehlt sie (aeltere Installation), wird das als
# "unbekannt" gemeldet — nicht geraten.
mpp_status_app() {
    local app="$1" ver
    if [ ! -d "$app" ]; then
        printf 'R|fail|%s|nicht installiert\n' "$app"
        return 0
    fi
    if [ -f "$app/VERSION" ]; then
        ver="$(head -n1 "$app/VERSION" | tr -d '[:space:]')"
        printf 'R|ok|%s|v%s\n' "$app" "$ver"
    else
        printf 'R|warn|%s|Version unbekannt\n' "$app"
    fi
}

# mpp_status_database <rolle> <datenbank>
mpp_status_database() {
    local role="$1" db="$2" psql="${MPP_PSQL:-}"
    if [ -z "$psql" ]; then
        psql="sudo -u postgres $(mpp_psql_bin 2>/dev/null)" || {
            printf 'R|unknown|Datenbank|nicht prüfbar\n'
            return 0
        }
    fi
    if $psql -tAc "SELECT 1 FROM pg_database WHERE datname='${db}'" 2>/dev/null | grep -q 1; then
        printf 'R|ok|Datenbank|%s\n' "$db"
    else
        printf 'R|fail|Datenbank|%s fehlt\n' "$db"
    fi
}

# mpp_status_links <env-datei>
# Der FQDN kommt aus ALLOWED_HOSTS. Gibt es ihn nicht, wird keine URL erfunden.
mpp_status_links() {
    local envfile="$1" fqdn
    fqdn="$(mpp_env_get "$envfile" ALLOWED_HOSTS)"
    fqdn="${fqdn%%,*}"

    printf 'S|LINKS & PORTS\n'
    if [ -n "$fqdn" ]; then
        printf 'P|Portal|https://%s/  :443\n' "$fqdn"
        printf 'P|Admin|https://%s/admin/\n' "$fqdn"
    else
        printf 'P|Portal|noch nicht installiert\n'
    fi
    printf 'P|gunicorn|127.0.0.1:8001  :8001\n'
    printf 'P|PostgreSQL|127.0.0.1:5432  :5432\n'
    printf 'P|Redis|localhost:6379  :6379\n'
}

# mpp_ui_render <titel>  — Daten kommen ueber stdin.
mpp_ui_render() {
    local titel="$1" zeile typ zustand name detail
    local tl tr bl br hz vb
    if mpp_ui_unicode_ok; then
        tl='╔'; tr='╗'; bl='╚'; br='╝'; hz='═'; vb='║'
    else
        tl='+'; tr='+'; bl='+'; br='+'; hz='-'; vb='|'
    fi

    # Kopfzeile: Titel in die obere Rahmenlinie einbetten.
    titel="$(_mpp_ui_text "$titel")"
    local kopf="${hz} ${titel} "
    local rest=$((MPP_UI_WIDTH - 2 - ${#kopf}))
    [ "$rest" -lt 0 ] && rest=0
    printf '%s%s' "$tl" "$kopf"
    local i=0
    while [ "$i" -lt "$rest" ]; do printf '%s' "$hz"; i=$((i + 1)); done
    printf '%s\n' "$tr"

    while IFS= read -r zeile || [ -n "$zeile" ]; do
        [ -n "$zeile" ] || continue
        typ="${zeile%%|*}"
        case "$typ" in
            S)
                _mpp_ui_line "$(_mpp_ui_text "${zeile#S|}")"
                ;;
            R)
                local restz="${zeile#R|}"
                zustand="${restz%%|*}"; restz="${restz#*|}"
                name="$(_mpp_ui_text "${restz%%|*}")"; detail="$(_mpp_ui_text "${restz#*|}")"
                local sym; sym="$(mpp_ui_symbol "$zustand")"
                # Farbe nur um das Symbol, deshalb Zeile manuell zusammensetzen
                # statt ueber _mpp_ui_line: ANSI-Sequenzen wuerden sonst in die
                # Breitenrechnung einfliessen und die Box verziehen.
                local h_inner=$((MPP_UI_WIDTH - 4))
                printf '%s ' "$vb"
                printf '  '
                _mpp_ui_color "$zustand"; printf '%s' "$sym"; _mpp_ui_color reset
                printf ' '
                _mpp_ui_pad "$(_mpp_ui_pad "$name" 15) ${detail}" "$((h_inner - 3 - ${#sym}))"
                printf ' %s\n' "$vb"
                ;;
            P)
                local restp="${zeile#P|}"
                name="$(_mpp_ui_text "${restp%%|*}")"; detail="$(_mpp_ui_text "${restp#*|}")"
                _mpp_ui_line "  $(_mpp_ui_pad "$name" 12) ${detail}"
                ;;
        esac
    done

    printf '%s' "$bl"
    i=0
    while [ "$i" -lt $((MPP_UI_WIDTH - 2)) ]; do printf '%s' "$hz"; i=$((i + 1)); done
    printf '%s\n' "$br"
}
