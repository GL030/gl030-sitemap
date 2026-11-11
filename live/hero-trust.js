/* GL030 Vorschau „Vertrauenszeile im Kopf“ – drei Varianten, Umschalter unten links (nur Vorschau). */
(function () {
  'use strict';
  if (document.getElementById('glt-style')) return;
  var h1 = document.querySelector('.page-header h1');
  if (!h1) return;
  var LANG = (location.pathname.match(/^\/(en|es)(\/|$)/) || [, 'de'])[1];
  var YEARS = new Date().getFullYear() - 2010;
  var T = {
    de: { since: 'Seit 2010', n: 'über 1,8 Mio.', gl: 'Gästelisten-Anmeldungen', years: YEARS + ' Jahre', yearsSub: 'Berliner Nachtleben',
          nSub: 'Gästelisten-Anmeldungen', lang: 'DE · EN · ES', langSub: 'dreisprachig', badge: 'Gästelisten seit' },
    en: { since: 'Since 2010', n: '1.8M+', gl: 'guest list sign-ups', years: YEARS + ' years', yearsSub: 'of Berlin nightlife',
          nSub: 'guest list sign-ups', lang: 'DE · EN · ES', langSub: 'in three languages', badge: 'Guest lists since' },
    es: { since: 'Desde 2010', n: 'más de 1,8 M', gl: 'inscripciones en listas', years: YEARS + ' años', yearsSub: 'de noche berlinesa',
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
    /* Umschalter (nur Vorschau) */
    '#glt-sw{position:fixed;left:12px;bottom:12px;z-index:99999;display:flex;gap:4px;padding:4px;border-radius:999px;background:rgba(18,22,34,.92);border:1px solid rgba(255,255,255,.18);font:500 12px Roboto,sans-serif;box-shadow:0 4px 14px rgba(0,0,0,.5)}' +
    '#glt-sw button{border:0;background:none;color:#cfd6e2;padding:6px 11px;border-radius:999px;cursor:pointer;font:inherit}' +
    '#glt-sw button[aria-pressed=true]{background:#fff;color:#141824;font-weight:700}#glt-sw span{color:#9aa6b6;padding:6px 4px 6px 8px}';

  var ICON = '<svg class="ic" viewBox="0 0 24 24"><path d="M12 2 3 6v6c0 5 3.8 9.7 9 10 5.2-.3 9-5 9-10V6l-9-4zm-1.2 14.6-4-4 1.4-1.4 2.6 2.6 5.6-5.6 1.4 1.4-7 7z"/></svg>';
  var V = {
    A: { where: 'after', html: '<div class="glt glt-a">' + ICON + '<span><b>' + T.since + '</b></span><i class="dot"></i><span><b>' + T.n + '</b> ' + T.gl + '</span></div>' },
    B: { where: 'both', before: '<div class="glt" style="margin-bottom:0"><span class="glt-b">' + T.badge + '<span class="yr">2010</span></span></div>',
         html: '<div class="glt glt-b-sub"><b>' + T.n + '</b> ' + T.gl + '</div>' },
    C: { where: 'after', html: '<div class="glt glt-c"><div><b><span>' + T.years + '</span></b><small>' + T.yearsSub + '</small></div>' +
         '<div><b>' + T.n + '</b><small>' + T.nSub + '</small></div><div><b>' + T.lang + '</b><small>' + T.langSub + '</small></div></div>' },
    0: { where: 'none' }
  };

  var st = document.createElement('style'); st.id = 'glt-style'; st.textContent = CSS; document.head.appendChild(st);
  var cur = null;
  function clear() { [].forEach.call(document.querySelectorAll('.glt'), function (e) { e.remove(); }); }
  function apply(k) {
    clear(); cur = k; var v = V[k];
    if (v.where === 'after' || v.where === 'both') h1.insertAdjacentHTML('afterend', v.html);
    if (v.where === 'both') h1.insertAdjacentHTML('beforebegin', v.before);
    [].forEach.call(document.querySelectorAll('#glt-sw button'), function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-k') === k)); });
    try { sessionStorage.setItem('glt', k); } catch (e) {}
  }
  var sw = document.createElement('div'); sw.id = 'glt-sw';
  sw.innerHTML = '<span>Kopf:</span><button data-k="A">A</button><button data-k="B">B</button><button data-k="C">C</button><button data-k="0">ohne</button>';
  sw.addEventListener('click', function (e) { var b = e.target.closest('button'); if (b) apply(b.getAttribute('data-k')); });
  document.body.appendChild(sw);
  var start = 'B'; try { start = sessionStorage.getItem('glt') || 'B'; } catch (e) {}
  apply(start);
})();
