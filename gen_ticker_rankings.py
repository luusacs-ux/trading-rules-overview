"""Builds gh_pages/ticker_rankings.html from logs/probability_engine_rank.csv.

Live dashboard page (fixed filename, overwrites each run) for the GitHub Pages
hub -- NOT a timestamped backtest report. Run probability_engine.py first to
refresh the CSV, then this to rebuild the page. Both are chained by
refresh_ticker_rankings.bat (weekly scheduled task).
"""

import os
from datetime import datetime

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
CSV = os.path.join(PROJECT_ROOT, "logs", "probability_engine_rank.csv")
OUT = os.path.join(HERE, "ticker_rankings.html")


def cell_color(v, lo, hi):
    v = max(lo, min(hi, v))
    t = (v - lo) / (hi - lo)
    r = int(220 - 140 * t)
    g = int(70 + 130 * t)
    return f"rgb({r},{g},80)"


def build():
    df = pd.read_csv(CSV)
    n = len(df)
    n_etf = int((df.quote_type == "ETF").sum())
    n_lev = int((df.leverage != 1).sum())
    bull = int((df.regime == "BULL").sum())
    top_eq = df[df.quote_type == "EQUITY"].iloc[0]
    csv_mtime = datetime.fromtimestamp(os.path.getmtime(CSV)).strftime("%Y-%m-%d %H:%M")

    rows = []
    for _, r in df.iterrows():
        lev = int(r.leverage)
        badge = "" if lev == 1 else f'<span class="lev">{"+" if lev>0 else ""}{lev}x</span>'
        reg_cls = {"BULL": "bull", "CAUTION": "caution", "BEAR": "bear"}.get(r.regime, "unk")
        is_eq = r.quote_type == "EQUITY"
        s_style = f"background:{cell_color(r.strength,0,1)};color:#fff" if is_eq else "color:#888"
        s_txt = f"{r.strength:.2f}" if is_eq else "&mdash;"
        d_style = f"background:{cell_color(r.decay_mult,0,1)};color:#fff" if lev != 1 else "color:#888"
        d_txt = f"{r.decay_mult:.2f}" if lev != 1 else "1.00"
        rows.append(
            f'<tr><td class="rank">{int(r["rank"])}</td>'
            f'<td class="tk">{r.ticker}{badge}</td><td class="qt">{r.quote_type}</td>'
            f"<td>${r.price:,.2f}</td><td>${r.target_price:,.2f}</td>"
            f'<td class="pos">+{r.target_pct:.1f}%</td><td>{r.prob_hit_pct:.0f}%</td>'
            f'<td>{r.rule_wr_pct:.0f}%</td><td class="num">{int(r.n_prod_rules)}</td>'
            f'<td><span class="reg {reg_cls}">{r.regime}</span></td><td>{r.arb_edge:.2f}</td>'
            f'<td style="{s_style}">{s_txt}</td><td style="{d_style}">{d_txt}</td>'
            f'<td class="comp">{r.composite_score:.4f}</td></tr>'
        )
    table_rows = "\n".join(rows)

    lev_df = df[df.leverage != 1].sort_values("decay_mult")
    corr = "".join(
        f'<li><b>{r.ticker}</b> ({"+" if r.leverage>0 else ""}{int(r.leverage)}x, '
        f'&sigma;={r.sigma_annual:.1f}) &rarr; decay &times;{r.decay_mult:.2f}, rank #{int(r["rank"])}</li>'
        for _, r in lev_df.head(6).iterrows()
    )

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Traded Ticker Rankings</title>
<style>
:root{{--bg:#0f1419;--card:#1a2230;--ink:#e6edf3;--mut:#8b98a9;--line:#2a3444;--acc:#4a9eff}}
@media(prefers-color-scheme:light){{:root{{--bg:#f5f7fa;--card:#fff;--ink:#1a2230;--mut:#5a6673;--line:#e2e8f0;--acc:#2563eb}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;padding:20px}}
a.back{{color:var(--acc);text-decoration:none;font-size:13px}}
h1{{font-size:24px;margin:8px 0 4px}}.sub{{color:var(--mut);margin-bottom:18px}}
.cards{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}}
.c{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 18px;min-width:120px}}
.c .v{{font-size:22px;font-weight:700}}.c .l{{color:var(--mut);font-size:12px}}
.method,.callout{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 20px;margin-bottom:16px}}
.callout{{border-left:3px solid var(--acc)}}
.method code{{color:var(--acc);font-weight:600}}.method ul,.callout ul{{margin:8px 0 0;padding-left:20px}}.method li{{margin:4px 0}}
.wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:10px}}
table{{border-collapse:collapse;width:100%;font-size:13px;min-width:900px}}
th{{background:var(--card);text-align:right;padding:9px 10px;position:sticky;top:0;cursor:pointer;white-space:nowrap;border-bottom:2px solid var(--line);user-select:none}}
th:hover{{color:var(--acc)}}th.l,td.tk,td.qt{{text-align:left}}
td{{padding:7px 10px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}}
tr:hover td{{background:rgba(74,158,255,.06)}}
.rank{{color:var(--mut);font-variant-numeric:tabular-nums}}.tk{{font-weight:700}}.comp{{font-weight:700;font-variant-numeric:tabular-nums}}
.qt{{color:var(--mut);font-size:11px}}.pos{{color:#3fb950}}.num{{color:var(--mut)}}
.lev{{display:inline-block;margin-left:6px;background:#b5432e;color:#fff;font-size:10px;padding:1px 5px;border-radius:4px;font-weight:600}}
.reg{{font-size:11px;padding:2px 7px;border-radius:4px;font-weight:600}}
.reg.bull{{background:#1a4a2e;color:#5fd88a}}.reg.caution{{background:#4a3f1a;color:#e0c060}}.reg.bear{{background:#4a1a1a;color:#e07070}}.reg.unk{{background:#2a3444;color:#8b98a9}}
</style></head><body>
<a class="back" href="index.html">&larr; Reports hub</a>
<h1>Traded Ticker Rankings</h1>
<div class="sub">Forward-looking composite score &middot; {n} tickers with deployed production rules &middot; data as of {csv_mtime}</div>
<div class="cards">
<div class="c"><div class="v">{n}</div><div class="l">tickers ranked</div></div>
<div class="c"><div class="v">{n_etf}</div><div class="l">ETFs ({n_lev} leveraged/inverse)</div></div>
<div class="c"><div class="v">{bull}</div><div class="l">in BULL regime</div></div>
<div class="c"><div class="v">{top_eq.ticker}</div><div class="l">top-ranked company</div></div>
</div>
<div class="method">
<b>Score</b> = <code>EV &times; regime &times; arb-edge &times; strength &times; decay</code>, where EV = target% &times; P(hit).
<ul>
<li><b>Future price</b> &mdash; target from blended rule-PTPnL + 1&sigma; vol move; P(hit) via Black-Scholes d2</li>
<li><b>Company strength</b> &mdash; <b>dominant lever</b>: profit margin, ROE, revenue &amp; earnings growth, debt/equity, free cash flow (yfinance) mapped to a factor in <b>[0.25, 1.0]</b> &mdash; a weak company is cut up to 74%. ETFs pass through at 1.0 and are judged by decay instead</li>
<li><b>Regime</b> &mdash; TickerRegimeFilter state: BULL &times;1.0 &middot; CAUTION &times;0.75 &middot; BEAR &times;0.5</li>
<li><b>ETF decay</b> &mdash; leveraged/inverse variance drag <code>exp(&minus;&frac12;&middot;L(L&minus;1)&middot;&sigma;&sup2;&middot;T)</code>, applied at each fund's <b>exact</b> per-ETF value. Plain equities = 1.0</li>
</ul>
</div>
<div class="callout">
<b>Strength leads, decay disciplines.</b> Company fundamentals drive the equity ranking; every leveraged/inverse ETF carries its own precise variance-drag penalty, so daily-reset junk stays buried on any hold:
<ul>{corr}</ul>
</div>
<div class="wrap"><table id="t">
<thead><tr>
<th onclick="s(0,1)">#</th><th class="l" onclick="s(1,0)">Ticker</th><th class="l" onclick="s(2,0)">Type</th>
<th onclick="s(3,1)">Price</th><th onclick="s(4,1)">Target</th><th onclick="s(5,1)">Tgt%</th>
<th onclick="s(6,1)">P(hit)</th><th onclick="s(7,1)">WR</th><th onclick="s(8,1)">Rules</th>
<th onclick="s(9,0)">Regime</th><th onclick="s(10,1)">Arb</th><th onclick="s(11,1)">Strength</th>
<th onclick="s(12,1)">Decay</th><th onclick="s(13,1)">Score</th>
</tr></thead><tbody>
{table_rows}
</tbody></table></div>
<script>
function s(i,num){{var tb=document.querySelector('#t tbody');var rows=[].slice.call(tb.rows);
var asc=tb.dataset.k==i+''?tb.dataset.a!=='1':false;tb.dataset.k=i;tb.dataset.a=asc?'1':'0';
function g(r){{var t=r.cells[i].innerText.replace(/[$,%+x]/g,'').trim();return num?(parseFloat(t)||0):t;}}
rows.sort(function(a,b){{var x=g(a),y=g(b);return (x<y?-1:x>y?1:0)*(asc?1:-1);}});
rows.forEach(function(r){{tb.appendChild(r);}});}}
</script>
</body></html>"""

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT} ({n} rows, data as of {csv_mtime})")


if __name__ == "__main__":
    build()
