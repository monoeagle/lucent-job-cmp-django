# _build — Doppel-Ausgabe-Build für den CMP-Guide

Erzeugt aus **einer** Markdown-Quelle (`docs/azubi-guide/*.md`) zwei Ausgaben:

- `build/html/` — gerenderte HTML-Vorschau: Mermaid als SVG (hell/dunkel), Lightbox
  (Galerie, ‹ › + Bildunterschrift), linke sticky Kapitel-Navigation, obere & untere
  Vor/Zurück-Leiste, zentrierte Bilder.
- `build/bookstack/` — BookStack-importierbares Markdown: Mermaid → PNG (`images/`),
  `<details>` → normale Abschnitte, Footer-Navigation entfernt, `.md`-Links zu Klartext.

## Bauen

```bash
cd docs/azubi-guide/_build
npm install marked @mermaid-js/mermaid-cli   # einmalig (lädt Chromium für Mermaid)
node build.js
# HTML-Vorschau öffnen: build/html/README.html
```

Der Build ist gecacht: Diagramme werden nur bei Änderung neu gerendert (schnelle Rebuilds).

## Dateien
- `build.js` — der Build (marked + mermaid-cli).
- `base.css` — Design-System (Farben, Typo, Layout, Lightbox-Styles).
- `extra.css` — Ergänzungen (Callout-Blockquotes, Sidebar, Seiten-Navigation).
- `lightbox.js` — Lightbox-Galerie + Mobile-Nav-Toggle.
