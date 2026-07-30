"""Builds gh_pages/events_calendar.html -- consolidated forward calendar of
macro/economic releases and per-ticker corporate events.

Sources (both read-only, never fetched here):
  ../macro_events.json      FOMC + CPI/Jobs/PPI/GDP   (macro_events.py)
  ../upcoming_events.json   earnings / ex-div / splits (refresh_upcoming_events.py)

Live dashboard page (fixed filename, overwrites each run) for the GitHub Pages
hub -- NOT a timestamped backtest report. refresh_events_calendar.bat chains the
two refresh scripts and then this one, and publishes.

Only events dated today-or-later are emitted: upcoming_events.json keeps a
ticker's previous ex-div/earnings entry when a refresh returns nothing new for
it, so the cache can hold dates that have since gone by.
"""

import os
import json
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
MACRO = os.path.join(PROJECT_ROOT, "macro_events.json")
TICKERS = os.path.join(PROJECT_ROOT, "upcoming_events.json")
OUT = os.path.join(HERE, "events_calendar.html")

# kind -> (label, css class). Macro kinds first, then corporate.
KINDS = {
    "FOMC":        ("FOMC Decision", "k-fomc"),
    "CPI":         ("CPI", "k-cpi"),
    "Jobs Report": ("Jobs Report", "k-jobs"),
    "PPI":         ("PPI", "k-ppi"),
    "GDP":         ("GDP", "k-gdp"),
    "earnings":    ("Earnings", "k-earn"),
    "ex_dividend": ("Ex-Dividend", "k-div"),
    "split":       ("Split", "k-split"),
}
MACRO_KINDS = ("FOMC", "CPI", "Jobs Report", "PPI", "GDP")


def _mtime(path):
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
    except OSError:
        return "missing"


def _load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def collect(today):
    """-> list of {date, kind, ticker, detail, macro} sorted by date then kind."""
    events = []

    macro = _load(MACRO, {})
    for e in macro.get("events", []):
        if e.get("date", "") >= today and e.get("kind") in KINDS:
            events.append({"date": e["date"], "kind": e["kind"],
                           "ticker": "", "detail": "", "macro": 1})

    tickers = _load(TICKERS, {})
    for tkr, entry in tickers.items():
        earn = entry.get("earnings") or {}
        if earn.get("date", "") >= today:
            session = (earn.get("session") or "").upper()
            events.append({"date": earn["date"], "kind": "earnings", "ticker": tkr,
                           "detail": session, "macro": 0})

        exd = entry.get("ex_dividend") or {}
        if exd.get("date", "") >= today:
            amt = exd.get("amount")
            events.append({"date": exd["date"], "kind": "ex_dividend", "ticker": tkr,
                           "detail": f"${amt:.2f}" if amt else "", "macro": 0})

        for sp in entry.get("splits", []):
            if sp.get("date", "") >= today:
                ratio = sp.get("ratio")
                events.append({"date": sp["date"], "kind": "split", "ticker": tkr,
                               "detail": f"{ratio:g}:1" if ratio else "", "macro": 0})

    order = list(KINDS)
    events.sort(key=lambda e: (e["date"], order.index(e["kind"]), e["ticker"]))
    return events


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:14px;padding-bottom:40px}
a{color:#53c0f0;text-decoration:none}
a:hover{color:#e94560;text-decoration:underline}
.header{background:#16213e;padding:14px 16px;border-bottom:1px solid #0f3460}
.header h1{font-size:1.3rem;color:#e94560;margin-bottom:4px}
.header .sub{color:#a0a0b0;font-size:12px}
.header .sub b{color:#e0e0e0}
.crumb{padding:8px 16px;font-size:12px;background:#141428;border-bottom:1px solid #0f3460}
.wrap{max-width:1100px;margin:0 auto;padding:0 12px}
.next-strip{display:flex;gap:10px;overflow-x:auto;padding:14px 4px 6px;scrollbar-width:thin}
.mcard{flex:0 0 auto;min-width:132px;background:#16213e;border:1px solid #0f3460;border-left-width:4px;border-radius:8px;padding:10px 12px}
.mcard .mk{font-size:12px;font-weight:700;letter-spacing:.02em}
.mcard .md{color:#a0a0b0;font-size:11px;margin-top:3px}
.mcard .mc{font-size:1.35rem;font-weight:700;margin-top:6px;line-height:1}
.mcard .mc small{font-size:11px;font-weight:400;color:#a0a0b0;margin-left:3px}
.sec{color:#a0a0b0;font-size:11px;text-transform:uppercase;letter-spacing:.08em;margin:16px 4px 2px}
.controls{position:sticky;top:0;z-index:5;background:#1a1a2e;padding:10px 4px;border-bottom:1px solid #0f3460;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.search{flex:1 1 200px;min-width:150px;padding:8px 12px;background:#16213e;border:1px solid #0f3460;border-radius:6px;color:#e0e0e0;font-size:14px;outline:none}
.search:focus{border-color:#e94560}
.chip{padding:5px 11px;border-radius:14px;border:1px solid #0f3460;background:#16213e;color:#a0a0b0;font-size:12px;font-weight:600;cursor:pointer;user-select:none;white-space:nowrap}
.chip:hover{border-color:#53c0f0;color:#e0e0e0}
.chip.on{background:#0f3460;color:#fff;border-color:#53c0f0}
.chip.k-fomc.on{background:#5c2233;border-color:#e94560;color:#ff8fa3}
.chip.k-earn.on{background:#1b3a2a;border-color:#4caf50;color:#8fe0a0}
.chip.k-div.on{background:#3a3320;border-color:#ffd54f;color:#ffd54f}
.chip.k-split.on{background:#32234a;border-color:#ce93d8;color:#ce93d8}
.daygroup{margin-top:14px}
.dayhdr{display:flex;align-items:baseline;gap:10px;padding:6px 4px;border-bottom:1px solid #1e2a4a}
.dayhdr .dd{font-weight:700;color:#53c0f0;font-size:13px}
.dayhdr .dw{color:#a0a0b0;font-size:12px}
.dayhdr .dc{margin-left:auto;color:#555;font-size:11px}
.dayhdr.today .dd{color:#e94560}
.dayhdr.today .dw:after{content:' - today';color:#e94560;font-weight:600}
.row{display:flex;align-items:center;gap:10px;padding:7px 6px;border-bottom:1px solid #1e2a4a;flex-wrap:wrap}
.row:hover{background:#1e2a4a}
.tag{flex:0 0 auto;font-size:10px;font-weight:700;padding:3px 8px;border-radius:10px;letter-spacing:.03em}
.k-fomc{background:#5c2233;color:#ff8fa3;border-left-color:#e94560}
.k-cpi{background:#4a3320;color:#ffb74d;border-left-color:#ff9800}
.k-jobs{background:#1e3a4a;color:#7fd4f0;border-left-color:#53c0f0}
.k-ppi{background:#3a2f1c;color:#ffd54f;border-left-color:#ffd54f}
.k-gdp{background:#243b2c;color:#8fe0a0;border-left-color:#4caf50}
.k-earn{background:#1b3a2a;color:#8fe0a0}
.k-div{background:#3a3320;color:#ffd54f}
.k-split{background:#32234a;color:#ce93d8}
.tkr{font-weight:700;color:#53c0f0;min-width:62px}
.macro-name{font-weight:600;color:#e0e0e0}
.detail{color:#a0a0b0;font-size:12px}
.sess{font-size:10px;font-weight:700;padding:2px 6px;border-radius:4px;background:#0f3460;color:#a0c8e0}
.away{margin-left:auto;color:#666;font-size:11px;white-space:nowrap}
.empty{padding:34px 10px;text-align:center;color:#666}
.footer{text-align:center;padding:20px 10px;color:#555;font-size:11px;line-height:1.7}
@media(max-width:480px){.tkr{min-width:52px}.row{gap:7px;padding:7px 2px}.wrap{padding:0 6px}}
"""

JS = """
var TODAY = DATA_TODAY;
var EVENTS = DATA_EVENTS;
var LABEL = DATA_LABELS;
var DOW = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
var MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
var range = 30;
var types = {macro:true, earnings:true, ex_dividend:true, split:true};

function daysOut(d){
  var a = new Date(TODAY + 'T00:00:00'), b = new Date(d + 'T00:00:00');
  return Math.round((b - a) / 86400000);
}
function fmtDay(d){
  var p = d.split('-');
  var dt = new Date(d + 'T00:00:00');
  return {w: DOW[dt.getDay()], t: MON[+p[1] - 1] + ' ' + (+p[2]) + ', ' + p[0]};
}
function away(n){
  if(n === 0) return 'today';
  if(n === 1) return 'tomorrow';
  return 'in ' + n + 'd';
}
function bucket(e){ return e.macro ? 'macro' : e.kind; }

function render(){
  var q = document.getElementById('search').value.trim().toUpperCase();
  var out = [], shown = 0, groups = {}, order = [];

  for(var i = 0; i < EVENTS.length; i++){
    var e = EVENTS[i];
    if(!types[bucket(e)]) continue;
    var n = daysOut(e.date);
    if(range > 0 && n > range) continue;
    if(q && e.ticker.indexOf(q) !== 0 && LABEL[e.kind].toUpperCase().indexOf(q) < 0) continue;
    if(!groups[e.date]){ groups[e.date] = []; order.push(e.date); }
    groups[e.date].push(e);
    shown++;
  }

  for(var g = 0; g < order.length; g++){
    var d = order[g], f = fmtDay(d), n = daysOut(d), list = groups[d];
    out.push('<div class="daygroup"><div class="dayhdr' + (n === 0 ? ' today' : '') + '">' +
             '<span class="dd">' + f.t + '</span><span class="dw">' + f.w + '</span>' +
             '<span class="dc">' + list.length + (list.length === 1 ? ' event' : ' events') + '</span></div>');
    for(var j = 0; j < list.length; j++){
      var e = list[j], cls = e.macro ? 'k-' + e.kind.toLowerCase().split(' ')[0] :
              (e.kind === 'earnings' ? 'k-earn' : e.kind === 'ex_dividend' ? 'k-div' : 'k-split');
      out.push('<div class="row"><span class="tag ' + cls + '">' + LABEL[e.kind] + '</span>' +
               (e.macro ? '<span class="macro-name">US Macro Release</span>' :
                          '<span class="tkr">' + e.ticker + '</span>') +
               (e.detail ? (e.kind === 'earnings' ? '<span class="sess">' + e.detail + '</span>'
                                                  : '<span class="detail">' + e.detail + '</span>') : '') +
               '<span class="away">' + away(n) + '</span></div>');
    }
    out.push('</div>');
  }

  document.getElementById('timeline').innerHTML =
    shown ? out.join('') : '<div class="empty">No events match these filters.</div>';
  document.getElementById('count').textContent =
    shown + (shown === 1 ? ' event' : ' events') +
    (range > 0 ? ' in the next ' + range + ' days' : ' scheduled');
}

document.getElementById('search').addEventListener('input', render);

var rchips = document.querySelectorAll('[data-range]');
for(var i = 0; i < rchips.length; i++){
  rchips[i].addEventListener('click', function(){
    for(var j = 0; j < rchips.length; j++) rchips[j].classList.remove('on');
    this.classList.add('on');
    range = +this.getAttribute('data-range');
    render();
  });
}

var tchips = document.querySelectorAll('[data-type]');
for(var i = 0; i < tchips.length; i++){
  tchips[i].addEventListener('click', function(){
    var t = this.getAttribute('data-type');
    types[t] = !types[t];
    this.classList.toggle('on', types[t]);
    render();
  });
}

render();
"""


def build():
    today = date.today().isoformat()
    events = collect(today)

    macro_next = [e for e in events if e["macro"]][:6]
    n_earn = sum(1 for e in events if e["kind"] == "earnings")
    n_div = sum(1 for e in events if e["kind"] == "ex_dividend")
    n_split = sum(1 for e in events if e["kind"] == "split")
    n_macro = sum(1 for e in events if e["macro"])
    n_tickers = len({e["ticker"] for e in events if e["ticker"]})
    week = sum(1 for e in events
               if (date.fromisoformat(e["date"]) - date.today()).days <= 7)

    cards = []
    for e in macro_next:
        label, cls = KINDS[e["kind"]]
        n = (date.fromisoformat(e["date"]) - date.today()).days
        when = "today" if n == 0 else ("tomorrow" if n == 1 else f"{n}<small>days</small>")
        pretty = date.fromisoformat(e["date"]).strftime("%b %d, %Y")
        cards.append(
            f'<div class="mcard {cls}"><div class="mk">{label}</div>'
            f'<div class="md">{pretty}</div><div class="mc">{when}</div></div>'
        )

    labels = {k: v[0] for k, v in KINDS.items()}
    js = (JS.replace("DATA_TODAY", json.dumps(today))
            .replace("DATA_EVENTS", json.dumps(events, separators=(",", ":")))
            .replace("DATA_LABELS", json.dumps(labels)))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Event Calendar &mdash; Macro &amp; Earnings</title>
<style>{CSS}</style>
</head>
<body>
<div class="header">
  <h1>Event Calendar</h1>
  <div class="sub">Scheduled macro releases and corporate events for every production ticker &bull;
    <b>{n_macro}</b> macro &bull; <b>{n_earn}</b> earnings &bull; <b>{n_div}</b> ex-div &bull;
    <b>{n_split}</b> splits &bull; <b>{week}</b> in the next 7 days</div>
</div>
<div class="crumb"><a href="hub.html">&larr; Dashboard Hub</a> &bull; <a href="index.html">Trading Rules Overview</a></div>

<div class="wrap">
  <div class="sec">Next macro releases</div>
  <div class="next-strip">{''.join(cards) or '<div class="empty">No macro events cached.</div>'}</div>

  <div class="controls">
    <input type="text" class="search" id="search" placeholder="Filter by ticker or event type..." autocomplete="off">
    <span class="chip" data-range="7">7d</span>
    <span class="chip on" data-range="30">30d</span>
    <span class="chip" data-range="90">90d</span>
    <span class="chip" data-range="0">All</span>
    <span class="chip k-fomc on" data-type="macro">Macro</span>
    <span class="chip k-earn on" data-type="earnings">Earnings</span>
    <span class="chip k-div on" data-type="ex_dividend">Ex-Div</span>
    <span class="chip k-split on" data-type="split">Splits</span>
  </div>
  <div class="sec" id="count"></div>
  <div id="timeline"></div>
</div>

<div class="footer">
  Macro dates: FOMC from the Fed's published calendar, CPI / Jobs / PPI / GDP from the FRED releases API
  (<code>macro_events.py</code>) &mdash; cache refreshed {_mtime(MACRO)}.<br>
  Corporate events: earnings date + session, ex-dividend and splits for {n_tickers} production tickers
  (<code>refresh_upcoming_events.py</code>) &mdash; cache refreshed {_mtime(TICKERS)}.<br>
  Page generated {datetime.now().strftime('%Y-%m-%d %H:%M')} &bull; BMO = before market open, AMC = after market close.
</div>

<script>
{js}
</script>
</body>
</html>
"""

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {OUT} -- {len(events)} upcoming events "
          f"({n_macro} macro, {n_earn} earnings, {n_div} ex-div, {n_split} splits)")


if __name__ == "__main__":
    build()
