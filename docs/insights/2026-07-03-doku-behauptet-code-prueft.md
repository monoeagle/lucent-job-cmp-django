# Insight: Wenn Doku und Code sich widersprechen, erst klären, welche Seite lügt

**Datum:** 2026-07-03 · **Session:** 4 · **Kontext:** Frage „was benutzen wir als Webserver?"

## Was passiert ist

Beim Beantworten der Webserver-Frage fiel eine scheinbare **Deployment-Lücke** auf:
`deploy/install.sh` startet gunicorn auf `config.wsgi` — aber CLAUDE.md führte
„Django Channels" als Stack-Bestandteil und die Oberflächen-Referenz behauptete,
Benachrichtigungen würden „über Django Channels (WebSocket) live ausgeliefert".
Erste Hypothese: *dem Deployment fehlt der ASGI-Baustein.*

Die Code-Prüfung drehte den Befund um: **Channels existiert im Projekt nicht.**
Kein `channels` in requirements/Wheelhouse, `config/asgi.py` ist Django-Default,
kein Consumer, kein `CHANNEL_LAYERS`, die Benachrichtigungs-Seite hat nicht mal
Polling. Das Deployment war korrekt — **die Doku war falsch**, geerbt aus dem
v1-Zielbild („Channels statt SSE"), das nie gebaut wurde.

## Die Lektion

1. **Ein Doku/Code-Widerspruch hat zwei mögliche Auflösungen.** Der Reflex „dann
   fehlt was im Deployment" nimmt die Doku als Grundwahrheit. Erst prüfen, welche
   Seite den Ist-Stand beschreibt — das ist dieselbe Regel wie „Spec ≠ Ist-Stand"
   (global etabliert 2026-06-20), nur rückwärts: auch *bestehende* Doku kann
   Zielbild-Prosa sein, die als Ist-Beschreibung verkleidet ist.
2. **Zielbild-Features gehören als benanntes AP in die Roadmap, nicht als
   Ist-Behauptung in Stack-Zeile/Referenz.** Fix: Behauptung korrigiert,
   **AP-12 · Live-Updates (Channels)** mit konkreten Schritten + DoD angelegt,
   Diagramme (Flowchart/Gantt/Architektur-Badge) nachgezogen.
3. **Gate-Lücke gefunden:** `R-APPIMAGE` prüft nur Byte-Gleichheit der drei
   AppImage-Kopien, nicht ob das AppImage die *aktuelle* Site enthält. Nach
   Doku-Änderungen also manuell `./run.sh docs-appimage` + Kopie nach
   `../AppImages/`. Kandidat für eine neue Gate-Regel (Frische-Check).

## Verifikation (geprüft, nicht geraten)

- `grep -ri channels requirements* mpp/` → nur `asgiref` (transitiv) — kein Channels.
- Gerenderte Artefakte gegengeprüft: AP-12 in beiden SVGs + `index-1.svg`
  („geplant AP-12" gestrichelt), Live-Site nach Deploy per `curl` verifiziert
  („noch nicht gebaut" sichtbar, „live ausgeliefert" weg).
