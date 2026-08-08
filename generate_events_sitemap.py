#!/usr/bin/env python3
"""
GL030 Event-Sitemap-Generator (Phase 2, ueberarbeitet 31.07.2026 / C5)

Liest die serverseitig gerenderten Tages-Seiten, extrahiert alle Event-Detail-URLs
der naechsten 14 Tage (DE + EN), ermittelt die ES-URLs ueber die hreflang-Links der
DE-Detailseiten (ES-Slugs sind uebersetzt - Muster-Konstruktion wuerde tote URLs
erzeugen; die ES-TAGESLISTEN leiten um, die ES-DETAILSEITEN existieren mit
Self-Canonical), schreibt sitemap-events.xml mit <lastmod> (= Datum des ersten
Auftauchens der URL, persistiert in first-seen.json) und pingt neue URLs per
IndexNow an Bing & Co.

Persistente Zustandsdateien im Repo:
  - hreflang-es-map.json : {de_pfad: es_pfad} - einmal ermittelt, nie neu gecrawlt
  - first-seen.json      : {pfad: JJJJ-MM-TT} - Basis fuer ehrliches lastmod

Laeuft taeglich als GitHub Action. Keine Abhaengigkeiten ausser stdlib.
"""
import os
import re
import sys
import time
import json
import urllib.request
from datetime import date, timedelta

BASE = "https://www.gaesteliste030.de"
LANGS = ["de", "en"]  # ES-Tageslisten leiten um; ES-Details kommen ueber hreflang
DAYS_AHEAD = 14
SITEMAP_FILE = "sitemap-events.xml"
ES_MAP_FILE = "hreflang-es-map.json"
FIRST_SEEN_FILE = "first-seen.json"
MAX_DETAIL_FETCHES = 500  # Schutz gegen Amok-Laeufe; Erstlauf ~400 DE-Seiten
UA = ("Mozilla/5.0 (compatible; GL030-SitemapBot/1.0; "
      "+https://www.gaesteliste030.de)")
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "").strip()
BYPASS_TOKEN = os.environ.get("GL030_BYPASS_TOKEN", "").strip()

DETAIL_RE = re.compile(
    r'href="(/(?:de|en)/berlin/events/[a-z0-9-]+/\d{2}-\d{2}-\d{2}/[a-z0-9-]+)"'
)
HREFLANG_ES_RE = re.compile(
    r'hreflang="es"\s+href="(?:https?://www\.gaesteliste030\.de)?'
    r'(/es/berlin/eventos/[a-z0-9-]+/\d{2}-\d{2}-\d{2}/[a-z0-9-]+)"'
)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if BYPASS_TOKEN:
        req.add_header("X-GL030-Auth", BYPASS_TOKEN)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            if r.status != 200:
                return ""
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  WARN {url}: {e}", file=sys.stderr)
        return ""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Weiterleitungen NICHT folgen - sonst sieht eine 302-URL wie 200 aus."""

    def redirect_request(self, *args, **kwargs):
        return None


_no_redirect_opener = urllib.request.build_opener(_NoRedirect)


def status_of(url: str) -> int:
    """HTTP-Status ohne Redirect-Folgen. 0 = Netzwerkfehler (nicht bewertbar)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if BYPASS_TOKEN:
        req.add_header("X-GL030-Auth", BYPASS_TOKEN)
    try:
        with _no_redirect_opener.open(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        print(f"  WARN Status {url}: {e}", file=sys.stderr)
        return 0


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  WARN {path} unlesbar ({e}) - starte leer.", file=sys.stderr)
        return {}


def save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write("\n")


def collect_event_paths() -> set:
    paths = set()
    today = date.today()
    for offset in range(DAYS_AHEAD + 1):
        d = today + timedelta(days=offset)
        dstr = d.strftime("%d-%m-%y")
        for lang in LANGS:
            url = f"{BASE}/{lang}/berlin/events/party/{dstr}"
            html = fetch(url)
            found = set(DETAIL_RE.findall(html))
            paths |= found
            print(f"  {url}: {len(found)} Events")
            time.sleep(1.5)  # hoeflich bleiben
    return paths


def resolve_es_paths(de_paths: set, es_map: dict) -> set:
    """ES-Pfade ueber hreflang der DE-Detailseiten; Ergebnisse werden gecacht.
    Fehlschlaege werden NICHT gecacht (naechster Lauf versucht es erneut)."""
    missing = sorted(p for p in de_paths if p not in es_map)
    if missing:
        todo = missing[:MAX_DETAIL_FETCHES]
        print(f"hreflang-Aufloesung: {len(todo)} neue DE-Details "
              f"({len(missing) - len(todo)} zurueckgestellt)")
        for p in todo:
            html = fetch(BASE + p)
            m = HREFLANG_ES_RE.search(html)
            if m:
                es_map[p] = m.group(1)
            else:
                print(f"  WARN kein hreflang-es: {p}", file=sys.stderr)
            time.sleep(0.7)
    # Gecachte Zuordnungen validieren: ES-Slugs aendern sich, wenn eine
    # Uebersetzung nachgezogen oder ein Event umbenannt wird. Ohne Pruefung
    # bleibt eine tote URL dauerhaft in der Sitemap (08.08.2026: 5x 302 + 3x 404,
    # GSC-Meldung "Seite mit Weiterleitung"). Fehlerhafte Eintraege werden neu
    # ueber hreflang aufgeloest; klappt das nicht, fliegt der Eintrag raus,
    # statt eine kaputte URL zu listen.
    cached = sorted(p for p in de_paths if p in es_map)
    revalidated = dropped = 0
    for p in cached:
        st = status_of(BASE + es_map[p])
        if st == 200 or st == 0:  # 0 = Netzwerkfehler: Bestand nicht wegwerfen
            continue
        print(f"  ES-Pfad ungueltig (HTTP {st}): {es_map[p]} - loese neu auf")
        html = fetch(BASE + p)
        m = HREFLANG_ES_RE.search(html)
        if m:
            es_map[p] = m.group(1)
            revalidated += 1
        else:
            es_map.pop(p, None)
            dropped += 1
            print(f"  WARN kein hreflang-es bei Neuaufloesung: {p}",
                  file=sys.stderr)
        time.sleep(0.7)
    if revalidated or dropped:
        print(f"Revalidierung: {revalidated} korrigiert, {dropped} entfernt "
              f"({len(cached)} geprueft)")

    # Nur ES-Pfade zurueckgeben, deren DE-Quelle aktuell in der Sitemap ist
    return {es_map[p] for p in de_paths if p in es_map}


def write_sitemap(paths: set, first_seen: dict) -> None:
    today_str = date.today().isoformat()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for p in sorted(paths):
        if p not in first_seen:
            first_seen[p] = today_str
        loc = (BASE + p).replace("&", "&amp;")
        lines.append(f"  <url><loc>{loc}</loc>"
                     f"<lastmod>{first_seen[p]}</lastmod></url>")
    lines.append("</urlset>")
    with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def read_previous_paths() -> set:
    if not os.path.exists(SITEMAP_FILE):
        return set()
    with open(SITEMAP_FILE, encoding="utf-8") as f:
        content = f.read()
    return set(
        m.replace(BASE, "")
        for m in re.findall(r"<loc>([^<]+)</loc>", content)
    )


def ping_indexnow(new_paths: set):
    if not INDEXNOW_KEY:
        print("Kein INDEXNOW_KEY gesetzt - Ping uebersprungen.")
        return
    if not new_paths:
        print("Keine neuen URLs - kein Ping noetig.")
        return
    url_list = [BASE + p for p in sorted(new_paths)][:9500]  # API-Limit 10K
    payload = json.dumps({
        "host": "www.gaesteliste030.de",
        "key": INDEXNOW_KEY,
        "keyLocation": f"{BASE}/{INDEXNOW_KEY}.txt",
        "urlList": url_list,
    }).encode("utf-8")
    req = urllib.request.Request(
        INDEXNOW_ENDPOINT, data=payload,
        headers={"Content-Type": "application/json; charset=utf-8",
                 "User-Agent": UA},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            print(f"IndexNow-Ping: HTTP {r.status} fuer {len(url_list)} URLs")
    except Exception as e:
        print(f"IndexNow-Ping fehlgeschlagen: {e}", file=sys.stderr)


def main():
    print(f"Sammle Events fuer {DAYS_AHEAD + 1} Tage ab {date.today()} ...")
    previous = read_previous_paths()
    current = collect_event_paths()
    if not current:
        print("FEHLER: 0 Events gefunden - Sitemap wird NICHT ueberschrieben "
              "(vermutlich Blockierung oder Strukturaenderung).", file=sys.stderr)
        sys.exit(1)

    es_map = load_json(ES_MAP_FILE)
    de_paths = {p for p in current if p.startswith("/de/")}
    es_paths = resolve_es_paths(de_paths, es_map)
    print(f"ES-Klasse: {len(es_paths)} URLs "
          f"(Map-Bestand: {len(es_map)} Zuordnungen)")
    current |= es_paths

    first_seen = load_json(FIRST_SEEN_FILE)
    new_paths = current - previous
    write_sitemap(current, first_seen)
    # first_seen auf aktuellen Bestand beschneiden (haelt die Datei klein)
    first_seen = {p: d for p, d in first_seen.items() if p in current}
    save_json(FIRST_SEEN_FILE, first_seen)
    # es_map ebenfalls beschneiden: nur DE-Pfade der letzten Sitemap behalten
    es_map = {p: v for p, v in es_map.items() if p in current}
    save_json(ES_MAP_FILE, es_map)

    print(f"Sitemap geschrieben: {len(current)} URLs "
          f"({len(new_paths)} neu gegenueber Vorlauf)")
    ping_indexnow(new_paths)


if __name__ == "__main__":
    main()
