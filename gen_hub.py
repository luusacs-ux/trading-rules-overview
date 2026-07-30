"""Builds gh_pages/hub.html -- the consolidated launcher for every page in the
GitHub Pages site.

Cards are declared in PAGES below; freshness stamps, file sizes and the report
counts are read off disk at build time, so the hub never claims a page is
current when it isn't. Missing files are rendered greyed-out rather than
dropped, which makes a broken refresh task obvious at a glance.

Adding a page: append one row to PAGES and re-run. Nothing here touches
index.html -- that file is hand-maintained (its builder is abandoned/stale).

    python gen_hub.py
"""

import os
import glob
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hub.html")

# (file, title, blurb, accent, badge)
PAGES = [
    ("__LIVE__", "Live Dashboards", "", "", ""),
    ("performance.html", "Paper Trading Performance",
     "Realised P&L, win rate and open positions across every deployed rule family.",
     "#53c0f0", ""),
    ("events_calendar.html", "Event Calendar",
     "FOMC, CPI, jobs and GDP releases plus earnings, ex-dividends and splits per ticker.",
     "#e94560", "NEW"),
    ("confidence_performance.html", "Performance by Confidence",
     "Trade outcomes bucketed by the confidence score assigned at signal time.",
     "#4caf50", ""),
    ("ticker_rankings.html", "Ticker Rankings",
     "Five-factor probability engine ranking of the tradeable universe.",
     "#ffd54f", ""),
    ("options_mispricing.html", "Options Mispricing Scanner",
     "Daily scan for mispriced contracts with open-interest and quality filters.",
     "#ce93d8", ""),
    ("ai_supply_chain.html", "AI Supply Chain Tracker",
     "Sector map of the AI hardware and infrastructure complex.",
     "#ff9800", ""),
    ("shadow_book.html", "Cross-Sectional Shadow Book",
     "Paper book for the cross-sectional prediction engine, tracked out of sample.",
     "#53c0f0", ""),
    ("meta_label_shadow.html", "ML Meta-Label Shadow Test",
     "Offline meta-label model scored against the live trade ledger.",
     "#7fd4c0", ""),
    ("short_squeeze_report.html", "Short Squeeze Monitor",
     "Short interest and days-to-cover screen.",
     "#ef5350", ""),

    ("__REF__", "Rules &amp; Data Reference", "", "", ""),
    ("index.html", "Trading Rules Overview",
     "The master table: every ticker with its rules, backtest and simulation reports.",
     "#e94560", "MAIN"),
    ("active_rules.html", "Active Rules Reference",
     "Full definition of every rule currently in production.",
     "#4caf50", ""),
    ("ticker_inventory.html", "Ticker Data Inventory",
     "Coverage and date ranges for every downloaded ticker.",
     "#53c0f0", ""),

    ("__DOCS__", "Design Documents", "", "", ""),
    ("design_requirements_v8.html", "Design Requirements v8",
     "Living system spec with the section-by-section change log.",
     "#53c0f0", "CURRENT"),
    ("pattern_discovery_design.html", "Pattern Discovery Pipeline",
     "Design for the automated pattern discovery track.",
     "#e94560", ""),
    ("reports/maxwell_design_requirements.html", "Maxwell Design Doc",
     "Spec for the Maxwell options bot.",
     "#ce93d8", ""),
    ("design_requirements_v7.html", "Design Requirements v7",
     "Superseded by v8 -- kept for the change history.",
     "#666", "ARCHIVE"),
]


def stamp(path):
    """-> (human age, freshness class, iso datetime) for a file on disk."""
    full = os.path.join(HERE, path)
    if not os.path.exists(full):
        return ("missing", "f-none", "")
    mt = datetime.fromtimestamp(os.path.getmtime(full))
    days = (datetime.now() - mt).days
    if days == 0:
        age = "today"
    elif days == 1:
        age = "yesterday"
    elif days < 60:
        age = f"{days}d ago"
    else:
        age = mt.strftime("%b %Y")
    cls = "f-fresh" if days <= 2 else ("f-ok" if days <= 8 else "f-old")
    return (age, cls, mt.strftime("%Y-%m-%d %H:%M"))


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#12121f;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:14px}
a{text-decoration:none;color:inherit}
.hero{position:relative;overflow:hidden;padding:34px 20px 28px;text-align:center;
  background:radial-gradient(1100px 320px at 50% -70px,#2a2350 0%,#181832 42%,#12121f 100%);
  border-bottom:1px solid #241f45}
.hero h1{font-size:2rem;font-weight:800;letter-spacing:-.02em;
  background:linear-gradient(92deg,#e94560 0%,#ce93d8 38%,#53c0f0 72%,#4caf50 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;margin-bottom:8px}
.hero p{color:#9a9ab0;font-size:13px;max-width:640px;margin:0 auto}
.stats{display:flex;justify-content:center;flex-wrap:wrap;gap:10px;margin-top:18px}
.stat{background:rgba(255,255,255,.04);border:1px solid #2a2450;border-radius:10px;padding:8px 16px;min-width:96px}
.stat .v{font-size:1.25rem;font-weight:700;color:#fff;line-height:1.15}
.stat .l{font-size:10px;color:#8a8aa0;text-transform:uppercase;letter-spacing:.07em;margin-top:2px}
.wrap{max-width:1180px;margin:0 auto;padding:6px 14px 44px}
.sec{display:flex;align-items:center;gap:12px;margin:30px 2px 14px}
.sec h2{font-size:12px;text-transform:uppercase;letter-spacing:.11em;color:#8a8aa0;font-weight:700;white-space:nowrap}
.sec:after{content:'';flex:1;height:1px;background:linear-gradient(90deg,#2a2450,transparent)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(268px,1fr));gap:14px}
.card{position:relative;display:block;background:#191933;border:1px solid #262650;border-radius:12px;
  padding:16px 16px 13px;overflow:hidden;transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease}
.card:before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--accent);opacity:.85}
.card:hover{transform:translateY(-3px);border-color:var(--accent);box-shadow:0 10px 26px -10px var(--accent)}
.card.dead{opacity:.45}
.card.dead:hover{transform:none;box-shadow:none}
.ct{display:flex;align-items:center;gap:8px;margin-bottom:7px}
.ct h3{font-size:15px;font-weight:700;color:#fff;letter-spacing:-.01em}
.badge{font-size:9px;font-weight:800;letter-spacing:.06em;padding:2px 6px;border-radius:5px;
  background:var(--accent);color:#12121f}
.card p{color:#9a9ab0;font-size:12.5px;line-height:1.5;min-height:38px}
.meta{display:flex;align-items:center;gap:6px;margin-top:11px;padding-top:9px;border-top:1px solid #242448;
  font-size:11px;color:#70708a}
.dot{width:7px;height:7px;border-radius:50%;flex:0 0 auto}
.f-fresh .dot{background:#4caf50;box-shadow:0 0 7px #4caf50}
.f-ok .dot{background:#ffd54f}
.f-old .dot{background:#70708a}
.f-none .dot{background:#ef5350}
.f-none{color:#ef5350}
.go{margin-left:auto;color:var(--accent);font-weight:700;font-size:15px;line-height:1}
.footer{text-align:center;padding:26px 14px 40px;color:#55556a;font-size:11px;line-height:1.8}
.footer a{color:#53c0f0}
@media(max-width:520px){.hero h1{font-size:1.55rem}.grid{grid-template-columns:1fr}.wrap{padding:6px 10px 34px}}
"""


def build():
    n_reports = len(glob.glob(os.path.join(HERE, "reports", "*_backtest_summary_*.html")))
    n_charts = len(glob.glob(os.path.join(HERE, "charts", "*.html")))
    n_sims = len(glob.glob(os.path.join(HERE, "sim_reports", "*.html")))
    n_pages = sum(1 for p in PAGES if not p[0].startswith("__")
                  and os.path.exists(os.path.join(HERE, p[0])))

    body, open_grid = [], False
    for path, title, blurb, accent, badge in PAGES:
        if path.startswith("__"):
            if open_grid:
                body.append("</div>")
            body.append(f'<div class="sec"><h2>{title}</h2></div><div class="grid">')
            open_grid = True
            continue

        age, fcls, exact = stamp(path)
        dead = " dead" if fcls == "f-none" else ""
        badge_html = f'<span class="badge">{badge}</span>' if badge else ""
        title_attr = f' title="last updated {exact}"' if exact else ""
        body.append(
            f'<a class="card{dead}" href="{path}" style="--accent:{accent}"{title_attr}>'
            f'<div class="ct"><h3>{title}</h3>{badge_html}</div>'
            f'<p>{blurb}</p>'
            f'<div class="meta {fcls}"><span class="dot"></span>updated {age}'
            f'<span class="go">&rarr;</span></div></a>'
        )
    if open_grid:
        body.append("</div>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trading System &mdash; Dashboard Hub</title>
<style>{CSS}</style>
</head>
<body>
<div class="hero">
  <h1>Trading System Hub</h1>
  <p>Every live dashboard, reference table and design document in one place.
     The dot on each card shows how recently that page was rebuilt.</p>
  <div class="stats">
    <div class="stat"><div class="v">{n_pages}</div><div class="l">Dashboards</div></div>
    <div class="stat"><div class="v">{n_reports:,}</div><div class="l">Backtest reports</div></div>
    <div class="stat"><div class="v">{n_charts:,}</div><div class="l">Trade charts</div></div>
    <div class="stat"><div class="v">{n_sims:,}</div><div class="l">Sim reports</div></div>
  </div>
</div>

<div class="wrap">
{chr(10).join(body)}
</div>

<div class="footer">
  Freshness: <span style="color:#4caf50">&#9679;</span> rebuilt within 2 days &bull;
  <span style="color:#ffd54f">&#9679;</span> within 8 days &bull;
  <span style="color:#70708a">&#9679;</span> older &bull;
  <span style="color:#ef5350">&#9679;</span> file missing<br>
  Hub generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by <code>gen_hub.py</code> &bull;
  <a href="index.html">Trading Rules Overview</a>
</div>
</body>
</html>
"""

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {OUT} -- {n_pages} pages linked, "
          f"{sum(1 for p in PAGES if not p[0].startswith('__')) - n_pages} missing")


if __name__ == "__main__":
    build()
