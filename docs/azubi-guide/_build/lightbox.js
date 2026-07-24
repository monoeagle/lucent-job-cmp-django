document.addEventListener('DOMContentLoaded', function () {
  var figures = Array.prototype.slice.call(document.querySelectorAll('figure.figcard'));
  var looseImgs = Array.prototype.slice.call(document.querySelectorAll('article img')).filter(function (im) {
    return !im.closest('figure.figcard');
  });
  var items = figures.map(function (f) { return { type: 'fig', el: f }; })
    .concat(looseImgs.map(function (im) { return { type: 'img', el: im }; }));
  if (!items.length) return;

  var lb = document.createElement('div');
  lb.id = 'lightbox';
  lb.innerHTML =
    '<span class="lb-count"></span>' +
    '<button class="lb-btn lb-close" aria-label="Schließen (Esc)">✕</button>' +
    '<button class="lb-btn lb-nav lb-prev" aria-label="Zurück">‹</button>' +
    '<div class="lb-stage"><div class="lb-media"></div><div class="lb-cap"></div></div>' +
    '<button class="lb-btn lb-nav lb-next" aria-label="Vor">›</button>';
  document.body.appendChild(lb);
  var media = lb.querySelector('.lb-media');
  var cap = lb.querySelector('.lb-cap');
  var count = lb.querySelector('.lb-count');
  var current = 0;

  function visibleSvg(fig) {
    var diags = Array.prototype.slice.call(fig.querySelectorAll('.diagram'));
    var vis = diags.filter(function (d) { return getComputedStyle(d).display !== 'none'; })[0] || diags[0];
    return vis ? vis.querySelector('svg') : null;
  }
  function nodeFor(item) { return item.type === 'img' ? item.el : visibleSvg(item.el); }
  function captionHTML(item) {
    if (item.type === 'img') { return item.el.getAttribute('alt') || ''; }
    var fc = item.el.querySelector('figcaption');
    if (!fc) return '';
    var c = fc.cloneNode(true);
    var hint = c.querySelector('.zoomhint'); if (hint) hint.remove();
    var br = c.querySelector('br'); if (br) br.remove();
    return c.innerHTML.trim();
  }
  function sizeNode(clone) {
    var vb = (clone.getAttribute('viewBox') || '').split(/[ ,]+/).map(Number);
    clone.removeAttribute('width'); clone.removeAttribute('height');
    clone.style.maxWidth = 'none'; clone.style.background = 'transparent';
    if (vb.length === 4 && vb[2] && vb[3]) {
      var s = Math.min(window.innerWidth * 0.84 / vb[2], window.innerHeight * 0.72 / vb[3]);
      clone.style.width = (vb[2] * s) + 'px';
      clone.style.height = (vb[3] * s) + 'px';
    } else {
      clone.style.width = 'auto'; clone.style.maxWidth = '84vw'; clone.style.maxHeight = '72vh';
    }
  }
  function render() {
    var node = nodeFor(items[current]);
    if (!node) return;
    var clone = node.cloneNode(true);
    sizeNode(clone);
    media.innerHTML = ''; media.appendChild(clone);
    cap.innerHTML = captionHTML(items[current]);
    count.textContent = (current + 1) + ' / ' + items.length;
  }
  function open(i) { current = i; lb.classList.add('open'); document.body.style.overflow = 'hidden'; render(); }
  function close() { lb.classList.remove('open'); media.innerHTML = ''; document.body.style.overflow = ''; }
  function go(d) { current = (current + d + items.length) % items.length; render(); }

  items.forEach(function (item, i) {
    var clickable = item.type === 'img' ? [item.el] :
      Array.prototype.slice.call(item.el.querySelectorAll('.diagram svg'));
    clickable.forEach(function (n) {
      n.classList.add('zoomable');
      n.addEventListener('click', function (e) { e.stopPropagation(); open(i); });
    });
  });
  document.querySelectorAll('figure.figcard figcaption').forEach(function (fc) {
    var s = document.createElement('span'); s.className = 'zoomhint';
    s.textContent = '🔍  Zum Vergrößern klicken';
    fc.appendChild(document.createElement('br')); fc.appendChild(s);
  });
  lb.querySelector('.lb-prev').addEventListener('click', function (e) { e.stopPropagation(); go(-1); });
  lb.querySelector('.lb-next').addEventListener('click', function (e) { e.stopPropagation(); go(1); });
  lb.addEventListener('click', function (e) {
    if (e.target === lb || e.target.classList.contains('lb-close')
      || e.target === media || e.target.classList.contains('lb-stage')) close();
  });
  document.addEventListener('keydown', function (e) {
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') go(-1);
    else if (e.key === 'ArrowRight') go(1);
  });
});

document.addEventListener('DOMContentLoaded', function () {
  var t = document.querySelector('.navtoggle');
  if (t) t.addEventListener('click', function () { document.body.classList.toggle('nav-open'); });
});
