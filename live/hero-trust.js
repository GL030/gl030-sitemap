/* GL030 Vorschau „Vertrauenszeile im Kopf“ – drei Varianten, Umschalter unten links (nur Vorschau). */
(function () {
  'use strict';
  if (document.getElementById('glt-style')) return;
  var h1 = document.querySelector('.page-header h1');
  if (!h1) return;
  var LANG = (location.pathname.match(/^\/(en|es)(\/|$)/) || [, 'de'])[1];
  var YEARS = new Date().getFullYear() - 2010;
  var T = {
    de: { since: 'Seit 2010', n: 'über 2,2 Mio.', gl: 'Gästelisten-Anmeldungen', years: YEARS + ' Jahre', yearsSub: 'Berliner Nachtleben',
          nSub: 'Gästelisten-Anmeldungen', lang: 'DE · EN · ES', langSub: 'dreisprachig', badge: 'Gästelisten seit' },
    en: { since: 'Since 2010', n: '2.2M+', gl: 'guest list sign-ups', years: YEARS + ' years', yearsSub: 'of Berlin nightlife',
          nSub: 'guest list sign-ups', lang: 'DE · EN · ES', langSub: 'in three languages', badge: 'Guest lists since' },
    es: { since: 'Desde 2010', n: 'más de 2,2 M', gl: 'inscripciones en listas', years: YEARS + ' años', yearsSub: 'de noche berlinesa',
          nSub: 'inscripciones en listas', lang: 'DE · EN · ES', langSub: 'en tres idiomas', badge: 'Listas de invitados desde' }
  }[LANG];

  var CSS = '' +
    '.glt{font-family:Roboto,sans-serif;color:rgba(255,255,255,.82);text-align:center}' +
    /* A: ruhige Zeile unter dem Titel */
    '.glt-a{display:flex;justify-content:center;align-items:center;flex-wrap:wrap;gap:6px 10px;margin:-4px auto 14px;font-size:.92rem;font-weight:400;letter-spacing:.01em}' +
    '.glt-a b{font-weight:700;color:#fff}.glt-a .dot{width:4px;height:4px;border-radius:50%;background:#00b4dc;display:inline-block}' +
    '.glt-a .ic{width:15px;height:15px;fill:#00b4dc;margin-right:4px;vertical-align:-2px}' +
    /* B: Glas-Plakette über dem Titel */
    '.glt-b{display:inline-flex;align-items:center;gap:8px;margin:0 auto 10px;padding:6px 6px 6px 14px;border-radius:999px;font-size:.8rem;font-weight:500;letter-spacing:.02em;' +
      'background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}' +
    '.glt-b .yr{background:linear-gradient(90deg,#00aa82,#00b4dc);color:#06222a;font-weight:700;border-radius:999px;padding:2px 9px;font-size:.75rem}' +
    '.glt-b-sub{font-size:.85rem;margin:-4px 0 14px;color:rgba(255,255,255,.7)}.glt-b-sub b{color:#fff;font-weight:700}' +
    /* C: drei Kennzahlen */
    '.glt-c{display:flex;justify-content:center;gap:0;margin:2px auto 16px;max-width:520px}' +
    '.glt-c > div{flex:1;padding:0 10px;border-left:1px solid rgba(255,255,255,.16)}.glt-c > div:first-child{border-left:0}' +
    '.glt-c b{display:block;font-size:1.25rem;font-weight:700;color:#fff;line-height:1.15;white-space:nowrap}' +
    '.glt-c b span{background:linear-gradient(90deg,#00aa82,#00b4dc);-webkit-background-clip:text;background-clip:text;color:transparent}' +
    '.glt-c small{display:block;font-size:.72rem;color:rgba(255,255,255,.65);margin-top:2px;line-height:1.25}' +
    '@media(max-width:400px){.glt-a{font-size:.84rem}.glt-c b{font-size:1.08rem}.glt-c small{font-size:.66rem}.glt-c > div{padding:0 6px}}' +
    /* Ecke links oben: Etikett über türkiser 2010 */
    '.glt-k{position:absolute;left:var(--glt-k,16px);top:var(--glt-k,16px);z-index:5;display:flex;flex-direction:column;align-items:center;gap:4px;padding:7px 9px 8px;border-radius:14px;'+
      'background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.16);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);text-align:center}' +
    '.glt-k .lb{font-size:.62rem;font-weight:500;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.75);line-height:1.15;white-space:nowrap}' +
    '.glt-k.long .lb{max-width:64px;white-space:normal}' +
    '.glt-k .yr{background:linear-gradient(90deg,#00aa82,#00b4dc);color:#06222a;font-weight:700;border-radius:999px;padding:2px 10px;font-size:.8rem;letter-spacing:.02em}' +
    '@media(min-width:992px){.glt-k{--glt-k:24px;padding:9px 12px 10px}.glt-k .lb{font-size:.68rem}.glt-k .yr{font-size:.9rem}}' +
    /* Umschalter (nur Vorschau) */
    '#glt-sw{position:fixed;left:12px;bottom:12px;z-index:99999;display:flex;gap:4px;padding:4px;border-radius:999px;background:rgba(18,22,34,.92);border:1px solid rgba(255,255,255,.18);font:500 12px Roboto,sans-serif;box-shadow:0 4px 14px rgba(0,0,0,.5)}' +
    '#glt-sw button{border:0;background:none;color:#cfd6e2;padding:6px 11px;border-radius:999px;cursor:pointer;font:inherit}' +
    '#glt-sw button[aria-pressed=true]{background:#fff;color:#141824;font-weight:700}#glt-sw span{color:#9aa6b6;padding:6px 4px 6px 8px}';

  var ICON = '<svg class="ic" viewBox="0 0 24 24"><path d="M12 2 3 6v6c0 5 3.8 9.7 9 10 5.2-.3 9-5 9-10V6l-9-4zm-1.2 14.6-4-4 1.4-1.4 2.6 2.6 5.6-5.6 1.4 1.4-7 7z"/></svg>';
  var LBL = { de: { gl: 'Gästelisten seit', seit: 'seit', est: 'Est.' }, en: { gl: 'Guest lists since', seit: 'since', est: 'Est.' }, es: { gl: 'Listas desde', seit: 'desde', est: 'Est.' } }[LANG];
  function corner(lbl, cls) { return '<div class="glt glt-k ' + (cls || '') + '"><span class="lb">' + lbl + '</span><span class="yr">2010</span></div>'; }
  var V = {
    1: { where: 'corner', html: corner(LBL.gl, 'long') },
    2: { where: 'corner', html: corner(LBL.seit) },
    3: { where: 'corner', html: corner(LBL.est) },
    F: { where: 'final', html: '<div class="glt glt-b-sub"><b>' + T.n + '</b> ' + T.gl + '</div>', corner: corner(LBL.est) },
    A: { where: 'after', html: '<div class="glt glt-a">' + ICON + '<span><b>' + T.since + '</b></span><i class="dot"></i><span><b>' + T.n + '</b> ' + T.gl + '</span></div>' },
    B: { where: 'both', before: '<div class="glt" style="margin-bottom:0"><span class="glt-b">' + T.badge + '<span class="yr">2010</span></span></div>',
         html: '<div class="glt glt-b-sub"><b>' + T.n + '</b> ' + T.gl + '</div>' },
    0: { where: 'none' }
  };
  function placeCorner() {
    var k = document.querySelector('.glt-k'), logo = document.querySelector('.page-header .gl-hero-home'); if (!k || !logo) return;
    var box = logo.parentNode; if (getComputedStyle(box).position === 'static') box.style.position = 'relative';
    var lr = logo.getBoundingClientRect(), br = box.getBoundingClientRect(), img = logo.querySelector('img,svg') || logo, ir = img.getBoundingClientRect();
    var mid = (ir.height ? ir.top + ir.height / 2 : lr.top + lr.height / 2) - br.top;
    k.style.top = Math.round(mid - k.offsetHeight / 2) + 'px';
  }
  window.addEventListener('resize', placeCorner);
  var st = document.createElement('style'); st.id = 'glt-style'; st.textContent = CSS; document.head.appendChild(st);
  var cur = null;
  function clear() { [].forEach.call(document.querySelectorAll('.glt'), function (e) { e.remove(); }); }
  function apply(k) {
    clear(); cur = k; var v = V[k];
    if (v.where === 'after' || v.where === 'both') h1.insertAdjacentHTML('afterend', v.html);
    if (v.where === 'both') h1.insertAdjacentHTML('beforebegin', v.before);
    if (v.where === 'final') { var ph = document.querySelector('.page-header'); if (getComputedStyle(ph).position === 'static') ph.style.position = 'relative'; ph.insertAdjacentHTML('afterbegin', v.corner); h1.insertAdjacentHTML('afterend', v.html); }
    if (v.where === 'corner') { var lg = document.querySelector('.page-header .gl-hero-home'); (lg ? lg.parentNode : h1.parentNode).insertAdjacentHTML('afterbegin', v.html); placeCorner(); setTimeout(placeCorner, 400); }
    [].forEach.call(document.querySelectorAll('#glt-sw button'), function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-k') === k)); });
    try { sessionStorage.setItem('glt2', k); } catch (e) {}
  }
  var sw = document.createElement('div'); sw.id = 'glt-sw';
  sw.innerHTML = '<span>Kopf:</span><button data-k="F">neu</button><button data-k="0">ohne</button>';
  sw.addEventListener('click', function (e) { var b = e.target.closest('button'); if (b) apply(b.getAttribute('data-k')); });
  document.body.appendChild(sw);
  var start = 'F';
  apply(start);
})();
