#!/usr/bin/env python3
"""N19 AI-Query-Mirror (11.09.2026): Welche Seiten holen sich KI-Assistenten auf Nutzeranfrage?

Quelle: Cloudflare GraphQL httpRequestsAdaptiveGroups (adaptive Stichprobe, 7 Tage Retention
fuer diese Aufloesung). Gezaehlt werden nur die "on demand"-Fetcher, die eine konkrete
Nutzerfrage spiegeln (ChatGPT-User, OAI-SearchBot, Perplexity-User, PerplexityBot,
Claude-User, Claude-SearchBot) - die Trainings-Crawler (GPTBot, ClaudeBot) sind Rauschen.
Gefaelschte UAs (Scanner mit ".env"-Pfaden) werden ueber die exakte Herstellerkennung
und Status 200 ausgeschlossen.

Env: CF_ANALYTICS_TOKEN (Zone Analytics Read).  Output: reports/ai-query-mirror/{datum}.md + latest.md
"""
import datetime, json, os, re, sys, urllib.request
from collections import defaultdict

ZONE = "917c95aa0daa0628e84e3c9aa0ae81da"
TOKEN = os.environ.get("CF_ANALYTICS_TOKEN")
DAYS = 7
# On-Demand = Abruf waehrend einer Nutzerfrage (Prompt-Spiegel); Crawler = Index-Aufbau (nur Summe).
ONDEMAND = {
    "ChatGPT-User": "ChatGPT-User/1.0; +https://openai.com/bot",
    "Perplexity-User": "Perplexity-User/1.0",
    "Claude-User": "Claude-User/1.0",
}
CRAWLER = {
    "OAI-SearchBot": "OAI-SearchBot/1.0; +https://openai.com/searchbot",
    "PerplexityBot": "PerplexityBot/1.0",
    "Claude-SearchBot": "Claude-SearchBot/1.0",
}
BOTS = dict(ONDEMAND, **CRAWLER)
CLASS_RULES = [
    ("Startseite", re.compile(r"^/(de|en|es)?/?$")),
    ("Location-Profil", re.compile(r"^/(de|en|es)/berlin/(locations|ubicaciones)/[^/]+/?$")),
    ("Datum", re.compile(r"/(events|eventos)/[^/]+/\d{2}-\d{2}-\d{2}/?$")),
    ("Event-Detail", re.compile(r"/(events|eventos)/[^/]+/\d{2}-\d{2}-\d{2}/[^/]+")),
    ("Kategorie/Tag", re.compile(r"^/(de|en|es)/berlin/(events|eventos)/[^/]+/?$")),
    ("Sonstige", re.compile(r".*")),
]


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req, timeout=60))
    if data.get("errors"):
        raise SystemExit("GraphQL error: " + json.dumps(data["errors"])[:500])
    return data["data"]["viewer"]["zones"][0]["httpRequestsAdaptiveGroups"]


def classify(path):
    for name, rx in CLASS_RULES:
        if rx.search(path):
            return name
    return "Sonstige"


def main():
    if not TOKEN:
        raise SystemExit("CF_ANALYTICS_TOKEN fehlt")
    end = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - datetime.timedelta(days=DAYS)
    q = """query($zone:String!,$start:Time!,$end:Time!,$ua:String!){ viewer { zones(filter:{zoneTag:$zone}) {
      httpRequestsAdaptiveGroups(limit:2000, filter:{datetime_geq:$start, datetime_lt:$end, userAgent_like:$ua, edgeResponseStatus:200},
        orderBy:[count_DESC]) { count dimensions { clientRequestPath } } } } }"""
    per_bot = {}
    for bot, needle in BOTS.items():
        rows = gql(q, {"zone": ZONE, "start": start.isoformat().replace("+00:00", "Z"),
                       "end": end.isoformat().replace("+00:00", "Z"), "ua": "%" + needle + "%"})
        counts = defaultdict(int)
        for r in rows:
            p = r["dimensions"]["clientRequestPath"].split("?")[0]
            if "." in p.rsplit("/", 1)[-1] or p.startswith("/reports/") or p.startswith("/content/"):
                continue  # Assets, Sitemaps, Reports
            counts[p] += r["count"]
        per_bot[bot] = counts

    total = defaultdict(int)
    for bot, counts in per_bot.items():
        if bot not in ONDEMAND:
            continue
        for p, n in counts.items():
            total[p] += n
    by_class = defaultdict(int)
    for p, n in total.items():
        by_class[classify(p)] += n
    by_lang = defaultdict(int)
    for p, n in total.items():
        m = re.match(r"^/(de|en|es)/", p)
        by_lang[m.group(1) if m else "-"] += n

    lines = [f"# AI-Query-Mirror {start:%d.%m.}–{(end - datetime.timedelta(days=1)):%d.%m.%Y}", "",
             "Quelle: Cloudflare GraphQL (adaptive Stichprobe), nur Status 200, nur On-Demand-Fetcher. Zahlen = Abrufe, nicht Nutzer.", "",
             "## Summe je Bot", "", "| Bot | Art | Abrufe | Seiten |", "|---|---|---:|---:|"]
    for bot, counts in sorted(per_bot.items(), key=lambda kv: -sum(kv[1].values())):
        lines.append(f"| {bot} | {'on-demand' if bot in ONDEMAND else 'Crawler'} | {sum(counts.values())} | {len(counts)} |")
    lines += ["", "## Seitenklassen (nur On-Demand)", "", "| Klasse | Abrufe | Anteil |", "|---|---:|---:|"]
    s = sum(by_class.values()) or 1
    for k, n in sorted(by_class.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {n} | {100 * n / s:.0f} % |")
    lines += ["", "## Sprache", "", "| Sprache | Abrufe |", "|---|---:|"]
    for k, n in sorted(by_lang.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {n} |")
    lines += ["", "## Top 60 Pfade (nur On-Demand)", "", "| # | Pfad | Abrufe | ChatGPT-User | Perplexity-User | Claude-User |", "|---:|---|---:|---:|---:|---:|"]
    for i, (p, n) in enumerate(sorted(total.items(), key=lambda kv: -kv[1])[:60], 1):
        lines.append(f"| {i} | `{p}` | {n} | {per_bot['ChatGPT-User'].get(p, 0)} | {per_bot['Perplexity-User'].get(p, 0)} | {per_bot['Claude-User'].get(p, 0)} |")
    lines += ["", "Lesehilfe: On-Demand-Abrufe spiegeln konkrete Nutzerfragen; Crawler-Summen zeigen nur, wie tief die Indizes gehen. "
              "Datumsseiten = heute/Wochenende-Fragen, Profile = Club-Fragen, EN = Touristen."]
    out = "\n".join(lines) + "\n"
    os.makedirs("reports/ai-query-mirror", exist_ok=True)
    stamp = (end - datetime.timedelta(days=1)).strftime("%Y%m%d")
    for name in (f"reports/ai-query-mirror/{stamp}.md", "reports/ai-query-mirror/latest.md"):
        with open(name, "w", encoding="utf-8") as f:
            f.write(out)
    print(out[:3000])


if __name__ == "__main__":
    main()
