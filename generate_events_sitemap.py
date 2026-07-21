#!/usr/bin/env python3
"""
GL030 Event-Sitemap-Generator (Phase 2)
Liest die serverseitig gerenderten Tages-Seiten, extrahiert alle Event-Detail-URLs
der naechsten 14 Tage (DE + EN), schreibt sitemap-events.xml und pingt neue URLs
per IndexNow an Bing & Co.

Laeuft taeglich als GitHub Action. Keine Abhaengigkeiten ausser requests.
"""
import os
import re
import sys
import time
import json
import urllib.request
from datetime import date, timedelta

BASE = "https://www.gaesteliste030.de"
LANGS = ["de", "en"]  # ES leitet bei Events um -> auslassen
DAYS_AHEAD = 14
SITEMAP_FILE = "sitemap-events.xml"
UA = ("Mozilla/5.0 (compatible; GL030-SitemapBot/1.0; "
      "+https://www.gaesteliste030.de)")
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "").strip()
BYPASS_TOKEN = os.environ.get("GL030_BYPASS_TOKEN", "").strip()

DETAIL_RE = re.compile(
    r'href="(/(?:de|en)/berlin/events/[a-z0-9-]+/\d{2}-\d{2}-\d{2}/[a-z0-9-]+)"'
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
            # Nur Detail-Seiten, keine Unterseiten (kommen ohnehin nicht im Muster vor)
            paths |= found
            print(f"  {url}: {len(found)} Events")
            time.sleep(1.5)  # hoeflich bleiben
    return paths


def write_sitemap(paths: set) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for p in sorted(paths):
        loc = (BASE + p).replace("&", "&amp;")
        lines.append(f"  <url><loc>{loc}</loc></url>")
    lines.append("</urlset>")
    content = "\n".join(lines) + "\n"
    with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    return content


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
    new_paths = current - previous
    write_sitemap(current)
    print(f"Sitemap geschrieben: {len(current)} URLs "
          f"({len(new_paths)} neu gegenueber Vorlauf)")
    ping_indexnow(new_paths)


if __name__ == "__main__":
    main()
