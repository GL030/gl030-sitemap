#!/usr/bin/env python3
"""
GL030 EN/ES-Qualitaets-Check (02.10.2026). Prueft die sichtbarsten fremdsprachigen Event- und Clubseiten:
  R1 Sprache:      deutsche Signalwoerter in der Beschreibung (unuebersetzt)
  R2 Datum:        Datum im Text (dd.mm.yy) ohne Bezug zum Seitendatum (nur Eventseiten)
  R3 Eigennamen:   Clubname der EN/ES-Seite weicht von der DE-Seite ab
  R4 Dubletten:    identische Beschreibung auf mehreren Seiten
  R5 Pflichtdaten: Event-Objekt (schema.org) ohne startDate/location
Ergebnis: reports/translation-check.md + translation-check.json (Verlauf der Fehlerquoten).
URL-Quelle: sitemap-events.xml (EN/ES-Eventseiten der naechsten 14 Tage) + sitemap-berlin.xml (EN/ES-Profile).
"""
import json, os, re, sys, time, html, datetime, urllib.request, collections

BASE = "https://www.gaesteliste030.de"
UA = "Mozilla/5.0 (compatible; GL030-QualityBot/1.0; +https://www.gaesteliste030.de)"
TOKEN = os.environ.get("GL030_BYPASS_TOKEN", "").strip()
DE = re.compile(r"\b(und|der|die|das|mit|nicht|für|auf|wir|ihr|euch|uhr|jeden|jede|alle|freitag|samstag|sonntag|eintritt|gäste|wird|werden|sind|ist|ein|eine|einen|dem|den|zum|zur|bei|nach|oder|auch|noch|nur|sich|wie)\b", re.I)
EN = re.compile(r"\b(and|the|with|not|for|you|your|every|all|friday|saturday|sunday|entry|guests|will|are|is|from|at|to|of|on|in|our|night|party|free|until)\b", re.I)
ES = re.compile(r"\b(y|el|la|los|las|con|no|para|por|todos|cada|viernes|sábado|domingo|entrada|invitados|será|son|es|un|una|del|al|en|de|que|noche|fiesta|gratis|hasta)\b", re.I)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if TOKEN: req.add_header("X-GL030-Auth", TOKEN)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, ""

def text(h):
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()

def description(h):
    m = re.search(r'itemprop="description"[^>]*>(.*?)</div>\s*</div>', h, re.S)
    return text(m.group(1)) if m else ""

def h1(h):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    return text(m.group(1)) if m else ""

def main():
    urls = []
    for sm in ("sitemap-events.xml", "sitemap-berlin.xml"):
        st, x = fetch(f"{BASE}/content/sitemap/{sm}")
        urls += re.findall(r"<loc>([^<]+)</loc>", x)
    today = datetime.date.today()
    cand = []
    for u in urls:
        p = u.replace(BASE, "")
        if not (p.startswith("/en/") or p.startswith("/es/")): continue
        m = re.search(r"/(\d{2})-(\d{2})-(\d{2})/", p)
        if m:
            d = datetime.date(2000 + int(m.group(3)), int(m.group(2)), int(m.group(1)))
            if not (today <= d <= today + datetime.timedelta(days=14)): continue
            cand.append(("event", p, d))
        elif "/locations/" in p or "/locales/" in p:
            cand.append(("club", p, None))
    cand = cand[:int(os.environ.get("GL_MAX", "150"))]
    rows, descs = [], collections.defaultdict(list)
    for kind, p, d in cand:
        lang = p[1:3]
        st, h = fetch(BASE + p)
        time.sleep(0.5)
        if st != 200:
            rows.append({"path": p, "status": st, "issues": ["HTTP"]}); continue
        desc = description(h) if kind == "event" else text(re.search(r'id="description".*?</section>', h, re.S).group(0)) if re.search(r'id="description"', h) else ""
        issues = []
        if desc and len(desc) > 80:
            de = len(DE.findall(desc)); tgt = len((ES if lang == "es" else EN).findall(desc))
            if de >= 4 and de > tgt * 2: issues.append("R1 deutsch")
            if kind == "event" and d:
                for dm in re.findall(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b", desc):
                    try:
                        y = int(dm[2]); y = y + 2000 if y < 100 else y
                        dd = datetime.date(y, int(dm[1]), int(dm[0]))
                        if abs((dd - d).days) > 1: issues.append("R2 datum %s" % ".".join(dm)); break
                    except ValueError: pass
            descs[desc[:200]].append(p)
        if kind == "club":
            de_path = p.replace("/en/berlin/locations/", "/de/berlin/locations/").replace("/es/berlin/locales/", "/de/berlin/locations/")
            st2, h2 = fetch(BASE + de_path); time.sleep(0.3)
            if st2 == 200 and h1(h2) and h1(h) and h1(h2).lower() != h1(h).lower():
                issues.append("R3 name '%s' vs '%s'" % (h1(h), h1(h2)))
        if kind == "event" and 'itemtype="https://schema.org/DanceEvent"' in h and ('itemprop="startDate"' not in h or 'itemprop="location"' not in h):
            issues.append("R5 schema")
        if "X-GL-Gate" in h or "coming soon. Date, club" in h or "en preparación" in h: issues.append("GATE aktiv")
        rows.append({"path": p, "status": st, "issues": issues})
    for k, ps in descs.items():
        if len(ps) > 1:
            for p in ps:
                for r in rows:
                    if r["path"] == p: r["issues"].append("R4 dublette x%d" % len(ps))
    n = len(rows); counts = collections.Counter(i.split(" ")[0] for r in rows for i in r["issues"])
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# EN/ES-Qualitaets-Check – {stamp}", "", f"Gepruefte Seiten: {n}", ""]
    lines.append("| Regel | Treffer | Quote |"); lines.append("|---|---|---|")
    for rule in ("R1", "R2", "R3", "R4", "R5", "GATE", "HTTP"):
        lines.append(f"| {rule} | {counts.get(rule,0)} | {100*counts.get(rule,0)/max(n,1):.1f} % |")
    lines += ["", "## Seiten mit Befund", ""]
    for r in rows:
        if r["issues"]: lines.append(f"- {BASE}{r['path']} – " + "; ".join(r["issues"]))
    os.makedirs("reports", exist_ok=True)
    open("reports/translation-check.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    hist = []
    if os.path.exists("reports/translation-check.json"): hist = json.load(open("reports/translation-check.json"))
    hist.append({"date": stamp, "pages": n, "counts": counts})
    json.dump(hist[-120:], open("reports/translation-check.json", "w"), indent=0)
    print("\n".join(lines[:12]))

if __name__ == "__main__":
    main()
