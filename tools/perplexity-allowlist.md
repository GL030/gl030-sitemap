# Perplexity IP-Zulassungsregeln (AEO)

Angelegt: 17.08.2026 per API · 24 Einzel-IPs als Cloudflare IP-Zugriffsregeln (Aktion: Zulassen, Zone gaesteliste030.de)

**Warum:** Perplexity ist kein Cloudflare-verifizierter Bot und wurde vom Super Bot Fight Mode
("manage definite bots", managed_challenge) abgewiesen - 94% seiner 2.023 Anfragen/Woche bekamen 403.
IP-Zulassungsregeln umgehen den Bot Fight Mode dokumentiert; UA-basierte Skip-Regeln tun das auf Pro nicht.

**Quellen der offiziellen IPs (halbjaehrlich abgleichen, Ranges aendern sich):**
- https://www.perplexity.ai/perplexitybot.json  (Index-Crawler PerplexityBot)
- https://www.perplexity.ai/perplexity-user.json  (Abruf-Bot Perplexity-User, holt Seiten fuer Nutzerantworten)

**Stand 17.08.2026:**
- PerplexityBot: 107.20.236.150, 3.224.62.45, 18.210.92.235, 3.222.232.239, 3.211.124.183, 3.231.139.107, 18.97.1.228/30, 18.97.9.96/29
- Perplexity-User: 44.208.221.197, 34.193.163.52, 18.97.21.0/30, 18.97.43.80/29
(/29 und /30 wurden als Einzel-IPs angelegt, da IP-Zugriffsregeln nur /16 und /24 als Range akzeptieren)

**Messgroesse:** GA4 sessionSource enthaelt "perplexity" - Baseline 11 Sessions in 6 Wochen (03.07.-16.08.).
Zweitindikator: Cloudflare-403-Quote fuer UA %Perplexity% (Baseline 94%) muss Richtung 0 fallen.
Erwartung: sichtbarer Effekt binnen 2-3 Wochen (Perplexity versuchte ~290 Abrufe/Tag).
