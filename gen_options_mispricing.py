"""
Generate options mispricing GitHub Pages report from signal history CSV.
Called by options_mispricing_scanner.py after each scan, or run standalone.
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GH_PAGES_DIR = os.path.dirname(os.path.abspath(__file__))
SIGNAL_HISTORY_FILE = os.path.join(PROJECT_DIR, "data", "options_signal_history.csv")
IV_HISTORY_FILE = os.path.join(PROJECT_DIR, "data", "options_iv_history.csv")
OUTPUT_FILE = os.path.join(GH_PAGES_DIR, "options_mispricing.html")
CHARTS_DIR = os.path.join(GH_PAGES_DIR, "charts")


def annotate_charts(records):
    """Attach a per-signal chart filename (charts/{ticker}_{signal_date}.html) to
    each record, generating the chart if missing. Closed-signal charts are stable
    once data covers their expiry, so we skip regeneration when the file exists."""
    try:
        from gen_mispricing_charts import make_chart
    except Exception:
        for r in records:
            r["chart"] = None
        return records
    for r in records:
        r["chart"] = None
        try:
            tkr = r.get("ticker")
            sd = str(r.get("signal_date", "") or "")
            exp = str(r.get("near_exp", "") or "")
            if not (tkr and sd and exp):
                continue
            existing = os.path.join(CHARTS_DIR, f"{tkr}_{sd}.html")
            if os.path.isfile(existing):
                r["chart"] = os.path.basename(existing)
            else:
                r["chart"] = make_chart(tkr, sd, r["price"], r["oi_target"], exp,
                                        r.get("direction", "bull"))
        except Exception:
            r["chart"] = None
    return records


def score_to_stars(score):
    if score >= 80:
        return "★★★★★"
    if score >= 60:
        return "★★★★☆"
    if score >= 40:
        return "★★★☆☆"
    if score >= 20:
        return "★★☆☆☆"
    return "★☆☆☆☆"


def load_signals():
    if not os.path.exists(SIGNAL_HISTORY_FILE):
        return pd.DataFrame()
    return pd.read_csv(SIGNAL_HISTORY_FILE)


def load_iv_history():
    if not os.path.exists(IV_HISTORY_FILE):
        return pd.DataFrame()
    return pd.read_csv(IV_HISTORY_FILE)


def compute_hit_stats(df):
    if df.empty or "hit" not in df.columns:
        return None
    checked = df[df["hit"].notna() & (df["hit"] != "")]
    if checked.empty:
        return None
    checked = checked.copy()
    checked["hit"] = pd.to_numeric(checked["hit"], errors="coerce")
    checked = checked[checked["hit"].notna()]
    if checked.empty:
        return None
    total = len(checked)
    hits = int(checked["hit"].sum())
    by_stars = {}
    for _, row in checked.iterrows():
        stars = score_to_stars(row["score"])
        if stars not in by_stars:
            by_stars[stars] = {"total": 0, "hits": 0}
        by_stars[stars]["total"] += 1
        if row["hit"] == 1:
            by_stars[stars]["hits"] += 1
    return {
        "total": total,
        "hits": hits,
        "hit_rate": round((hits / total) * 100, 1) if total > 0 else 0,
        "by_stars": by_stars,
    }


def build_today_signals(df):
    if df.empty or "signal_date" not in df.columns:
        return [], []
    today = datetime.now().strftime("%Y-%m-%d")
    today_df = df[df["signal_date"] == today]
    if today_df.empty:
        dates = sorted(df["signal_date"].unique(), reverse=True)
        if dates:
            today_df = df[df["signal_date"] == dates[0]]
            today = dates[0]
    bullish = today_df[today_df["direction"] == "bull"].sort_values("score", ascending=False)
    bearish = today_df[today_df["direction"] == "bear"].sort_values("score", ascending=False)
    return bullish.to_dict("records"), bearish.to_dict("records")


def build_recent_history(df, days=30):
    if df.empty or "hit" not in df.columns:
        return []
    checked = df[df["hit"].notna() & (df["hit"] != "")].copy()
    if checked.empty:
        return []
    checked["hit"] = pd.to_numeric(checked["hit"], errors="coerce")
    checked = checked.sort_values("signal_date", ascending=False).head(100)
    return checked.to_dict("records")


def generate_html(signals_df):
    bullish, bearish = build_today_signals(signals_df)
    hit_stats = compute_hit_stats(signals_df)
    recent = build_recent_history(signals_df)

    # generate + attach per-signal charts (entry/target hlines, date vlines)
    annotate_charts(bullish)
    annotate_charts(bearish)
    annotate_charts(recent)

    if signals_df.empty:
        latest_date = "No data"
        total_signals = 0
    else:
        latest_date = signals_df["signal_date"].max()
        total_signals = len(signals_df)

    today_count = len(bullish) + len(bearish)

    bull_json = json.dumps(bullish, default=str)
    bear_json = json.dumps(bearish, default=str)
    recent_json = json.dumps(recent, default=str)
    hit_json = json.dumps(hit_stats, default=str)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Options Mispricing Scanner</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#1a1a2e;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:14px}}
.header{{background:#16213e;padding:12px 16px;border-bottom:1px solid #0f3460}}
.header h1{{font-size:1.3rem;color:#e94560;margin-bottom:4px}}
.subtitle{{color:#a0a0b0;font-size:12px;margin:4px 0}}
.nav{{padding:8px 16px;font-size:12px;border-bottom:1px solid #1e2a4a}}
.nav a{{color:#53c0f0;text-decoration:none;margin-right:12px}}
.nav a:hover{{color:#e94560;text-decoration:underline}}
.container{{padding:8px 16px;max-width:1200px;margin:0 auto}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:16px 0}}
.card{{background:#16213e;border:1px solid #0f3460;border-radius:8px;padding:16px}}
.card h3{{color:#e94560;font-size:13px;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px}}
.card .big{{font-size:2rem;font-weight:700;color:#53c0f0}}
.card .sub{{font-size:12px;color:#a0a0b0;margin-top:4px}}
.section{{margin:20px 0}}
.section h2{{color:#e94560;font-size:1.1rem;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid #0f3460}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#0f3460;color:#e94560;padding:8px 6px;text-align:right;cursor:pointer;user-select:none;white-space:nowrap;border-bottom:2px solid #e94560;font-size:11px}}
th:first-child{{text-align:left}}
td{{padding:7px 6px;text-align:right;border-bottom:1px solid #1e2a4a}}
td:first-child{{text-align:left;font-weight:600;color:#53c0f0}}
tr:hover{{background:#1e2a4a}}
.green{{color:#4caf50}}
.red{{color:#ef5350}}
.stars{{color:#ffd700;font-size:14px;letter-spacing:1px}}
.bull-tag{{background:#1b3a2a;color:#4caf50;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}}
.bear-tag{{background:#2a1b1b;color:#ef5350;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}}
.hit-bar{{display:flex;align-items:center;gap:8px;margin:6px 0}}
.hit-bar-fill{{height:20px;border-radius:4px;min-width:2px}}
.hit-bar-label{{font-size:12px;white-space:nowrap}}
.empty{{text-align:center;color:#555;padding:40px;font-size:16px}}
.footer{{text-align:center;padding:16px;color:#555;font-size:11px}}
.scroll-x{{overflow-x:auto}}
@media(max-width:480px){{
  table{{font-size:11px}}
  th,td{{padding:5px 3px}}
  th{{font-size:10px}}
  .cards{{grid-template-columns:1fr 1fr}}
  .card .big{{font-size:1.5rem}}
}}
</style>
</head>
<body>
<div class="header">
  <h1>Options Mispricing Scanner</h1>
  <p class="subtitle">Latest scan: {latest_date} &bull; {today_count} signals today &bull; {total_signals} total historical signals</p>
</div>
<div class="nav">
  <a href="index.html">&larr; Trading Rules Overview</a>
  <a href="performance.html">Paper Trading</a>
  <a href="ai_supply_chain.html">AI Supply Chain</a>
</div>
<div class="container">

<div class="cards" id="statsCards"></div>

<div class="section">
  <h2>Bullish Signals</h2>
  <div class="scroll-x">
    <table id="bullTable"><thead><tr>
      <th style="text-align:left">Ticker</th><th>Score</th><th>Rating</th><th>Price</th><th>Target</th><th>Move</th><th>Expiry</th>
    </tr></thead><tbody id="bullBody"></tbody></table>
  </div>
</div>

<div class="section">
  <h2>Bearish Signals</h2>
  <div class="scroll-x">
    <table id="bearTable"><thead><tr>
      <th style="text-align:left">Ticker</th><th>Score</th><th>Rating</th><th>Price</th><th>Target</th><th>Move</th><th>Expiry</th>
    </tr></thead><tbody id="bearBody"></tbody></table>
  </div>
</div>

<div class="section" id="hitRateSection">
  <h2>Historical Hit Rate</h2>
  <div id="hitRateContent"></div>
</div>

<div class="section">
  <h2>Recent Signal History</h2>
  <div class="scroll-x">
    <table id="histTable"><thead><tr>
      <th style="text-align:left">Date</th><th style="text-align:left">Ticker</th><th>Dir</th><th>Score</th><th>Price</th><th>Target</th><th>Actual</th><th>Actual %</th><th>Hit</th>
    </tr></thead><tbody id="histBody"></tbody></table>
  </div>
</div>

</div>
<div class="footer">Auto-generated by options_mispricing_scanner.py</div>

<script>
var bullish = {bull_json};
var bearish = {bear_json};
var recent = {recent_json};
var hitStats = {hit_json};

function stars(score) {{
  if (score >= 80) return "\\u2605\\u2605\\u2605\\u2605\\u2605";
  if (score >= 60) return "\\u2605\\u2605\\u2605\\u2605\\u2606";
  if (score >= 40) return "\\u2605\\u2605\\u2605\\u2606\\u2606";
  if (score >= 20) return "\\u2605\\u2605\\u2606\\u2606\\u2606";
  return "\\u2605\\u2606\\u2606\\u2606\\u2606";
}}

function renderCards() {{
  var c = document.getElementById('statsCards');
  var cards = [];
  cards.push('<div class="card"><h3>Today</h3><div class="big">' + (bullish.length + bearish.length) + '</div><div class="sub">' + bullish.length + ' bullish, ' + bearish.length + ' bearish</div></div>');
  if (hitStats) {{
    cards.push('<div class="card"><h3>Hit Rate</h3><div class="big">' + hitStats.hit_rate + '%</div><div class="sub">' + hitStats.hits + '/' + hitStats.total + ' predictions correct</div></div>');
  }}
  var avgScore = 0;
  var all = bullish.concat(bearish);
  if (all.length > 0) {{
    avgScore = Math.round(all.reduce(function(s,x){{ return s + x.score; }}, 0) / all.length);
  }}
  cards.push('<div class="card"><h3>Avg Score</h3><div class="big">' + avgScore + '</div><div class="sub">out of 100</div></div>');
  var topScore = all.length > 0 ? Math.max.apply(null, all.map(function(x){{ return x.score; }})) : 0;
  cards.push('<div class="card"><h3>Top Score</h3><div class="big stars">' + stars(topScore) + '</div><div class="sub">score ' + topScore + '</div></div>');
  c.innerHTML = cards.join('');
}}

function renderSignals(data, tbodyId) {{
  var tb = document.getElementById(tbodyId);
  if (data.length === 0) {{
    tb.innerHTML = '<tr><td colspan="7" class="empty">No signals</td></tr>';
    return;
  }}
  var html = '';
  for (var i = 0; i < data.length; i++) {{
    var s = data[i];
    var moveClass = s.oi_pct_move > 0 ? 'green' : 'red';
    var exp = s.near_exp || '';
    try {{ exp = new Date(exp + 'T00:00:00').toLocaleDateString('en-US', {{month:'short', day:'numeric'}}); }} catch(e) {{}}
    var tkrCell = s.chart ? '<a href="charts/' + s.chart + '" target="_blank" title="View chart">' + s.ticker + ' \\uD83D\\uDCC8</a>' : s.ticker;
    html += '<tr><td>' + tkrCell + '</td><td>' + s.score + '</td><td class="stars">' + stars(s.score) + '</td><td>$' + Number(s.price).toFixed(2) + '</td><td>$' + Number(s.oi_target).toFixed(2) + '</td><td class="' + moveClass + '">' + (s.oi_pct_move > 0 ? '+' : '') + Number(s.oi_pct_move).toFixed(1) + '%</td><td>' + exp + '</td></tr>';
  }}
  tb.innerHTML = html;
}}

function renderHitRate() {{
  var el = document.getElementById('hitRateContent');
  if (!hitStats) {{
    el.innerHTML = '<p class="empty">No backchecked signals yet</p>';
    return;
  }}
  var html = '<div style="margin-bottom:16px;font-size:15px">Overall: <strong>' + hitStats.hits + '/' + hitStats.total + '</strong> (' + hitStats.hit_rate + '%)</div>';
  var starKeys = Object.keys(hitStats.by_stars).sort().reverse();
  for (var i = 0; i < starKeys.length; i++) {{
    var k = starKeys[i];
    var s = hitStats.by_stars[k];
    var pct = s.total > 0 ? Math.round((s.hits / s.total) * 100) : 0;
    var barWidth = Math.max(2, pct * 2);
    var barColor = pct >= 60 ? '#4caf50' : pct >= 40 ? '#ffb74d' : '#ef5350';
    html += '<div class="hit-bar"><span class="stars" style="min-width:90px">' + k + '</span><div class="hit-bar-fill" style="width:' + barWidth + 'px;background:' + barColor + '"></div><span class="hit-bar-label">' + s.hits + '/' + s.total + ' (' + pct + '%)</span></div>';
  }}
  el.innerHTML = html;
}}

function renderHistory() {{
  var tb = document.getElementById('histBody');
  if (recent.length === 0) {{
    tb.innerHTML = '<tr><td colspan="9" class="empty">No backchecked history yet</td></tr>';
    return;
  }}
  var html = '';
  for (var i = 0; i < recent.length; i++) {{
    var r = recent[i];
    var dirTag = r.direction === 'bull' ? '<span class="bull-tag">BULL</span>' : '<span class="bear-tag">BEAR</span>';
    var actualPrice = r.actual_price != null ? '$' + Number(r.actual_price).toFixed(2) : '-';
    var actualPct = r.actual_pct_move != null ? (r.actual_pct_move > 0 ? '+' : '') + Number(r.actual_pct_move).toFixed(1) + '%' : '-';
    var actualClass = r.actual_pct_move > 0 ? 'green' : r.actual_pct_move < 0 ? 'red' : '';
    var hitIcon = r.hit === 1 || r.hit === true || r.hit === 'True' ? '<span class="green">\\u2713</span>' : r.hit === 0 || r.hit === false || r.hit === 'False' ? '<span class="red">\\u2717</span>' : '-';
    var histTkr = r.chart ? '<a href="charts/' + r.chart + '" target="_blank" title="View chart">' + r.ticker + ' \\uD83D\\uDCC8</a>' : r.ticker;
    html += '<tr><td>' + r.signal_date + '</td><td>' + histTkr + '</td><td>' + dirTag + '</td><td>' + r.score + '</td><td>$' + Number(r.price).toFixed(2) + '</td><td>$' + Number(r.oi_target).toFixed(2) + '</td><td>' + actualPrice + '</td><td class="' + actualClass + '">' + actualPct + '</td><td>' + hitIcon + '</td></tr>';
  }}
  tb.innerHTML = html;
}}

renderCards();
renderSignals(bullish, 'bullBody');
renderSignals(bearish, 'bearBody');
renderHitRate();
renderHistory();
</script>
</body>
</html>"""
    return html


def main():
    signals_df = load_signals()
    html = generate_html(signals_df)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {OUTPUT_FILE} ({len(html):,} bytes)")
    if not signals_df.empty:
        today = signals_df["signal_date"].max()
        today_count = len(signals_df[signals_df["signal_date"] == today])
        print(f"  Latest date: {today}, {today_count} signals")


if __name__ == "__main__":
    main()
