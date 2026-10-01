"""Builds gh_pages/value_metrics.html -- the value scanner dashboard.

Sources (read-only, produced by ../value_metrics.py, never fetched here):
  ../data/value_metrics/latest.csv                 today's grades for every equity
  ../data/value_metrics/alerts.csv                 every cheap-zone entry (sent or not)
  ../data/value_metrics/verdicts/{date}_{T}.json   Maxwell's reasoning per alert
  ../data/value_metrics/outcomes.csv               forward returns vs SPY
  ../data/value_metrics/industry_targets_*.csv     peer cutoffs

Live dashboard page (fixed filename, overwritten each run). run_value_metrics.bat
calls this after the scan and publishes it.
"""

import glob
import json
import math
import os
from datetime import datetime

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
STATE = os.path.join(PROJECT_ROOT, "data", "value_metrics")
OUT = os.path.join(HERE, "value_metrics.html")

RATIOS = [("pe", "P/E"), ("fpe", "Fwd P/E"), ("peg", "PEG"), ("ps", "P/S"),
          ("pb", "P/B"), ("ev_ebitda", "EV/EBITDA"), ("p_fcf", "P/FCF")]
HORIZONS = (21, 63, 126, 252)
ALERT_DAYS = 60


def _clean(v):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return None
    return v


def _round(v, nd=2):
    v = _clean(v)
    return None if v is None else round(float(v), nd)


def _text(v):
    """CSV blanks come back as NaN floats; the page wants strings."""
    v = _clean(v)
    return "" if v is None else str(v)


def _read(path):
    try:
        return pd.read_csv(path)
    except (OSError, ValueError, pd.errors.ParserError):
        return pd.DataFrame()


def _status(s):
    # pandas reads the literal "N/A" status back as NaN
    return s if isinstance(s, str) and s else "N/A"


def stocks(latest):
    """Compact per-ticker rows for the searchable table."""
    out = []
    for r in latest.to_dict("records"):
        row = {
            "t": r["ticker"], "n": _text(r.get("long_name")), "s": _text(r.get("sector")),
            "i": _text(r.get("industry")), "p": _clean(r.get("price")),
            "mc": _clean(r.get("market_cap")), "c": int(r.get("cheap_count") or 0),
            "tg": _round(r.get("target_mean")), "tl": _round(r.get("target_low")), "th": _round(r.get("target_high")),
            "na": int(_clean(r.get("n_analysts")) or 0), "rk": _text(r.get("rec_key")).replace("_", " "),
            "up": _round(100 * (r["target_mean"] / r["price"] - 1)) if _clean(r.get("target_mean")) and _clean(r.get("price")) else None,
            "v": int(r.get("valid_count") or 0), "b": int(r.get("bargain_count") or 0),
            "z": bool(r.get("in_cheap")), "fx": bool(r.get("fx_mismatch")),
        }
        for k, _ in RATIOS:
            val = _clean(r.get(k))
            row[k] = round(val, 2) if val is not None else ("L" if r.get(f"{k}_loss") is True else None)
            row[k + "_s"] = _status(r.get(f"{k}_status"))[0]   # B / C / F / E / N
            row[k + "_c"] = _clean(r.get(f"{k}_cheap"))
        out.append(row)
    return out


def alerts(al, outc):
    if al.empty:
        return []
    cutoff = (datetime.now() - pd.Timedelta(days=ALERT_DAYS)).strftime("%Y-%m-%d")
    al = al[al["date"] >= cutoff].sort_values(["date", "bargain_count", "cheap_count"], ascending=[False, False, False])
    ret = {}
    if not outc.empty:
        for r in outc.to_dict("records"):
            ret[(r["date"], r["ticker"])] = {h: _clean(r.get(f"excess_{h}d")) for h in HORIZONS}
    out = []
    for r in al.to_dict("records"):
        v = {}
        vpath = os.path.join(STATE, "verdicts", f"{r['date']}_{r['ticker']}.json")
        if os.path.exists(vpath):
            try:
                with open(vpath, encoding="utf-8") as f:
                    v = json.load(f).get("verdict", {})
            except (OSError, ValueError):
                v = {}
        out.append({
            "d": r["date"], "t": r["ticker"], "i": _text(r.get("industry")),
            "p": _clean(r.get("price")), "c": int(r.get("cheap_count") or 0), "v": int(r.get("valid_count") or 0),
            "b": int(r.get("bargain_count") or 0),
            "verdict": _clean(r.get("verdict")) or ("NOT ANALYZED" if not r.get("analyzed") else "NO_VERDICT"),
            "llm": _clean(r.get("llm_verdict")) or "", "conf": int(r.get("confidence") or 0),
            "sent": str(r.get("sent")).lower() == "true",
            "blk": _clean(r.get("blockers")) or "", "flags": _clean(r.get("trap_flags")) or "",
            "thesis": v.get("thesis", ""), "bear": v.get("bear_case", ""),
            "cat": v.get("catalysts", []), "risk": v.get("risks", []),
            "x": ret.get((r["date"], r["ticker"]), {}),
        })
    return out


def track_record(outc):
    """Per final verdict: count and mean excess return / hit rate per horizon."""
    if outc.empty:
        return []
    rows = []
    for verdict, g in outc.groupby(outc["verdict"].fillna("NOT ANALYZED")):
        row = {"verdict": verdict, "n": len(g)}
        for h in HORIZONS:
            col = f"excess_{h}d"
            x = g[col].dropna() if col in g else pd.Series(dtype=float)
            row[h] = {"n": len(x), "mean": round(float(x.mean()), 2) if len(x) else None,
                      "hit": round(float((x > 0).mean()) * 100) if len(x) else None}
        rows.append(row)
    return rows


def sector_targets():
    files = sorted(glob.glob(os.path.join(STATE, "industry_targets_*.csv")))
    if not files:
        return [], ""
    t = _read(files[-1])
    if t.empty:
        return [], ""
    t = t[t["level"] == "sector"]
    out = []
    for sector, g in t.groupby("group"):
        row = {"s": sector}
        for k, _ in RATIOS:
            m = g[g["ratio"] == k]
            row[k] = round(float(m["p25"].iloc[0]), 2) if len(m) else None
        out.append(row)
    return out, os.path.basename(files[-1])[len("industry_targets_"):-4]


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:14px;padding-bottom:40px}
a{color:#53c0f0;text-decoration:none}
a:hover{color:#e94560;text-decoration:underline}
.header{background:#16213e;padding:14px 16px;border-bottom:1px solid #0f3460}
.header h1{font-size:1.3rem;color:#7fd4c0;margin-bottom:4px}
.header .sub{color:#a0a0b0;font-size:12px}
.header .sub b{color:#e0e0e0}
.crumb{padding:8px 16px;font-size:12px;background:#141428;border-bottom:1px solid #0f3460}
.wrap{max-width:1200px;margin:0 auto;padding:0 12px}
.kpis{display:flex;gap:10px;flex-wrap:wrap;padding:14px 4px 4px}
.kpi{flex:1 1 130px;background:#16213e;border:1px solid #0f3460;border-radius:8px;padding:10px 12px}
.kpi .kl{color:#a0a0b0;font-size:11px;text-transform:uppercase;letter-spacing:.06em}
.kpi .kv{font-size:1.5rem;font-weight:700;margin-top:4px}
.sec{color:#a0a0b0;font-size:11px;text-transform:uppercase;letter-spacing:.08em;margin:22px 4px 8px}
.note{color:#888;font-size:12px;margin:0 4px 8px;line-height:1.5}
.alert{background:#16213e;border:1px solid #0f3460;border-left:4px solid #555;border-radius:8px;padding:10px 12px;margin:0 0 10px}
.alert.BARGAIN_BUY{border-left-color:#4caf50}.alert.WATCH{border-left-color:#ffd54f}
.alert.VALUE_TRAP{border-left-color:#ef5350}.alert.PASS{border-left-color:#888}
.ah{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px}
.ah .tkr{font-weight:700;font-size:15px;color:#53c0f0}
.ah .ind{color:#a0a0b0;font-size:12px}
.ah .dt{margin-left:auto;color:#666;font-size:11px}
.badge{font-size:10px;font-weight:700;padding:3px 8px;border-radius:10px;letter-spacing:.03em;background:#333;color:#ccc}
.badge.BARGAIN_BUY{background:#1b3a2a;color:#8fe0a0}.badge.WATCH{background:#3a3320;color:#ffd54f}
.badge.VALUE_TRAP{background:#4a2020;color:#ff8a80}.badge.PASS{background:#2a2a3a;color:#aaa}
.ab{font-size:12.5px;color:#c8c8d0;margin-top:6px;line-height:1.5}
.ab .lbl{color:#888}
.blk{color:#ffb74d}
.xr{display:flex;gap:12px;font-size:11px;color:#888;margin-top:6px;flex-wrap:wrap}
.pos{color:#8fe0a0}.neg{color:#ff8a80}
.controls{position:sticky;top:0;z-index:5;background:#1a1a2e;padding:10px 4px;border-bottom:1px solid #0f3460;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.search{flex:1 1 200px;min-width:150px;padding:8px 12px;background:#16213e;border:1px solid #0f3460;border-radius:6px;color:#e0e0e0;font-size:14px;outline:none}
.search:focus{border-color:#7fd4c0}
select{padding:7px 8px;background:#16213e;border:1px solid #0f3460;border-radius:6px;color:#e0e0e0;font-size:13px}
.chip{padding:5px 11px;border-radius:14px;border:1px solid #0f3460;background:#16213e;color:#a0a0b0;font-size:12px;font-weight:600;cursor:pointer;user-select:none;white-space:nowrap}
.chip.on{background:#0f3460;color:#fff;border-color:#7fd4c0}
.tw{overflow-x:auto;border:1px solid #0f3460;border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th{background:#16213e;color:#a0a0b0;font-weight:600;text-align:right;padding:7px 8px;white-space:nowrap;cursor:pointer;position:sticky;top:0}
th.l,td.l{text-align:left}
td{padding:6px 8px;border-top:1px solid #1e2a4a;text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
tr:hover td{background:#1e2a4a}
td.B{color:#8fe0a0;font-weight:700}td.C{color:#c5e1a5}td.F{color:#a0a0b0}td.E{color:#ef9a9a}td.N{color:#555}
.tk{font-weight:700;color:#53c0f0}
.zone{font-size:9px;font-weight:700;padding:2px 5px;border-radius:4px;background:#1b3a2a;color:#8fe0a0;margin-left:4px}
.fx{font-size:9px;padding:2px 5px;border-radius:4px;background:#333;color:#aaa;margin-left:4px}
.sm{color:#888;font-size:11px}
.empty{padding:26px 10px;text-align:center;color:#666}
.footer{text-align:center;padding:24px 10px;color:#555;font-size:11px;line-height:1.7;max-width:900px;margin:0 auto}
@media(max-width:600px){.wrap{padding:0 6px}td,th{padding:5px 6px}}
"""

JS = r"""
var STOCKS = DATA_STOCKS;
var ALERTS = DATA_ALERTS;
var RATIOS = DATA_RATIOS;
var HORIZONS = [21, 63, 126, 252];
var zoneOnly = true, sortKey = 'b', sortDir = -1;

function esc(s){ return String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function num(v, d){ if(v === null || v === undefined) return '&ndash;'; if(v === 'L') return 'loss'; return (+v).toFixed(d == null ? 1 : d); }
function cap(v){ if(!v) return '&ndash;'; if(v >= 1e12) return (v/1e12).toFixed(1)+'T'; if(v >= 1e9) return (v/1e9).toFixed(1)+'B'; return (v/1e6).toFixed(0)+'M'; }
function pct(v){ if(v === null || v === undefined) return '&ndash;'; return '<span class="' + (v >= 0 ? 'pos' : 'neg') + '">' + (v >= 0 ? '+' : '') + v.toFixed(1) + '%</span>'; }
function label(v){ return String(v).replace(/_/g, ' '); }

function renderAlerts(){
  var el = document.getElementById('alerts');
  if(!ALERTS.length){ el.innerHTML = '<div class="empty">No alerts yet. The first ones arrive after the next weekday run (about 1:55 PM PT).</div>'; return; }
  var out = [];
  for(var i = 0; i < ALERTS.length; i++){
    var a = ALERTS[i], x = [];
    for(var h = 0; h < HORIZONS.length; h++){
      var r = a.x[HORIZONS[h]];
      if(r !== null && r !== undefined) x.push(HORIZONS[h] + 'd vs SPY ' + pct(r));
    }
    out.push('<div class="alert ' + esc(a.verdict) + '"><div class="ah">' +
      '<span class="tkr">' + esc(a.t) + '</span><span class="badge ' + esc(a.verdict) + '">' + esc(label(a.verdict)) +
      (a.conf ? ' ' + a.conf + '/5' : '') + '</span><span class="ind">' + esc(a.i) + ' &bull; $' + num(a.p, 2) +
      ' &bull; cheap ' + a.c + '/' + a.v + ', bargain ' + a.b + '</span>' +
      '<span class="dt">' + esc(a.d) + (a.sent ? '' : ' &bull; not sent') + '</span></div>' +
      (a.thesis ? '<div class="ab">' + esc(a.thesis) + '</div>' : '') +
      (a.bear ? '<div class="ab"><span class="lbl">Bear case:</span> ' + esc(a.bear) + '</div>' : '') +
      (a.blk ? '<div class="ab blk">Held back from BARGAIN BUY: ' + esc(a.blk) + '</div>' : '') +
      (a.flags ? '<div class="ab"><span class="lbl">Trap flags:</span> ' + esc(a.flags) + '</div>' : '') +
      (a.cat && a.cat.length ? '<div class="ab"><span class="lbl">Catalysts:</span> ' + esc(a.cat.join('; ')) + '</div>' : '') +
      (a.risk && a.risk.length ? '<div class="ab"><span class="lbl">Risks:</span> ' + esc(a.risk.join('; ')) + '</div>' : '') +
      (x.length ? '<div class="xr">' + x.join('') + '</div>' : '') +
      '</div>');
  }
  el.innerHTML = out.join('');
}

function renderTable(){
  var q = document.getElementById('search').value.trim().toUpperCase();
  var sec = document.getElementById('sector').value;
  var rows = [];
  for(var i = 0; i < STOCKS.length; i++){
    var s = STOCKS[i];
    if(q){
      if(s.t.indexOf(q) !== 0 && s.n.toUpperCase().indexOf(q) < 0 && s.i.toUpperCase().indexOf(q) < 0) continue;
    } else if(zoneOnly && !s.z) continue;
    if(sec && s.s !== sec) continue;
    rows.push(s);
  }
  rows.sort(function(a, b){
    var x = a[sortKey], y = b[sortKey];
    if(x === 'L') x = 1e9; if(y === 'L') y = 1e9;
    if(x === null || x === undefined) x = sortDir > 0 ? 1e12 : -1e12;
    if(y === null || y === undefined) y = sortDir > 0 ? 1e12 : -1e12;
    if(typeof x === 'string') return sortDir * x.localeCompare(y);
    if(x === y) return b.c - a.c;
    return sortDir * (x - y);
  });
  var shown = rows.slice(0, 400), out = [];
  for(var j = 0; j < shown.length; j++){
    var s = shown[j], cells = '';
    for(var k = 0; k < RATIOS.length; k++){
      var key = RATIOS[k][0];
      cells += '<td class="' + s[key + '_s'] + '" title="cheap below ' + num(s[key + '_c']) + '">' + num(s[key]) + '</td>';
    }
    out.push('<tr><td class="l"><span class="tk">' + esc(s.t) + '</span>' + (s.z ? '<span class="zone">CHEAP ZONE</span>' : '') +
      (s.fx ? '<span class="fx">FX</span>' : '') + '<div class="sm">' + esc(s.i) + '</div></td>' +
      '<td>$' + num(s.p, 2) + '</td><td>' + cap(s.mc) + '</td>' +
      '<td' + (s.tl != null && s.th != null ? ' title="analyst range $' + num(s.tl, 2) + ' - $' + num(s.th, 2) + '"' : '') + '>' +
      (s.tg != null ? '$' + num(s.tg, 2) : '&ndash;') + '</td><td>' + pct(s.up) + '</td><td>' + (s.na || '&ndash;') + '</td>' +
      '<td class="l sm">' + esc(s.rk || '') + '</td>' + cells +
      '<td>' + s.c + '/' + s.v + '</td><td>' + s.b + '</td></tr>');
  }
  document.getElementById('rows').innerHTML = out.length ? out.join('') :
    '<tr><td colspan="' + (RATIOS.length + 9) + '" class="empty">No stocks match.</td></tr>';
  document.getElementById('count').textContent = rows.length + (rows.length === 1 ? ' stock' : ' stocks') +
    (rows.length > shown.length ? ' (showing first ' + shown.length + ')' : '') +
    (q ? ' matching "' + q + '"' : (zoneOnly ? ' in the cheap zone' : ' graded'));
}

var ths = document.querySelectorAll('th[data-k]');
for(var i = 0; i < ths.length; i++){
  ths[i].addEventListener('click', function(){
    var k = this.getAttribute('data-k');
    if(sortKey === k) sortDir = -sortDir; else { sortKey = k; sortDir = (k === 't' || k === 'c' || k === 'b' || k === 'mc' || k === 'up' || k === 'na' || k === 'tg') ? -1 : 1; }
    if(k === 't') sortDir = sortKey === k && sortDir === 1 ? 1 : sortDir;
    renderTable();
  });
}
document.getElementById('search').addEventListener('input', renderTable);
document.getElementById('sector').addEventListener('change', renderTable);
var zc = document.querySelectorAll('[data-zone]');
for(var i = 0; i < zc.length; i++){
  zc[i].addEventListener('click', function(){
    for(var j = 0; j < zc.length; j++) zc[j].classList.remove('on');
    this.classList.add('on');
    zoneOnly = this.getAttribute('data-zone') === '1';
    renderTable();
  });
}
renderAlerts();
renderTable();
"""


def build():
    latest = _read(os.path.join(STATE, "latest.csv"))
    al = _read(os.path.join(STATE, "alerts.csv"))
    outc = _read(os.path.join(STATE, "outcomes.csv"))
    st = stocks(latest) if not latest.empty else []
    alist = alerts(al, outc)
    track = track_record(outc)
    targets, tdate = sector_targets()

    run_day = "never"
    snaps = sorted(f for f in os.listdir(STATE) if f.startswith("snapshot_") and "_partial" not in f) if os.path.isdir(STATE) else []
    if snaps:
        run_day = snaps[-1][len("snapshot_"):-4]
    n_zone = sum(1 for s in st if s["z"])
    today_alerts = [a for a in alist if a["d"] == run_day]
    n_buy = sum(1 for a in alist if a["verdict"] == "BARGAIN_BUY")
    sectors = sorted({s["s"] for s in st if s["s"]})

    head = "".join(f'<th data-k="{k}">{lbl}</th>' for k, lbl in RATIOS)
    tgt_head = "".join(f"<th>{lbl}</th>" for _, lbl in RATIOS)
    fmt = lambda v: "&ndash;" if v is None else f"{v:.1f}"
    tgt_rows = "".join(
        f'<tr><td class="l">{t["s"]}</td>' + "".join(f"<td>{fmt(t[k])}</td>" for k, _ in RATIOS) + "</tr>"
        for t in targets)

    if any(r[h]["n"] for r in track for h in HORIZONS):
        def cell(stat):
            if stat["mean"] is None:
                return "<td>&ndash;</td>"
            return f'<td>{stat["mean"]:+.1f}%<div class="sm">{stat["hit"]}% beat SPY, n={stat["n"]}</div></td>'

        cells = []
        for r in track:
            c = "".join(cell(r[h]) for h in HORIZONS)
            cells.append(f'<tr><td class="l">{r["verdict"].replace("_", " ")}</td><td>{r["n"]}</td>{c}</tr>')
        track_html = ('<div class="tw"><table><tr><th class="l">Verdict</th><th>Alerts</th>'
                      + "".join(f"<th>{h}d vs SPY</th>" for h in HORIZONS) + "</tr>" + "".join(cells) + "</table></div>")
    else:
        track_html = ('<div class="empty">No returns yet. The first 1-month results appear about 21 trading days '
                      'after the first alerts. Roughly 100 alerts (6-12 months) are needed before the numbers mean much.</div>')

    js = (JS.replace("DATA_STOCKS", json.dumps(st, separators=(",", ":")))
            .replace("DATA_ALERTS", json.dumps(alist, separators=(",", ":"), default=str))
            .replace("DATA_RATIOS", json.dumps(RATIOS)))
    sector_opts = "".join(f'<option value="{s}">{s}</option>' for s in sectors)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Value Scanner &mdash; Maxwell Bargain Verdicts</title>
<style>{CSS}</style>
</head>
<body>
<div class="header">
  <h1>Value Scanner</h1>
  <div class="sub">Seven valuation ratios graded against industry peers every weekday &bull; Maxwell's verdict on each new cheap stock &bull;
    last run <b>{run_day}</b></div>
</div>
<div class="crumb"><a href="hub.html">&larr; Dashboard Hub</a> &bull; <a href="index.html">Trading Rules Overview</a></div>

<div class="wrap">
  <div class="kpis">
    <div class="kpi"><div class="kl">Stocks graded</div><div class="kv">{len(st):,}</div></div>
    <div class="kpi"><div class="kl">In cheap zone</div><div class="kv">{n_zone}</div></div>
    <div class="kpi"><div class="kl">New on last run</div><div class="kv">{len(today_alerts)}</div></div>
    <div class="kpi"><div class="kl">Bargain buys ({ALERT_DAYS}d)</div><div class="kv" style="color:#8fe0a0">{n_buy}</div></div>
  </div>

  <div class="sec">Recent alerts (last {ALERT_DAYS} days)</div>
  <div id="alerts"></div>

  <div class="sec">Stocks</div>
  <div class="note">Green = cheaper than 75% of industry peers (bold = cheaper than 90%), red = pricier than the median or losing money.
    Hover a ratio for its cheap cutoff, or a target for the analysts' low-high range. Target = Yahoo mean analyst price target. Search any ticker to see how it grades even outside the cheap zone.</div>
  <div class="controls">
    <input type="text" class="search" id="search" placeholder="Search any ticker, company or industry..." autocomplete="off">
    <select id="sector"><option value="">All sectors</option>{sector_opts}</select>
    <span class="chip on" data-zone="1">Cheap zone</span>
    <span class="chip" data-zone="0">All stocks</span>
  </div>
  <div class="sec" id="count"></div>
  <div class="tw"><table>
    <thead><tr><th class="l" data-k="t">Ticker</th><th data-k="p">Price</th><th data-k="mc">Mkt cap</th><th data-k="tg">Target</th><th data-k="up">Upside</th><th data-k="na">Analysts</th><th class="l" data-k="rk">Rating</th>{head}<th data-k="c">Cheap</th><th data-k="b">Bargain</th></tr></thead>
    <tbody id="rows"></tbody>
  </table></div>

  <div class="sec">Track record (excess return vs SPY)</div>
  {track_html}

  <div class="sec">Sector cheap targets ({tdate or 'n/a'})</div>
  <div class="note">The cheap cutoff (25th percentile) per sector. Most stocks are graded against their industry instead, when it has at least 20 peers.
    Banks are graded on P/E, forward P/E, PEG and P/B only; REITs on P/S, EV/EBITDA and P/FCF.</div>
  <div class="tw"><table><tr><th class="l">Sector</th>{tgt_head}</tr>{tgt_rows or '<tr><td class="empty" colspan="8">No targets yet.</td></tr>'}</table></div>
</div>

<div class="footer">
  Data: Yahoo Finance via <code>value_metrics.py</code>, weekdays 1:30 PM PT. A stock enters the cheap zone when most of its ratios
  (at least one earnings ratio and one sales/book/cash-flow ratio) are in the cheapest quarter of its industry, and leaves once it rises
  above the cheapest 35%. PEG is shown but not counted. Foreign ADRs (FX) never alert because Yahoo mixes currencies in their ratios.
  Verdicts come from a local Ollama model; BARGAIN BUY also has to pass hard checks (positive free cash flow, revenue not shrinking,
  no earnings within 7 days, no crash, few red flags). Alerts only, not trade signals.<br>
  Page generated {datetime.now().strftime('%Y-%m-%d %H:%M')}.
</div>

<script>
{js}
</script>
</body>
</html>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {OUT} -- {len(st)} stocks, {n_zone} in zone, {len(alist)} alerts, {len(track)} verdict groups")


if __name__ == "__main__":
    build()
