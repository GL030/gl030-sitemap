"""Crawl-Freshness (09.10.2026, Brief "Google-Zeitwerte"): protokolliert je Event-URL der Sitemap den ersten und
letzten Abruf durch Googlebot und Bingbot (Cloudflare GraphQL, Stundenraster, nur HTTP 200) und schreibt einen
Bericht: Zeit vom Sitemap-Eintrag bis zum ersten Abruf, Abruf vor dem Termin, Reaktion auf lastmod-Aenderungen.
Cloudflare bewahrt nur 8 Tage auf -> taeglich laufen (Workflow crawl-freshness.yml).
Hinweis: adaptive Stichprobe von Cloudflare; bei wenigen Abrufen pro URL praktisch vollstaendig."""
import datetime, json, os, re, statistics, sys, urllib.request

ZONE = "917c95aa0daa0628e84e3c9aa0ae81da"
TOKEN = os.environ.get("CF_ANALYTICS_TOKEN", "").strip()
SEEN_FILE = "googlebot-seen.json"
REPORT = "reports/crawl-freshness/latest.md"
BOTS = {"g": "%Googlebot%", "b": "%bingbot%"}
TRACK_START = "2026-10-09"   # ab hier sind Sitemap-Eintrag und erster Abruf sauber vergleichbar


def gql(query, variables):
    req = urllib.request.Request("https://api.cloudflare.com/client/v4/graphql",
                                 data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    if d.get("errors"):
        raise RuntimeError(d["errors"])
    return d["data"]["viewer"]["zones"][0]["r"]


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def main():
    if not TOKEN:
        print("CF_ANALYTICS_TOKEN fehlt", file=sys.stderr); sys.exit(1)
    first_seen = load("first-seen.json", {})
    last_changed = load("last-changed.json", {})
    seen = load(SEEN_FILE, {})
    end = datetime.datetime.now(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0)
    q = """query($zone:String!,$start:Time!,$end:Time!,$ua:String!){ viewer { zones(filter:{zoneTag:$zone}) {
      r: httpRequestsAdaptiveGroups(limit:5000, filter:{datetime_geq:$start, datetime_lt:$end, userAgent_like:$ua,
         edgeResponseStatus:200, clientRequestPath_like:"/%/even%"}) { count dimensions { clientRequestPath datetimeHour } } } } }"""
    for key, ua in BOTS.items():
        for h in range(0, 48, 6):   # 48 h in 6-h-Fenstern (Ueberlappung bei taeglichem Lauf, Limit 5000 je Fenster)
            s = end - datetime.timedelta(hours=h + 6); e = end - datetime.timedelta(hours=h)
            rows = gql(q, {"zone": ZONE, "ua": ua, "start": s.isoformat().replace("+00:00", "Z"),
                           "end": e.isoformat().replace("+00:00", "Z")})
            for r in rows:
                p = r["dimensions"]["clientRequestPath"].split("?")[0].rstrip("/")
                if p not in first_seen:
                    continue
                t = r["dimensions"]["datetimeHour"]
                rec = seen.setdefault(p, {})
                if not rec.get(key + "_first") or t < rec[key + "_first"]:
                    rec[key + "_first"] = t
                if not rec.get(key + "_last") or t > rec[key + "_last"]:
                    rec[key + "_last"] = t
    seen = {p: v for p, v in seen.items() if p in first_seen}
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=0, sort_keys=True); f.write("\n")
    write_report(first_seen, last_changed, seen, end)


def event_date(path):
    m = re.search(r"/(\d\d)-(\d\d)-(\d{2,4})(?:/|$)", path)
    if not m:
        return None
    d, mo, y = m.groups(); y = int(y); y = y + 2000 if y < 100 else y
    try:
        return datetime.date(y, int(mo), int(d))
    except ValueError:
        return None


def hours(a_date, b_iso):
    a = datetime.datetime.fromisoformat(a_date + "T00:00:00+00:00")
    b = datetime.datetime.fromisoformat(b_iso.replace("Z", "+00:00"))
    return (b - a).total_seconds() / 3600


def write_report(first_seen, last_changed, seen, now):
    today = now.date()
    lines = [f"# Crawl-Freshness Events – Stand {now:%d.%m.%Y %H:%M} UTC", "",
             f"Basis: Event-URLs der Sitemap mit Eintrag ab {TRACK_START}. Stundenraster, nur HTTP 200.", ""]
    for key, name in (("g", "Googlebot"), ("b", "Bingbot")):
        coh = {"< 7 Tage": [], "7–20 Tage": [], "≥ 21 Tage": []}
        crawled_before, due = 0, 0
        for p, fs in first_seen.items():
            if fs < TRACK_START:
                continue
            ev = event_date(p)
            lead = (ev - datetime.date.fromisoformat(fs)).days if ev else None
            c = "< 7 Tage" if lead is not None and lead < 7 else "7–20 Tage" if lead is not None and lead < 21 else "≥ 21 Tage"
            first = seen.get(p, {}).get(key + "_first")
            coh[c].append(hours(fs, first) if first else None)
            if ev and ev <= today:
                due += 1
                if first and first[:10] <= ev.isoformat():
                    crawled_before += 1
        lines += [f"## {name}", "", "| Vorlauf | URLs | erster Abruf erfolgt | Median Std. bis Abruf | 75 %-Wert |",
                  "|---|---|---|---|---|"]
        for c, vals in coh.items():
            got = sorted(v for v in vals if v is not None)
            med = f"{statistics.median(got):.0f}" if got else "–"
            p75 = f"{got[int(len(got) * .75)]:.0f}" if got else "–"
            lines.append(f"| {c} | {len(vals)} | {len(got)} ({100 * len(got) / max(len(vals), 1):.0f} %) | {med} | {p75} |")
        lines += ["", f"Events mit Termin bis heute: {due}, davon vor dem Termin abgerufen: {crawled_before}"
                      f" ({100 * crawled_before / max(due, 1):.0f} %).", ""]
    react = []
    for p, ch in last_changed.items():
        last = seen.get(p, {}).get("g_last")
        if last and last[:10] >= ch:
            react.append(hours(ch, last))
    lines += ["## Reaktion auf lastmod-Aenderungen (Googlebot)", "",
              f"Geänderte URLs: {len(last_changed)}, danach erneut abgerufen: {len(react)}"
              + (f", Median {statistics.median(react):.0f} Std." if react else "") + "", ""]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
