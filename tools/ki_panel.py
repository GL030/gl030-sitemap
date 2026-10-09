"""KI-Panel (09.10.2026, Brief "kein einheitliches AI-Ranking"): misst je Absichtsgruppe, ob ChatGPT (OpenAI-API mit
Websuche, Standort Berlin) Gaesteliste030 nennt und gaesteliste030.de zitiert, und welche Drittquellen es zitiert.
Woechentlich REPEATS Durchlaeufe je Prompt (Antworten schwanken stark - Einzelabfragen sind wertlos).
Erfolgskriterium (Brief): Verbesserung erst gelten lassen, wenn sie 3 Wochen in >= 2 Gruppen haelt.
Perplexity/Gemini folgen spaeter (eigene Funktionen ergaenzen)."""
import collections, datetime, json, os, re, sys, time, urllib.parse, urllib.request

KEY = os.environ.get("OPENAI_API_KEY", "").strip()
REPEATS = int(os.environ.get("REPEATS", "5"))
MODELS = [m for m in os.environ.get("MODELS", "gpt-4.1-mini,gpt-4o-mini").split(",") if m]
TOOLS = ["web_search", "web_search_preview"]
BRAND_RE = re.compile(r"g(ä|ae)steliste\s?030|gl030", re.I)
OUT_DIR = "reports/ki-panel"


def call(model, tool, prompt):
    body = {"model": model, "input": prompt,
            "tools": [{"type": tool, "user_location": {"type": "approximate", "country": "DE", "city": "Berlin"}}]}
    req = urllib.request.Request("https://api.openai.com/v1/responses", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def parse(resp):
    text, urls = [], []
    for item in resp.get("output", []):
        for c in item.get("content", []) or []:
            if c.get("type") == "output_text":
                text.append(c.get("text", ""))
                for a in c.get("annotations", []) or []:
                    if a.get("type") == "url_citation" and a.get("url"):
                        urls.append(a["url"])
    t = "\n".join(text)
    urls += re.findall(r"https?://[^\s)\]>\"']+", t)
    domains = sorted({urllib.parse.urlparse(u).netloc.lower().removeprefix("www.") for u in urls if "://" in u})
    return t, domains


def main():
    if not KEY:
        print("OPENAI_API_KEY fehlt", file=sys.stderr); sys.exit(1)
    prompts = json.load(open("tools/ki_panel_prompts.json", encoding="utf-8"))
    # Modell + Werkzeug einmal ermitteln (erstes, das antwortet)
    combo = None
    for m in MODELS:
        for t in TOOLS:
            try:
                call(m, t, "Berlin"); combo = (m, t); break
            except urllib.error.HTTPError as e:
                print(f"  {m}/{t}: HTTP {e.code} {e.read()[:200]!r}", file=sys.stderr)
        if combo: break
    if not combo:
        print("Kein Modell/Werkzeug nutzbar - Schluessel/Guthaben pruefen", file=sys.stderr); sys.exit(2)
    print("Nutze", combo)
    rows = []
    for group, langs in prompts.items():
        for lang, plist in langs.items():
            for p in plist:
                for i in range(REPEATS):
                    try:
                        t, doms = parse(call(combo[0], combo[1], p))
                        rows.append({"group": group, "lang": lang, "prompt": p, "run": i + 1,
                                     "mention": bool(BRAND_RE.search(t)), "cited": "gaesteliste030.de" in doms,
                                     "domains": doms, "chars": len(t)})
                    except Exception as e:
                        rows.append({"group": group, "lang": lang, "prompt": p, "run": i + 1, "error": str(e)[:200]})
                    time.sleep(1)
    day = datetime.date.today().isoformat()
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump({"date": day, "system": "chatgpt", "model": combo[0], "tool": combo[1], "repeats": REPEATS, "rows": rows},
              open(f"{OUT_DIR}/{day}-chatgpt.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = [r for r in rows if "error" not in r]
    lines = [f"# KI-Panel ChatGPT – {day}", "", f"Modell {combo[0]} mit {combo[1]}, {REPEATS} Durchläufe je Prompt, "
             f"{len(ok)} Antworten, {len(rows) - len(ok)} Fehler.", "",
             "| Gruppe | Sprache | Antworten | Nennung GL030 | Zitat gaesteliste030.de |", "|---|---|---|---|---|"]
    for group in prompts:
        for lang in ("de", "en"):
            sub = [r for r in ok if r["group"] == group and r["lang"] == lang]
            if sub:
                m = sum(r["mention"] for r in sub); c = sum(r["cited"] for r in sub)
                lines.append(f"| {group} | {lang} | {len(sub)} | {m} ({100 * m / len(sub):.0f} %) | {c} ({100 * c / len(sub):.0f} %) |")
    dom = collections.Counter(d for r in ok for d in r["domains"])
    lines += ["", "## Häufigste zitierte Domains", ""] + [f"- {d}: {n}" for d, n in dom.most_common(15)]
    open(f"{OUT_DIR}/latest.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
