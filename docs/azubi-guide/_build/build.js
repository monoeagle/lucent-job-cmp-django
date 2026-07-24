/* Dual build: one markdown source -> (1) HTML with Mermaid+Lightbox, (2) BookStack-ready .md */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { marked } = require('marked');

const SRC = path.resolve(__dirname, '..');
const ROOT = __dirname;
const OUT_HTML = path.join(ROOT, 'build', 'html');
const OUT_BS = path.join(ROOT, 'build', 'bookstack');
const OUT_BS_IMG = path.join(OUT_BS, 'images');
const CACHE = path.join(ROOT, '.mmcache');
[OUT_HTML, OUT_BS_IMG, CACHE].forEach(d => fs.mkdirSync(d, { recursive: true }));

const MMDC = path.join(ROOT, 'node_modules', '@mermaid-js', 'mermaid-cli', 'src', 'cli.js');

const CAPTIONS = {
  '01': 'Kontext: Wer nutzt CMP — und die Wertschöpfungskette Katalog → Abo',
  '02': 'Die Modellkette der Fachdomäne, inkl. der Kontext-Regeln aus der App cmdb',
  '04': 'Zustandsdiagramm der Order — erzeugt aus TRANSITIONS in core/domain/value_objects.py',
  '05': 'Die Schichten eines HTTP-Requests: views → forms/services → models → core',
  '06': 'Provisioning-Ablauf: die Celery-Naht zwischen Web-Request und Worker',
  '11': 'Laufzeit-Topologie in Produktion: nginx · gunicorn · Celery · PostgreSQL · Redis',
};

const CFG = "'flowchart':{'htmlLabels':true,'padding':16,'nodeSpacing':60,'rankSpacing':66,'diagramPadding':12},'sequence':{'boxMargin':14,'noteMargin':12,'messageMargin':40},'er':{'entityPadding':18}";
const LIGHT_INIT = "%%{init: {'theme':'base','themeVariables':{'primaryColor':'#eef2f6','primaryTextColor':'#24384a','primaryBorderColor':'#94a9bc','lineColor':'#64788a'}," + CFG + "}}%%\n";
const DARK_INIT  = "%%{init: {'theme':'base','themeVariables':{'primaryColor':'#1a2634','primaryTextColor':'#cdd9e4','primaryBorderColor':'#4a637a','lineColor':'#7d93a6'}," + CFG + "}}%%\n";

function mmdc(inFile, outFile, extra) {
  execSync(`node "${MMDC}" -i "${inFile}" -o "${outFile}" ${extra}`, { stdio: 'ignore' });
}
function renderSVG(code, init, key) {
  const mmf = path.join(CACHE, key + '.mmd');
  const svgf = path.join(CACHE, key + '.svg');
  const src = init + code;
  if (!(fs.existsSync(svgf) && fs.existsSync(mmf) && fs.readFileSync(mmf, 'utf8') === src)) {
    fs.writeFileSync(mmf, src);
    mmdc(mmf, svgf, '-b transparent -w 1200');
  }
  let svg = fs.readFileSync(svgf, 'utf8').trim();
  const m = svg.match(/<svg[^>]*\sid="([^"]+)"/);
  if (m) svg = svg.split(m[1]).join('x' + key);
  return svg;
}
function renderPNG(code, key) {
  const mmf = path.join(CACHE, key + '_png.mmd');
  const pngf = path.join(OUT_BS_IMG, key + '.png');
  const src = LIGHT_INIT + code;
  if (!(fs.existsSync(pngf) && fs.existsSync(mmf) && fs.readFileSync(mmf, 'utf8') === src)) {
    fs.writeFileSync(mmf, src);
    mmdc(mmf, pngf, '-b white -w 1600 -s 2');
  }
  return key + '.png';
}

const MERMAID_RE = /```mermaid\s*\n([\s\S]*?)```/g;
const files = fs.readdirSync(SRC).filter(f => f.endsWith('.md')).sort();

// design system CSS from the preview file + extras
const BASE_CSS = fs.readFileSync(path.join(ROOT, 'base.css'), 'utf8');
const EXTRA_CSS = fs.readFileSync(path.join(ROOT, 'extra.css'), 'utf8');
const LIGHTBOX_JS = fs.readFileSync(path.join(ROOT, 'lightbox.js'), 'utf8');

function styleCallouts(html) {
  return html.replace(/<blockquote>\s*<p>\s*(💡|⚠️|🔍|🚧)/g, (mm, e) => {
    const cls = e === '⚠️' ? 'cl-warn' : e === '🔍' ? 'cl-ref' : e === '🚧' ? 'cl-todo' : 'cl-note';
    return `<blockquote class="${cls}"><p>${e}`;
  });
}
// ---- navigation infra ----
const byPrefix = {};
files.forEach(f => { const p = (f.match(/^(\d{2}|[A-Z])/) || [])[1]; if (p) byPrefix[p] = f; });
const meta = {};
files.forEach(f => {
  const r = fs.readFileSync(path.join(SRC, f), 'utf8');
  const t = (r.match(/^#\s+(.+)$/m) || [, f])[1];
  meta[f] = { href: f === 'README.md' ? 'README.html' : f.replace(/\.md$/, '.html'), title: t, short: t.replace(/^[^—]*—\s*/, '').trim() };
});
const ordered = ['README.md'].concat(files.filter(f => f !== 'README.md'));
const TREE = [
  { teil: 'Teil 0 · Ankommen', items: ['00', '01', '02'] },
  { teil: 'Teil 1 · Fundament', items: ['03', '04', '05'] },
  { teil: 'Teil 2 · Technik', items: ['06', '07', '08'] },
  { teil: 'Teil 3 · Loslegen', items: ['09', '10', '11'] },
  { teil: 'Teil 4 · Betrieb', items: ['12', '13'] },
  { teil: 'Anhang', items: ['A', 'B', 'C'] },
];
function sidebar(cur) {
  let h = `<a class="sb-home${cur === 'README.md' ? ' current' : ''}" href="README.html">📖 Übersicht</a>`;
  for (const g of TREE) {
    h += `<div class="sb-group"><div class="sb-teil">${g.teil}</div>`;
    for (const p of g.items) {
      const f = byPrefix[p]; if (!f) continue; const m = meta[f];
      h += `<a class="sb-item${f === cur ? ' current' : ''}" href="${m.href}"><span class="sb-num">${p}</span>${m.short}</a>`;
    }
    h += `</div>`;
  }
  return `<aside class="sidebar"><nav class="sb-inner">${h}</nav></aside>`;
}
function topnav(cur, cls) {
  const i = ordered.indexOf(cur);
  const prev = i > 0 ? meta[ordered[i - 1]] : null;
  const next = i >= 0 && i < ordered.length - 1 ? meta[ordered[i + 1]] : null;
  return `<nav class="pagenav${cls ? ' ' + cls : ''}">` +
    (prev ? `<a class="pn pn-prev" href="${prev.href}"><span class="pn-dir">‹ Zurück</span><span class="pn-ttl">${prev.short}</span></a>` : `<span class="pn"></span>`) +
    (next ? `<a class="pn pn-next" href="${next.href}"><span class="pn-dir">Weiter ›</span><span class="pn-ttl">${next.short}</span></a>` : `<span class="pn"></span>`) +
    `</nav>`;
}
function htmlPage(title, bodyInner, cur) {
  return `<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title}</title>
<style>${BASE_CSS}\n${EXTRA_CSS}</style></head>
<body>
<header class="topbar">
  <div class="brand"><button class="navtoggle" aria-label="Kapitel-Navigation">☰</button><span class="dot"></span><b>CloudMan Portal</b><span>· Guide</span></div>
  <div class="topmeta"><a href="README.html">📖 Übersicht</a></div>
</header>
<div class="layout">
${sidebar(cur)}
<main><article>${topnav(cur)}${bodyInner}${topnav(cur, 'pagenav-bottom')}</article></main>
</div>
<script>${LIGHTBOX_JS}</script>
</body></html>`;
}

const summary = [];
for (const file of files) {
  const raw = fs.readFileSync(path.join(SRC, file), 'utf8');
  const prefix = (file.match(/^(\d{2}|[A-Z])/) || [])[1] || '';
  const title = (raw.match(/^#\s+(.+)$/m) || [, file])[1];

  // collect + render mermaid blocks
  const blocks = [];
  let idx = 0;
  raw.replace(MERMAID_RE, (mm, code) => { blocks.push({ key: `${prefix}-${idx++}`, code: code.trim() }); return mm; });
  const rendered = {};
  for (const b of blocks) {
    rendered[b.key] = {
      light: renderSVG(b.code, LIGHT_INIT, b.key + '_l'),
      dark: renderSVG(b.code, DARK_INIT, b.key + '_d'),
      png: renderPNG(b.code, b.key),
      caption: CAPTIONS[prefix] || 'Diagramm',
    };
  }

  // ---------- HTML version ----------
  let bi = 0;
  let mdHtml = raw.replace(MERMAID_RE, () => `@@FIG${blocks[bi++].key}@@`);
  // HTML-Ansicht: Markdown-Fußzeile entfernen — die untere pagenav ersetzt sie
  mdHtml = mdHtml.replace(/\n---\s*\n+[^\n]*📖 Übersicht\]\(README\.md\)[^\n]*\n?/g, '\n');
  let html = marked.parse(mdHtml, { gfm: true });
  for (const b of blocks) {
    const r = rendered[b.key];
    const fig = `<figure class="figcard"><div class="diagram diagram--light">${r.light}</div>` +
      `<div class="diagram diagram--dark">${r.dark}</div><figcaption>${r.caption}</figcaption></figure>`;
    html = html.split(`<p>@@FIG${b.key}@@</p>`).join(fig).split(`@@FIG${b.key}@@`).join(fig);
  }
  html = html.replace(/<table>/g, '<div class="tablewrap"><table>').replace(/<\/table>/g, '</table></div>');
  html = styleCallouts(html);
  html = html.replace(/href="([^":/]+)\.md((?:#[^"]*)?)"/g, 'href="$1.html$2"');
  const IMGDIR = path.join(OUT_HTML, 'img'); fs.mkdirSync(IMGDIR, { recursive: true });
  html = html.replace(/<img([^>]*?)src="([^"]+)"([^>]*)>/g, function (m, pre, src, post) {
    if (/^(https?:|data:|img\/)/.test(src)) return m;
    const abs = path.resolve(SRC, src);
    if (fs.existsSync(abs)) { const bn = path.basename(abs); fs.copyFileSync(abs, path.join(IMGDIR, bn)); return `<img${pre}src="img/${bn}"${post}>`; }
    return m;
  });
  const outName = file === 'README.md' ? 'README.html' : file.replace(/\.md$/, '.html');
  fs.writeFileSync(path.join(OUT_HTML, outName), htmlPage(title, html, file));

  // ---------- BookStack version ----------
  let bj = 0;
  let bs = raw.replace(MERMAID_RE, () => {
    const b = blocks[bj++]; const r = rendered[b.key];
    return `![${r.caption}](images/${r.png})`;
  });
  // copy referenced local images (e.g. screenshots) into images/ and rewrite
  bs = bs.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, function (m, alt, src) {
    if (/^(https?:|images\/)/.test(src)) return m;
    const abs = path.resolve(SRC, src);
    if (fs.existsSync(abs)) { const bn = path.basename(abs); fs.copyFileSync(abs, path.join(OUT_BS_IMG, bn)); return `![${alt}](images/${bn})`; }
    return m;
  });
  // unwrap <details>/<summary>
  bs = bs.replace(/<summary>([\s\S]*?)<\/summary>/g, (m, inner) => '\n**' + inner.replace(/<\/?b>/g, '').trim() + '**\n');
  bs = bs.replace(/^\s*<\/?details>\s*$/gm, '');
  // drop footer nav (the line with the Übersicht marker + its preceding ---)
  bs = bs.replace(/\n---\s*\n+[^\n]*📖 Übersicht[^\n]*\n?/g, '\n');
  // convert local .md links to plain text
  bs = bs.replace(/\[([^\]]+)\]\([^)]*?\.md(?:#[^)]*)?\)/g, '$1');
  // collapse >2 blank lines
  bs = bs.replace(/\n{3,}/g, '\n\n').trimEnd() + '\n';
  fs.writeFileSync(path.join(OUT_BS, file), bs);

  summary.push(`${file.padEnd(32)} html+bookstack  diagrams:${blocks.length}`);
}

// import note for BookStack
fs.writeFileSync(path.join(OUT_BS, '_IMPORT-HINWEIS.md'),
`# BookStack-Import — Hinweise

- Lege ein **Book** „CMP Azubi-Guide" an; importiere jede \`NN-*.md\` als **Page** in Reihenfolge (00 … 12, dann A, B). \`README.md\` = Book-Beschreibung/Startseite.
- **Bilder**: Der Ordner \`images/\` enthält die aus Mermaid gerenderten PNGs. Lade sie in BookStack hoch; die Markdown-Verweise \`![...](images/NN-0.png)\` musst du nach dem Upload auf die BookStack-Bild-URL zeigen lassen (BookStack vergibt eigene Bild-URLs).
- **Querverweise** wie „Kapitel 04" stehen als Klartext (die \`.md\`-Links wurden entfernt) — nach dem Import bei Bedarf als BookStack-Seiten-Links neu setzen.
- Keine \`<details>\`/Mermaid/HTML-Reste: alles wurde in BookStack-nativen Markdown übersetzt.
`);

console.log('OK\n' + summary.join('\n'));
