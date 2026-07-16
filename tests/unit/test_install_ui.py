"""Unit-Tests fuer deploy/ui.sh — Pruefbereich, Links/Ports und Menue-Panel.

Erhebung und Rendering sind strikt getrennt: die Render-Funktion bekommt ihre
Daten ueber stdin. Nur so laesst sich das Panel gegen erfundene Zustaende
testen ("nginx fehlt, PostgreSQL ist AppStream"), ohne dass irgendetwas
installiert sein muss.

Zwei Fallen, die hier abgesichert werden:
  * bash `printf %-20s` polstert nach BYTES, nicht nach Zeichen — mit UTF-8
    (✓, ═) wird die Box sonst schief.
  * Auf einer VM mit LANG=C gibt es kein UTF-8; dann muss ASCII raus, sonst
    steht da Buchstabensalat.
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

UI = Path(__file__).resolve().parents[2] / "deploy" / "ui.sh"

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run_ui(snippet, stdin="", env=None):
    script = f'set -euo pipefail\nsource "{UI}"\n{snippet}'
    base = dict(os.environ)
    base["NO_COLOR"] = "1"
    if env:
        base.update(env)
    return subprocess.run(
        ["bash", "-c", script], input=stdin, capture_output=True, text=True, env=base
    )


def sichtbare_breiten(ausgabe):
    """Sichtbare Zeichenbreite je Zeile (ohne ANSI-Sequenzen)."""
    return [len(ANSI.sub("", z)) for z in ausgabe.splitlines() if z.strip()]


DEMO = (
    "S|SYSTEM\n"
    "R|ok|python3.12|3.12.4\n"
    "R|ok|PostgreSQL|PGDG 16 · aktiv\n"
    "R|fail|nginx|nicht installiert\n"
    "S|LINKS & PORTS\n"
    "P|Portal|https://mpp.intern/  :443\n"
)


# ── Breite / Ausrichtung ──────────────────────────────────────────────────────


def test_alle_panel_zeilen_haben_dieselbe_breite():
    """Die UTF-8-Byte-Falle: ✓ ist 1 Zeichen, aber 3 Bytes."""
    r = run_ui('mpp_ui_render "MPP Django · Installer"', stdin=DEMO)

    assert r.returncode == 0, r.stderr
    breiten = set(sichtbare_breiten(r.stdout))
    assert len(breiten) == 1, f"Box ist schief, Breiten: {sorted(breiten)}\n{r.stdout}"


def test_panel_bleibt_buendig_wenn_umlaute_und_symbole_gemischt_sind():
    daten = "S|PRÜFUNG\nR|ok|Größe|übergroß · ✓ ok\nR|warn|nginx|fehlt\n"

    r = run_ui('mpp_ui_render "Prüfbereich"', stdin=daten)

    breiten = set(sichtbare_breiten(r.stdout))
    assert len(breiten) == 1, f"Breiten: {sorted(breiten)}\n{r.stdout}"


def test_zu_langer_text_sprengt_die_box_nicht():
    daten = "R|ok|einsehrlangername" + "x" * 60 + "|und ein sehr langes Detail" + "y" * 60 + "\n"

    r = run_ui('mpp_ui_render "Titel"', stdin=daten)

    assert r.returncode == 0, r.stderr
    breiten = set(sichtbare_breiten(r.stdout))
    assert len(breiten) == 1, f"lange Zeile sprengt die Box: {sorted(breiten)}"


def test_breite_ist_konfigurierbar():
    r = run_ui('mpp_ui_render "Titel"', stdin=DEMO, env={"MPP_UI_WIDTH": "60"})

    breiten = set(sichtbare_breiten(r.stdout))
    assert breiten == {60}, f"erwartet 60, bekam {sorted(breiten)}"


# ── Symbole / Zustaende ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "state,symbol", [("ok", "✓"), ("warn", "⚠"), ("fail", "✗"), ("unknown", "?")]
)
def test_symbol_je_zustand(state, symbol):
    r = run_ui(f"mpp_ui_symbol {state}")

    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == symbol


def test_unbekannter_zustand_wird_nicht_als_ok_gerendert():
    """Eine fehlgeschlagene Pruefung darf nie wie ein Erfolg aussehen."""
    r = run_ui('mpp_ui_render "Titel"', stdin="R|unknown|PostgreSQL|Prüfung fehlgeschlagen\n")

    assert "✓" not in r.stdout
    assert "?" in r.stdout


# ── ASCII-Fallback bei LANG=C ─────────────────────────────────────────────────


def test_ascii_fallback_wenn_locale_kein_utf8():
    """Auf einer VM mit LANG=C wuerden ✓ und ═ als Muell erscheinen."""
    e = {"LC_ALL": "C", "LANG": "C"}

    r = run_ui('mpp_ui_render "Titel"', stdin=DEMO, env=e)

    assert r.returncode == 0, r.stderr
    assert "✓" not in r.stdout and "═" not in r.stdout, "UTF-8 trotz LANG=C"
    assert "[OK]" in r.stdout, f"kein ASCII-Symbol gerendert:\n{r.stdout}"


def test_ascii_fallback_bleibt_buendig():
    e = {"LC_ALL": "C", "LANG": "C"}

    r = run_ui('mpp_ui_render "Titel"', stdin=DEMO, env=e)

    breiten = set(sichtbare_breiten(r.stdout))
    assert len(breiten) == 1, f"ASCII-Box ist schief: {sorted(breiten)}"


# ── Inhalt ────────────────────────────────────────────────────────────────────


def test_sektionsueberschrift_erscheint():
    r = run_ui('mpp_ui_render "Titel"', stdin=DEMO)

    assert "SYSTEM" in r.stdout
    assert "LINKS & PORTS" in r.stdout


def test_titel_erscheint():
    r = run_ui('mpp_ui_render "MPP Django · Installer"', stdin=DEMO)

    assert "MPP Django" in r.stdout


def test_plain_zeile_hat_kein_statussymbol():
    """Links/Ports sind keine Pruefungen — sie brauchen kein ✓/✗."""
    r = run_ui('mpp_ui_render "Titel"', stdin="P|Portal|https://mpp.intern/  :443\n")

    assert "https://mpp.intern/" in r.stdout
    for sym in ("✓", "✗", "⚠"):
        assert sym not in r.stdout, f"{sym} bei einer Plain-Zeile gerendert"


# ── NO_COLOR ─────────────────────────────────────────────────────────────────


def test_no_color_unterdrueckt_ansi_sequenzen():
    r = run_ui('mpp_ui_render "Titel"', stdin=DEMO, env={"NO_COLOR": "1"})

    assert "\x1b[" not in r.stdout, "ANSI trotz NO_COLOR"


def test_ohne_no_color_wird_koloriert():
    e = dict(os.environ)
    e.pop("NO_COLOR", None)
    script = f'set -euo pipefail\nsource "{UI}"\nmpp_ui_render "Titel"'
    r = subprocess.run(
        ["bash", "-c", script], input=DEMO, capture_output=True, text=True, env=e
    )

    assert "\x1b[" in r.stdout, "keine Farbe trotz aktivierter Kolorierung"
