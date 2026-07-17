"""Unit-Tests fuer den HTTP/HTTPS-Auto-Modus des Installers (deploy/lib.sh).

Der Installer waehlt den Modus automatisch: liegt ein zum FQDN passendes
Zertifikat vor, laeuft HTTPS; sonst HTTP (kein TLS). Beide Modi muessen sich
konsistent durch env-Datei, nginx-Conf und Panel ziehen — sonst ist das Portal
ueber HTTP nicht benutzbar (Secure-Cookies verhindern den Login) oder das Panel
zeigt die falsche URL an.
"""
import subprocess
from pathlib import Path

LIB = Path(__file__).resolve().parents[2] / "deploy" / "lib.sh"


def run_sh(snippet, env=None):
    """Sourcet lib.sh und fuehrt `snippet` in bash aus."""
    script = f'set -euo pipefail\nsource "{LIB}"\n{snippet}'
    return subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, env=env
    )


# ── cmp_env_security_lines <fqdn> <mode> ──────────────────────────────────────
def test_env_security_lines_http_disables_secure_cookies():
    """HTTP-Modus: Redirect + Secure-Cookies AUS, CSRF-Origin auf http — sonst
    kommt das Session-/CSRF-Cookie ueber reines HTTP nie an und Login scheitert."""
    out = run_sh("cmp_env_security_lines cmp.intern http").stdout
    assert "CSRF_TRUSTED_ORIGINS=http://cmp.intern" in out
    assert "SECURE_SSL_REDIRECT=False" in out
    assert "SESSION_COOKIE_SECURE=False" in out
    assert "CSRF_COOKIE_SECURE=False" in out


def test_env_security_lines_https_keeps_secure_defaults():
    """HTTPS-Modus: CSRF-Origin auf https, KEINE Downgrade-Zeilen — die Cookies
    bleiben per production-Default sicher."""
    out = run_sh("cmp_env_security_lines cmp.intern https").stdout
    assert "CSRF_TRUSTED_ORIGINS=https://cmp.intern" in out
    assert "SESSION_COOKIE_SECURE=False" not in out
    assert "CSRF_COOKIE_SECURE=False" not in out
    assert "SECURE_SSL_REDIRECT=False" not in out


# ── cmp_render_nginx <fqdn> <app_dir> <mode> ──────────────────────────────────
def test_render_nginx_http_serves_on_80_without_tls():
    """HTTP-Modus: nginx proxyt direkt auf Port 80 — kein TLS, kein Redirect auf
    ein 443, das es ohne Zertifikat nicht gibt."""
    out = run_sh("cmp_render_nginx cmp.intern /opt/cmp/app http").stdout
    assert "listen 80" in out
    assert "proxy_pass http://127.0.0.1:8001" in out
    assert "server_name cmp.intern" in out
    assert "/opt/cmp/app/cmp/staticfiles/" in out
    assert "listen 443" not in out
    assert "return 301" not in out
    assert "ssl_certificate" not in out


def test_render_nginx_https_redirects_and_terminates_tls():
    """HTTPS-Modus: 80 leitet auf 443 um, 443 terminiert TLS mit dem cmp-Zert."""
    out = run_sh("cmp_render_nginx cmp.intern /opt/cmp/app https").stdout
    assert "return 301 https" in out
    assert "listen 443 ssl" in out
    assert "ssl_certificate /etc/pki/cmp/cmp.crt" in out
    assert "proxy_pass http://127.0.0.1:8001" in out


# ── cmp_portal_proto <nginx-conf> ─────────────────────────────────────────────
def test_portal_proto_https_when_conf_terminates_tls(tmp_path):
    """Aus der real geschriebenen Conf ableiten: 443 vorhanden -> https/443."""
    conf = tmp_path / "cmp.conf"
    conf.write_text("server { listen 443 ssl; server_name cmp.intern; }\n")
    assert run_sh(f"cmp_portal_proto {conf}").stdout.strip() == "https 443"


def test_portal_proto_http_when_only_port_80(tmp_path):
    """Nur Port 80 -> http/80 (nicht https behaupten)."""
    conf = tmp_path / "cmp.conf"
    conf.write_text("server { listen 80; server_name cmp.intern; }\n")
    assert run_sh(f"cmp_portal_proto {conf}").stdout.strip() == "http 80"


def test_portal_proto_empty_when_no_conf(tmp_path):
    """Keine Conf -> keine Ausgabe (nichts erfinden)."""
    assert run_sh(f"cmp_portal_proto {tmp_path}/gibtsnicht.conf").stdout.strip() == ""
