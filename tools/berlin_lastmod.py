#!/usr/bin/env python3
"""
GL030 Berlin-Sitemap: ehrliches <lastmod> (24.09.2026, Crawl-Budget F6).

sitemap-berlin.xml (Profile, Kategorien, Saison- und Tag-Seiten) wird weiter von Hand gepflegt -
dieses Skript aendert die URL-LISTE nie. Es ruft jede URL ab, bildet einen Fingerabdruck aus dem,
was sich fuer Suchmaschinen wirklich aendert (Titel, Beschreibung, H1 und die verlinkten Event-
Detailseiten), und setzt <lastmod> auf den Tag der letzten Aenderung dieses Fingerabdrucks.
Zeitstempel ("Stand: heute, 08:15"), Tokens und Zaehler fliessen NICHT ein - sonst waere jede
Seite taeglich "geaendert" und lastmod wertlos.

Zustand: berlin-lastmod.json {pfad: {"h": fingerprint, "d": "JJJJ-MM-TT"}}.
Fehlgeschlagene Abrufe behalten ihren alten Stand. Nur stdlib.
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date

BASE = "https://www.gaesteliste030.de"
SITEMAP = "sitemap-berlin.xml"
STATE = "berlin-lastmod.json"
UA = "Mozilla/5.0 (compatible; GL030-SitemapBot/1.0; +https://www.gaesteliste030.de)"
BYPASS_TOKEN = os.environ.get("GL030_BYPASS_TOKEN", "").strip()

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"')
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
EVENT_LINK_RE = re.compile(
    r'href="(/(?:de|en|es)/berlin/(?:events|eventos)/[a-z0-9-]+/(?:\d{2}-\d{2}-\d{2}/[a-z0-9.-]+'
    r'|[a-z0-9.-]+(?:/\d{2}-\d{2}-\d{4})?))"'
)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


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


def fingerprint(html: str) -> str:
    def first(rx):
        m = rx.search(html)
        return WS_RE.sub(" ", TAG_RE.sub(" ", m.group(1))).strip() if m else ""
    parts = [first(TITLE_RE), first(DESC_RE), first(H1_RE)]
    parts += sorted(set(EVENT_LINK_RE.findall(html)))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


def main():
    with open(SITEMAP, encoding="utf-8") as f:
        xml = f.read()
    urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    if not urls:
        print("FEHLER: keine URLs in sitemap-berlin.xml", file=sys.stderr)
        sys.exit(1)

    state = {}
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            state = json.load(f)

    today = date.today().isoformat()
    changed = failed = 0
    for url in urls:
        path = url.replace(BASE, "") or "/"
        html = fetch(url.replace("&amp;", "&"))
        time.sleep(0.4)
        if not html:
            failed += 1
            continue
        fp = fingerprint(html)
        old = state.get(path)
        if not old or old.get("h") != fp:
            state[path] = {"h": fp, "d": today}
            changed += 1

    if failed > len(urls) // 2:
        print(f"FEHLER: {failed} von {len(urls)} Abrufen gescheitert - nichts geschrieben.", file=sys.stderr)
        sys.exit(1)

    # URL-Liste unveraendert lassen, nur <lastmod> je <url> setzen/ersetzen.
    def repl(m):
        block = m.group(0)
        loc = re.search(r"<loc>([^<]+)</loc>", block).group(1)
        path = loc.replace(BASE, "") or "/"
        entry = state.get(path)
        if not entry:
            return block
        block = re.sub(r"<lastmod>[^<]*</lastmod>", "", block)
        return block.replace("</loc>", f"</loc><lastmod>{entry['d']}</lastmod>", 1)

    new_xml = re.sub(r"<url>.*?</url>", repl, xml, flags=re.S)
    with open(SITEMAP, "w", encoding="utf-8") as f:
        f.write(new_xml)

    known = {u.replace(BASE, "") or "/" for u in urls}
    state = {p: v for p, v in state.items() if p in known}
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write("\n")

    print(f"Berlin-Sitemap: {len(urls)} URLs, {changed} mit neuem lastmod, {failed} Abrufe gescheitert")


if __name__ == "__main__":
    main()
