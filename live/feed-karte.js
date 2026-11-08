/* GL030 Vorschau „Karte im Feed“ – wird über designlab (?glv=karte) in den Live-Feed eingeblendet.
   Nur Vorschau: Daten als Schnappschuss-JSON auf GitHub Pages, Kacheln OSM. */
(function () {
  'use strict';
  var BASE = 'https://gl030.github.io/gl030-sitemap/live/';
  var m = location.pathname.match(/^\/(de|en|es)\/berlin\/(events|eventos)\/([^\/]+)\/(\d\d)-(\d\d)-(\d\d)\/?$/);
  if (!m) return;
  var LANG = m[1], EVSEG = m[2], DSTR = m[4] + '-' + m[5] + '-' + m[6], DAYKEY = m[4] + m[5] + m[6], DAY = '20' + m[6] + '-' + m[5] + '-' + m[4];
  var CATMAP = { es: { party: 'fiesta' } };

  var T = {
    de: { list: 'Liste', map: 'Karte', all: 'Alle', open: 'Jetzt offen', gl: 'Gästeliste', tk: 'Tickets', tb: 'Tisch',
      openTill: 'Offen · bis ', opens: 'Öffnet ', over: 'Vorbei', glTill: 'Gästeliste bis ', glClosed: 'Gästeliste geschlossen',
      ownTk: 'Tickets über GL030', extTk: 'Tickets', table: 'Tisch', toGl: 'Auf die Gästeliste', buy: 'Tickets kaufen', toEv: 'Zum Event', route: 'Route',
      sum: function (o, g, t) { return '<b>' + o + '</b> offen · <b>' + g + '</b> mit Gästeliste · <b>' + t + '</b> mit Tickets'; },
      time: 'Uhrzeit', now: 'Jetzt', near: 'In meiner Nähe', partner: 'Partner', legOpen: 'offen', legSoon: 'öffnet bald', legOff: 'später / vorbei',
      none: 'Keine Clubs für diesen Filter.', nodata: 'Für dieses Datum gibt es in der Vorschau noch keine Kartendaten (Vorschau: 14.11.2026).',
      note: 'Vorschau mit echten GL030-Daten, Stand ' },
    en: { list: 'List', map: 'Map', all: 'All', open: 'Open now', gl: 'Guest list', tk: 'Tickets', tb: 'Table',
      openTill: 'Open · until ', opens: 'Opens ', over: 'Over', glTill: 'Guest list until ', glClosed: 'Guest list closed',
      ownTk: 'Tickets via GL030', extTk: 'Tickets', table: 'Table', toGl: 'Join the guest list', buy: 'Buy tickets', toEv: 'View event', route: 'Route',
      sum: function (o, g, t) { return '<b>' + o + '</b> open · <b>' + g + '</b> with guest list · <b>' + t + '</b> with tickets'; },
      time: 'Time', now: 'Now', near: 'Near me', partner: 'Partner', legOpen: 'open', legSoon: 'opens soon', legOff: 'later / over',
      none: 'No clubs for this filter.', nodata: 'No map data for this date in the preview yet (preview: 14 Nov 2026).',
      note: 'Preview with real GL030 data, as of ' },
    es: { list: 'Lista', map: 'Mapa', all: 'Todos', open: 'Abierto ahora', gl: 'Lista de invitados', tk: 'Entradas', tb: 'Mesa',
      openTill: 'Abierto · hasta las ', opens: 'Abre a las ', over: 'Terminado', glTill: 'Lista hasta las ', glClosed: 'Lista cerrada',
      ownTk: 'Entradas en GL030', extTk: 'Entradas', table: 'Mesa', toGl: 'Apuntarse a la lista', buy: 'Comprar entradas', toEv: 'Ver evento', route: 'Ruta',
      sum: function (o, g, t) { return '<b>' + o + '</b> abiertos · <b>' + g + '</b> con lista · <b>' + t + '</b> con entradas'; },
      time: 'Hora', now: 'Ahora', near: 'Cerca de mí', partner: 'Partner', legOpen: 'abierto', legSoon: 'abre pronto', legOff: 'más tarde / terminado',
      none: 'No hay clubs para este filtro.', nodata: 'Aún no hay datos de mapa para esta fecha en la vista previa (vista previa: 14/11/2026).',
      note: 'Vista previa con datos reales de GL030, a fecha de ' }
  }[LANG];

  var CSS = '' +
    '.glk-toggle{display:flex;justify-content:center;margin:14px auto 4px}' +
    '.glk-seg{display:inline-flex;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);border-radius:999px;padding:4px;gap:2px;backdrop-filter:blur(8px)}' +
    '.glk-seg button{display:inline-flex;align-items:center;gap:7px;border:0;background:none;color:#cfd6e2;font:500 .9rem Roboto,sans-serif;padding:8px 18px;border-radius:999px;cursor:pointer}' +
    '.glk-seg button svg{width:16px;height:16px;fill:currentColor}' +
    '.glk-seg button[aria-pressed=true]{background:linear-gradient(90deg,#00aa82,#00b4dc);color:#06222a;font-weight:700}' +
    'html.glk-on #event-scroll-container,html.glk-on #today-reco{display:none!important}' +
    '#glk{display:none;margin-bottom:24px}html.glk-on #glk{display:block}' +
    '.glk-sum{font-size:.88rem;color:#9aa6b6;margin:2px 0 10px}.glk-sum b{color:#eef1f5;font-weight:500}' +
    '.glk-chips{display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;padding-bottom:2px}.glk-chips::-webkit-scrollbar{display:none}' +
    '.glk-chip{flex:none;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.06);color:#eef1f5;border-radius:999px;padding:6px 12px;font:500 .8rem Roboto,sans-serif;cursor:pointer;white-space:nowrap}' +
    '.glk-chip[aria-pressed=true]{background:#fff;color:#141824;border-color:#fff}.glk-chip .n{opacity:.65;font-weight:400;margin-left:4px}' +
    '.glk-time{margin-top:8px;align-items:center}.glk-time .lab{flex:none;font-size:.72rem;color:#9aa6b6}.glk-time .glk-chip{padding:4px 10px;font-size:.74rem}' +
    '.glk-mapbox{position:relative;margin-top:12px;border-radius:1rem;overflow:hidden;border:1px solid rgba(255,255,255,.12)}' +
    '#glk-map{height:62vh;min-height:380px;max-height:640px;background:#0f1320}' +
    '.glk-dark{filter:invert(1) hue-rotate(180deg) brightness(.82) contrast(.92) saturate(.6)}' +
    '.glk-leg{position:absolute;z-index:500;left:10px;bottom:10px;background:rgba(18,22,34,.86);border:1px solid rgba(255,255,255,.12);border-radius:10px;padding:6px 9px;font:.7rem Roboto,sans-serif;color:#9aa6b6;display:flex;gap:9px;flex-wrap:wrap;max-width:calc(100% - 20px)}' +
    '.glk-leg span{display:inline-flex;align-items:center;gap:4px}.glk-leg i{width:9px;height:9px;border-radius:50%;display:inline-block}' +
    '.glk-near{position:absolute;z-index:500;right:10px;top:10px;border:1px solid rgba(255,255,255,.14);background:rgba(18,22,34,.86);color:#eef1f5;border-radius:999px;padding:7px 12px;font:500 .78rem Roboto,sans-serif;cursor:pointer}' +
    '.glk-pin{position:relative;width:40px;height:40px;border-radius:50%;background:#1b2735 center/cover no-repeat;border:3px solid #6b7585;box-shadow:0 3px 10px rgba(0,0,0,.55)}' +
    '.glk-pin.pr{width:50px;height:50px}.glk-pin.open{border-color:#2ee59d}.glk-pin.soon{border-color:#ffc24b}.glk-pin.off{opacity:.7;filter:grayscale(.6)}' +
    '.glk-pin .ini{position:absolute;inset:0;display:grid;place-items:center;color:#cfd6e2;font:700 12px Roboto,sans-serif}' +
    '.glk-pin .tg{position:absolute;right:-10px;top:-7px;font:700 9px Roboto,sans-serif;border-radius:5px;padding:2px 4px;color:#06222a;background:#00b4dc;box-shadow:0 1px 4px rgba(0,0,0,.5)}' +
    '.glk-pin .tg.t{right:auto;left:-10px;background:#ff6b6b;color:#fff}' +
    '.glk-pin .lb{position:absolute;left:50%;top:100%;transform:translateX(-50%);margin-top:3px;font:700 10px Roboto,sans-serif;color:#fff;white-space:nowrap;text-shadow:0 1px 3px #000,0 0 2px #000;pointer-events:none}' +
    '.glk-list{display:grid;grid-template-columns:1fr;gap:12px;margin-top:14px}@media(min-width:768px){.glk-list{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}}' +
    '.glk-card{min-width:0;background:rgba(20,24,36,.72);border:1px solid rgba(255,255,255,.10);border-radius:1rem;padding:13px;color:#eef1f5;font-family:Roboto,sans-serif}' +
    '.glk-card.pr{border-color:rgba(0,180,220,.55)}.glk-card.hl{outline:2px solid #00b4dc}' +
    '.glk-ch{display:flex;gap:11px;align-items:center}.glk-logo{flex:none;width:46px;height:46px;border-radius:12px;background:#232a3b center/cover no-repeat;position:relative;display:grid;place-items:center;font-weight:700;color:#cfd6e2}' +
    '.glk-logo::after{content:"";position:absolute;right:-3px;top:-3px;width:12px;height:12px;border-radius:50%;border:2px solid #141824;background:#6b7585}' +
    '.s-open .glk-logo::after{background:#2ee59d}.s-soon .glk-logo::after{background:#ffc24b}' +
    '.glk-cn{flex:1;min-width:0}.glk-cn a{color:#eef1f5;text-decoration:none;font-weight:700;font-size:1rem}.glk-st{font-size:.8rem;font-weight:500;color:#9aa6b6}' +
    '.s-open .glk-st{color:#2ee59d}.s-soon .glk-st{color:#ffc24b}' +
    '.glk-pt{flex:none;font-size:.62rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#00b4dc;border:1px solid rgba(0,180,220,.5);border-radius:6px;padding:2px 6px}' +
    '.glk-ev{margin-top:9px;padding-top:9px;border-top:1px solid rgba(255,255,255,.10)}' +
    '.glk-en{color:#eef1f5;font-weight:500;font-size:.9rem;text-decoration:none;display:block;line-height:1.3}.glk-em{font-size:.76rem;color:#9aa6b6;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '.glk-bd{display:flex;flex-wrap:wrap;gap:6px;margin-top:7px}.glk-b{font-size:.7rem;font-weight:500;border-radius:6px;padding:3px 7px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);color:#cfd6e2}' +
    '.glk-b.gl{background:rgba(0,180,220,.16);border-color:rgba(0,180,220,.55);color:#7fe3ff}.glk-b.gl.warn{background:rgba(255,194,75,.14);border-color:rgba(255,194,75,.55);color:#ffd789}.glk-b.gl.x{opacity:.55;text-decoration:line-through}' +
    '.glk-b.own{background:rgba(255,107,107,.16);border-color:rgba(255,107,107,.55);color:#ffb0b0}' +
    '.glk-act{display:flex;gap:7px;margin-top:9px}.glk-btn{flex:1;text-align:center;text-decoration:none!important;font:500 .82rem Roboto,sans-serif;border-radius:.5rem;padding:8px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.06);color:#eef1f5!important}' +
    '.glk-btn.p{background:linear-gradient(90deg,#00aa82,#00b4dc);border:0;color:#06222a!important;font-weight:700}.glk-btn.t{background:linear-gradient(90deg,#16bde0,#4fc3e6);border:0;color:#06222a!important;font-weight:700}.glk-btn.r{flex:0 0 auto;padding:8px 11px}' +
    '.glk-empty,.glk-note{color:#9aa6b6;font-size:.78rem;line-height:1.5}.glk-empty{text-align:center;padding:30px 0}.glk-note{margin-top:12px}' +
    '#glk-map .leaflet-popup-content-wrapper{background:#141824;color:#eef1f5;border-radius:14px;border:1px solid rgba(255,255,255,.12)}#glk-map .leaflet-popup-tip{background:#141824}' +
    '#glk-map .leaflet-popup-content{margin:10px 12px;width:250px!important}#glk-map .leaflet-popup-content .glk-card{min-width:0;background:none;border:0;padding:0}' +
    '#glk-map .leaflet-control-attribution{background:rgba(18,22,34,.7);color:#7b8696}#glk-map .leaflet-control-attribution a{color:#9aa6b6}';

  var ICON_LIST = '<svg viewBox="0 0 24 24"><path d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z"/></svg>';
  var ICON_MAP = '<svg viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/></svg>';

  var DATA = null, map = null, layer = null, meMarker = null;
  var state = { f: 'all', t: null, me: null };

  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function dt(s) { var a = s.split('T'), d = a[0].split('-'), t = a[1].split(':'); return new Date(+d[0], d[1] - 1, +d[2], +t[0], +t[1]); }
  function hm(d) { return pad(d.getHours()) + ':' + pad(d.getMinutes()); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function isToday() { var n = new Date(), s = dt(DAY + 'T12:00'), e = new Date(s.getTime() + 864e5); return n >= s && n < e; }
  var TIMES = isToday() ? ['now', '22:00', '00:00', '02:00', '05:00'] : ['20:00', '21:00', '22:00', '23:00', '00:00', '02:00', '05:00'];
  state.t = isToday() ? 'now' : '21:00';
  function nowT() { if (state.t === 'now') return new Date(); var d = dt(DAY + 'T' + state.t); if (+state.t.slice(0, 2) < 12) d.setDate(d.getDate() + 1); return d; }
  function evSt(e, t) { var b = dt(e.b), en = e.e ? dt(e.e) : new Date(b.getTime() + 6 * 36e5);
    if (t >= b && t < en) return { k: 'open', en: en }; if (t < b) return { k: (b - t) <= 3 * 36e5 ? 'soon' : 'later', b: b }; return { k: 'past' }; }
  function clubSt(c, t) { var best = null, R = { open: 0, soon: 1, later: 2, past: 3 };
    c.ev.forEach(function (e) { var s = evSt(e, t); s.e = e; s.r = R[s.k]; if (!best || s.r < best.r) best = s; }); return best; }
  function glI(e, t) { if (!e.gl) return null; var d = dt(e.gl), left = d - t; if (left <= 0) return { x: 1, txt: T.glClosed }; return { warn: left < 3 * 36e5, txt: T.glTill + hm(d) }; }
  function evUrl(e) {
    var sl = e.s[LANG];
    var a = document.querySelector('a[href$="/' + DSTR + '/' + sl + '"]');
    if (a) return a.href;
    var cat = (CATMAP[LANG] && CATMAP[LANG][e.c]) || e.c;
    return '/' + LANG + '/berlin/' + EVSEG + '/' + cat + '/' + DSTR + '/' + sl;
  }
  function locUrl(c) { return '/' + LANG + '/berlin/' + 'locations' + '/' + c.ls[LANG]; }
  function dist(c) { if (!state.me) return null; var R = 6371, r = function (x) { return x * Math.PI / 180; }, dLa = r(c.lat - state.me[0]), dLo = r(c.lng - state.me[1]);
    var a = Math.sin(dLa / 2) * Math.sin(dLa / 2) + Math.cos(r(state.me[0])) * Math.cos(r(c.lat)) * Math.sin(dLo / 2) * Math.sin(dLo / 2); return 2 * R * Math.asin(Math.sqrt(a)); }
  function enrich() { var t = nowT(); return DATA.clubs.map(function (c) {
    var s = clubSt(c, t), alive = function (e) { return evSt(e, t).k !== 'past'; };
    return { c: c, s: s, gl: c.ev.some(function (e) { var g = glI(e, t); return g && !g.x && alive(e); }),
      tk: c.ev.some(function (e) { return (e.tt || e.tx) && alive(e); }), tb: c.ev.some(function (e) { return e.tb && alive(e); }), d: dist(c) }; }); }
  function pass(x, f) { if (f === 'all') return x.s.k !== 'past'; if (f === 'open') return x.s.k === 'open'; return x[f] && x.s.k !== 'past'; }
  function stTxt(s) { return s.k === 'open' ? T.openTill + hm(s.en) : (s.k === 'past' ? T.over : T.opens + hm(s.b)); }
  function ini(n) { return n.replace(/[^A-Za-zÄÖÜäöü0-9 ]/g, '').split(' ').filter(Boolean).slice(0, 2).map(function (w) { return w[0]; }).join('').toUpperCase(); }

  function card(x, t, pop) {
    var c = x.c, h = '<article class="glk-card s-' + x.s.k + (c.pr ? ' pr' : '') + '"><div class="glk-ch">' +
      '<a class="glk-logo" href="' + locUrl(c) + '" style="' + (c.logo ? 'background-image:url(' + c.logo + ')' : '') + '">' + (c.logo ? '' : esc(ini(c.n))) + '</a>' +
      '<div class="glk-cn"><a href="' + locUrl(c) + '">' + esc(c.n) + '</a><div class="glk-st">' + stTxt(x.s) + '</div></div>';
    if (x.d != null) h += '<span class="glk-pt" style="color:#9aa6b6;border-color:rgba(255,255,255,.2)">' + (x.d < 1 ? Math.round(x.d * 1000) + ' m' : x.d.toFixed(1) + ' km') + '</span>';
    else if (c.pr && !pop) h += '<span class="glk-pt">' + T.partner + '</span>';
    h += '</div>';
    var evs = c.ev.filter(function (e) { return evSt(e, t).k !== 'past'; }); if (!evs.length) evs = c.ev.slice(-1);
    evs.forEach(function (e) {
      var b = dt(e.b), g = glI(e, t), u = evUrl(e);
      h += '<div class="glk-ev"><a class="glk-en" href="' + u + '">' + esc(e.n) + '</a><div class="glk-em">' + hm(b) + (e.e ? '–' + hm(dt(e.e)) : '') + (e.m ? ' · ' + esc(e.m) : '') + '</div><div class="glk-bd">';
      if (g) h += '<span class="glk-b gl' + (g.warn ? ' warn' : '') + (g.x ? ' x' : '') + '">' + g.txt + '</span>';
      if (e.tt) h += '<span class="glk-b own">' + T.ownTk + '</span>'; else if (e.tx) h += '<span class="glk-b">' + T.extTk + '</span>';
      if (e.tb) h += '<span class="glk-b">' + T.table + '</span>';
      h += '</div><div class="glk-act">';
      var glOpen = g && !g.x;
      if (glOpen) h += '<a class="glk-btn p" href="' + u + '">' + T.toGl + '</a>';
      if (e.tt) h += '<a class="glk-btn t" href="' + u + '">' + T.buy + '</a>';
      else if (e.tx) h += '<a class="glk-btn" href="' + esc(e.tx) + '" target="_blank" rel="noopener nofollow">' + T.extTk + ' ↗</a>';
      if (!glOpen && !e.tt && !e.tx) h += '<a class="glk-btn" href="' + u + '">' + T.toEv + '</a>';
      h += '<a class="glk-btn r" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=' + c.lat + ',' + c.lng + '">' + T.route + '</a></div></div>';
    });
    return h + '</article>';
  }

  function render() {
    var root = document.getElementById('glk'); if (!root) return;
    if (!DATA) { root.innerHTML = '<div class="glk-empty">' + T.nodata + '</div>'; return; }
    var t = nowT(), all = enrich(), R = { open: 0, soon: 1, later: 2, past: 3 };
    var cnt = { all: 0, open: 0, gl: 0, tk: 0, tb: 0 };
    all.forEach(function (x) { ['all', 'open', 'gl', 'tk', 'tb'].forEach(function (k) { if (pass(x, k)) cnt[k]++; }); });
    var vis = all.filter(function (x) { return pass(x, state.f); });
    vis.sort(function (a, b) { if (state.me) return a.d - b.d; return (R[a.s.k] - R[b.s.k]) || ((b.gl ? 1 : 0) - (a.gl ? 1 : 0)) || ((b.c.pr ? 1 : 0) - (a.c.pr ? 1 : 0)) || (dt(a.s.e.b) - dt(b.s.e.b)); });
    root.querySelector('.glk-sum').innerHTML = T.sum(cnt.open, cnt.gl, cnt.tk);
    root.querySelector('.glk-f').innerHTML = [['all', T.all], ['open', T.open], ['gl', T.gl], ['tk', T.tk], ['tb', T.tb]].map(function (a) {
      return '<button class="glk-chip" data-f="' + a[0] + '" aria-pressed="' + (state.f === a[0]) + '">' + a[1] + '<span class="n">' + cnt[a[0]] + '</span></button>'; }).join('');
    root.querySelector('.glk-time').innerHTML = '<span class="lab">' + T.time + ':</span>' + TIMES.map(function (k) {
      return '<button class="glk-chip" data-t="' + k + '" aria-pressed="' + (state.t === k) + '">' + (k === 'now' ? T.now : k) + '</button>'; }).join('');
    root.querySelector('.glk-list').innerHTML = vis.length ? vis.map(function (x) { return card(x, t); }).join('') : '<div class="glk-empty">' + T.none + '</div>';
    if (!map) return;
    layer.clearLayers();
    vis.forEach(function (x) {
      var c = x.c, k = x.s.k === 'open' ? 'open' : x.s.k === 'soon' ? 'soon' : 'off', sz = c.pr ? 50 : 40;
      var html = '<div class="glk-pin ' + k + (c.pr ? ' pr' : '') + '" style="' + (c.logo ? 'background-image:url(' + c.logo + ')' : '') + '">' +
        (c.logo ? '' : '<span class="ini">' + esc(ini(c.n)) + '</span>') + (x.gl ? '<span class="tg">GL</span>' : '') +
        (x.tk ? '<span class="tg t">T</span>' : '') + ((c.pr || x.gl) ? '<span class="lb">' + esc(c.n) + '</span>' : '') + '</div>';
      var z = (x.s.k === 'open' ? 3000 : x.s.k === 'soon' ? 2000 : 0) + (x.gl ? 800 : 0) + (c.pr ? 400 : 0);
      L.marker([c.lat, c.lng], { icon: L.divIcon({ html: html, className: '', iconSize: [sz, sz], iconAnchor: [sz / 2, sz / 2], popupAnchor: [0, -sz / 2] }), zIndexOffset: z, title: c.n })
        .bindPopup(function () { return card(x, t, true); }, { maxWidth: 280 }).addTo(layer);
    });
  }

  function initMap() {
    if (map || !window.L) return;
    map = L.map('glk-map', { zoomControl: true, scrollWheelZoom: false }).setView([52.512, 13.41], 12);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, className: 'glk-dark', attribution: '© OpenStreetMap' }).addTo(map);
    layer = L.layerGroup().addTo(map); render();
    map.setView([52.515, 13.405], window.innerWidth < 600 ? 12 : 13);
  }
  function loadLeaflet(cb) {
    if (window.L) return cb();
    var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css'; document.head.appendChild(l);
    var s = document.createElement('script'); s.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js'; s.onload = cb; document.head.appendChild(s);
  }

  function setView(v) {
    var on = v === 'map';
    document.documentElement.classList.toggle('glk-on', on);
    [].forEach.call(document.querySelectorAll('.glk-seg button'), function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-v') === v)); });
    try { history.replaceState(null, '', location.pathname + location.search + (on ? '#karte' : '')); } catch (e) {}
    if (on) loadLeaflet(function () { if (!DATA) return render(); initMap(); setTimeout(function () { map && map.invalidateSize(); }, 60); });
  }

  function mount() {
    var st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
    var dp = document.querySelector('.page-header .date-picker') || document.querySelector('.page-header h1');
    var tg = document.createElement('div'); tg.className = 'glk-toggle';
    tg.innerHTML = '<div class="glk-seg" role="group"><button data-v="list" aria-pressed="true">' + ICON_LIST + T.list + '</button><button data-v="map" aria-pressed="false">' + ICON_MAP + T.map + '</button></div>';
    if (dp && dp.parentNode) dp.parentNode.insertBefore(tg, dp.nextSibling);
    var feed = document.getElementById('event-scroll-container'); if (!feed) return;
    var box = document.createElement('section'); box.id = 'glk';
    box.innerHTML = '<div class="glk-sum"></div><div class="glk-chips glk-f"></div><div class="glk-chips glk-time"></div>' +
      '<div class="glk-mapbox"><div id="glk-map"></div><button class="glk-near">◎ ' + T.near + '</button>' +
      '<div class="glk-leg"><span><i style="background:#2ee59d"></i>' + T.legOpen + '</span><span><i style="background:#ffc24b"></i>' + T.legSoon + '</span><span><i style="background:#6b7585"></i>' + T.legOff + '</span>' +
      '<span><b style="font-size:9px;background:#00b4dc;color:#06222a;border-radius:4px;padding:1px 3px">GL</b>' + T.gl + '</span><span><b style="font-size:9px;background:#ff6b6b;color:#fff;border-radius:4px;padding:1px 3px">T</b>' + T.tk + '</span></div></div>' +
      '<div class="glk-list"></div><p class="glk-note"></p>';
    var ans = document.getElementById('today-answer');
    feed.parentNode.insertBefore(box, feed);
    document.addEventListener('click', function (ev) {
      var b = ev.target.closest && ev.target.closest('button'); if (!b) return;
      if (b.getAttribute('data-v')) { setView(b.getAttribute('data-v')); }
      else if (b.closest('#glk')) {
        if (b.getAttribute('data-f')) { state.f = b.getAttribute('data-f'); render(); }
        else if (b.getAttribute('data-t')) { state.t = b.getAttribute('data-t'); render(); }
        else if (b.className === 'glk-near' && navigator.geolocation) {
          b.textContent = '…'; navigator.geolocation.getCurrentPosition(function (p) {
            state.me = [p.coords.latitude, p.coords.longitude]; b.textContent = '◎ ' + T.near;
            if (meMarker) meMarker.remove(); meMarker = L.circleMarker(state.me, { radius: 7, color: '#fff', weight: 2, fillColor: '#00b4dc', fillOpacity: 1 }).addTo(map);
            map.setView(state.me, 14); render(); }, function () { b.textContent = '◎ –'; });
        }
      }
    });
    fetch(BASE + 'feed-karte-' + DAYKEY + '.json?v=' + Date.now()).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }).then(function (d) {
      DATA = d; if (d) box.querySelector('.glk-note').textContent = T.note + d.stand + '.';
      render(); if (/#karte/.test(location.hash)) setView('map');
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
