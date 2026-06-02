"""Generate AI Supply Chain tracker page for GitHub Pages."""
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf
import pandas as pd

OUT_PATH = Path(__file__).parent / "ai_supply_chain.html"
METADATA_CACHE = Path(__file__).parent / "ai_supply_chain_meta.json"
STATE_FILE = Path(__file__).parent.parent / "paper_trader_individual_state.json"
MIN_TICKERS_REQUIRED = 50

CATEGORIES = {
    "AI Chip Designers": ["NVDA","AMD","INTC","AVGO","QCOM","MRVL","ARM","MXL","HIMX","SIMO","AMBA","LSCC","MPWR","POWI"],
    "EDA / Chip IP": ["SNPS","CDNS","RMBS","CEVA","SITM","ALGM"],
    "Chip Foundries": ["TSM","GFS","UMC"],
    "Semiconductor Equipment": ["ASML","AMAT","LRCX","KLAC","ONTO","CAMT","ACLS","TER","COHU","IPGP","MKSI","ENTG"],
    "Chip Testing / Packaging": ["AMKR","ASX","AEHR"],
    "Memory / Storage": ["MU","WDC","STX","PSTG","NTAP"],
    "Networking / Switching": ["ANET","CSCO","CIEN","CALX","VIAV"],
    "Optical / Photonics": ["COHR","LITE","AAOI","GLW"],
    "Connectors / Components": ["APH","TEL","HUBB","MTSI","NDSN"],
    "AI Servers / Hardware": ["SMCI","DELL","HPE","CLS","IBM"],
    "Cloud / Data Center": ["AMZN","MSFT","GOOGL","META","ORCL","CRM","BABA","BIDU"],
    "Data Center REITs": ["EQIX","DLR","IRM"],
    "AI Software / Platforms": ["PLTR","AI","SNOW","DDOG","MDB","PATH","SOUN","BBAI","UPST","DT","ESTC","WDAY","NOW","S"],
    "AI Cybersecurity": ["CRWD","PANW","ZS","FTNT","NET"],
    "Power / Energy": ["VST","CEG","NRG","NEE","SO","EVRG","AES","D","GEV","ETN"],
    "Nuclear / Uranium": ["OKLO","SMR","NNE","CCJ","LEU","BWXT","UEC","UUUU"],
    "Cooling / Thermal": ["VRT","MOD","AAON","GNRC"],
    "Electrical Infrastructure": ["PWR","EME","AYI","POWL"],
    "Contract Manufacturing": ["FLEX","JBL","SANM","BHE"],
    "Semiconductor Materials": ["AEIS","UCTT"],
    "AI / Robotics ETFs": ["BOTZ","ROBT","AIQ","ROBO","SMH","SOXX"],
}


def _load_metadata_cache():
    if METADATA_CACHE.exists():
        age_days = (time.time() - METADATA_CACHE.stat().st_mtime) / 86400
        if age_days < 7:
            with open(METADATA_CACHE) as f:
                return json.load(f)
    return {}


def _save_metadata_cache(cache):
    with open(METADATA_CACHE, "w") as f:
        json.dump(cache, f, indent=2)


def _color(v):
    if v > 0: return "color:#66ff66"
    elif v < 0: return "color:#ff6666"
    return ""


def _load_bot_itd():
    """Load Bot ITD% from paper trader state file."""
    itd = {}
    if not STATE_FILE.exists():
        return itd
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        for ticker, data in state.get("tickers", {}).items():
            trades = data.get("trades", [])
            cap = data.get("starting_capital", 10000)
            pnl = sum(t.get("pnl", 0) for t in trades)
            itd[ticker] = round(pnl / cap * 100, 1) if cap else 0
    except Exception:
        pass
    return itd


def fetch_data(tickers):
    """Fetch current price, Today%, YTD%, 30d%, 7d% for all tickers."""
    all_tickers = list(set(tickers))
    print(f"Fetching data for {len(all_tickers)} tickers...")

    meta_cache = _load_metadata_cache()
    cache_hits = 0

    results = {}
    batch_size = 20
    for i in range(0, len(all_tickers), batch_size):
        batch = all_tickers[i:i+batch_size]
        batch_str = " ".join(batch)
        try:
            data = yf.download(batch_str, period="1y", interval="1d", progress=False, threads=True)
            if data.empty:
                continue

            for ticker in batch:
                try:
                    if len(batch) == 1:
                        close = data["Close"].dropna()
                    else:
                        if ticker not in data["Close"].columns:
                            continue
                        close = data["Close"][ticker].dropna()

                    if len(close) < 5:
                        continue

                    current = float(close.iloc[-1])
                    now = close.index[-1]

                    ytd_start = close.index[close.index >= f"{now.year}-01-01"]
                    ytd_pct = ((current / float(close.loc[ytd_start[0]]) - 1) * 100) if len(ytd_start) > 0 else 0

                    d30 = close.index[close.index >= (now - timedelta(days=35))]
                    pct_30d = ((current / float(close.loc[d30[0]]) - 1) * 100) if len(d30) > 0 else 0

                    d7 = close.index[close.index >= (now - timedelta(days=10))]
                    pct_7d = ((current / float(close.loc[d7[0]]) - 1) * 100) if len(d7) > 0 else 0

                    if ticker in meta_cache:
                        name = meta_cache[ticker].get("name", ticker)
                        industry = meta_cache[ticker].get("industry", "")
                        cache_hits += 1
                    else:
                        info = yf.Ticker(ticker).info
                        name = info.get("shortName", info.get("longName", ticker))
                        industry = info.get("industry", "")
                        meta_cache[ticker] = {"name": name, "industry": industry}

                    today_pct = 0.0
                    try:
                        t_info = yf.Ticker(ticker).info
                        today_pct = t_info.get("regularMarketChangePercent", 0.0) or 0.0
                    except Exception:
                        prev_close = float(close.iloc[-2]) if len(close) >= 2 else current
                        today_pct = ((current / prev_close) - 1) * 100

                    results[ticker] = {
                        "name": name,
                        "industry": industry,
                        "price": round(current, 2),
                        "today": round(today_pct, 1),
                        "ytd": round(ytd_pct, 1),
                        "d30": round(pct_30d, 1),
                        "d7": round(pct_7d, 1),
                    }
                except Exception as e:
                    print(f"  {ticker}: {e}")
        except Exception as e:
            print(f"  Batch error: {e}")

        if (i + batch_size) % 60 == 0:
            print(f"  {i+batch_size}/{len(all_tickers)} done...")
        time.sleep(0.5)

    _save_metadata_cache(meta_cache)
    print(f"  Metadata: {cache_hits} cache hits, {len(meta_cache) - cache_hits} fresh lookups")
    return results


def generate_html(categories, data, bot_itd):
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    sections = []
    for cat, tickers in categories.items():
        rows = []
        for t in tickers:
            d = data.get(t)
            if not d:
                continue
            itd = bot_itd.get(t)
            itd_str = f'{itd:+.1f}%' if itd is not None else "-"
            itd_style = _color(itd) if itd else ""
            rows.append(
                f'<tr>'
                f'<td><strong>{t}</strong></td>'
                f'<td>${d["price"]:,.2f}</td>'
                f'<td style="{_color(d["today"])}">{d["today"]:+.1f}%</td>'
                f'<td style="{_color(d["d7"])}">{d["d7"]:+.1f}%</td>'
                f'<td style="{_color(d["d30"])}">{d["d30"]:+.1f}%</td>'
                f'<td style="{_color(d["ytd"])}">{d["ytd"]:+.1f}%</td>'
                f'<td style="{itd_style}">{itd_str}</td>'
                f'</tr>'
            )
        if rows:
            sections.append(f'<h2>{cat} ({len(rows)})</h2>')
            sections.append(
                '<table><thead><tr>'
                '<th onclick="sortTable(this)">Ticker<span class="sort-arrow"></span></th>'
                '<th onclick="sortTable(this)">Price<span class="sort-arrow"></span></th>'
                '<th onclick="sortTable(this)">Today<span class="sort-arrow"></span></th>'
                '<th onclick="sortTable(this)">7D<span class="sort-arrow"></span></th>'
                '<th onclick="sortTable(this)">30D<span class="sort-arrow"></span></th>'
                '<th onclick="sortTable(this)">YTD<span class="sort-arrow"></span></th>'
                '<th onclick="sortTable(this)">Bot ITD<span class="sort-arrow"></span></th>'
                '</tr></thead><tbody>' + "\n".join(rows) + '</tbody></table>'
            )

    fetched = len(data)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Supply Chain Tracker</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #0d1117; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; padding: 20px; }}
  h1 {{ color: #58a6ff; margin-bottom: 5px; font-size: 1.8em; }}
  .subtitle {{ color: #8b949e; margin-bottom: 20px; font-size: 0.9em; }}
  h2 {{ color: #79c0ff; margin: 30px 0 10px; font-size: 1.2em; border-bottom: 1px solid #21262d; padding-bottom: 5px; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 0.85em; }}
  th {{ background: #161b22; color: #8b949e; padding: 8px 10px; text-align: left; cursor: pointer; user-select: none; position: sticky; top: 0; }}
  th:hover {{ background: #1f2937; }}
  td {{ padding: 6px 10px; border-bottom: 1px solid #21262d; }}
  tr:hover {{ background: #161b22; }}
  .sort-arrow {{ margin-left: 4px; font-size: 0.7em; }}
  .summary {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 15px; margin-bottom: 20px; display: flex; gap: 30px; flex-wrap: wrap; }}
  .stat {{ text-align: center; }}
  .stat-value {{ font-size: 1.5em; font-weight: bold; color: #58a6ff; }}
  .stat-label {{ font-size: 0.8em; color: #8b949e; }}
  a {{ color: #58a6ff; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>AI Supply Chain Tracker</h1>
<p class="subtitle">Updated: {date_str} | <a href="index.html">Back to Dashboard</a></p>

<div class="summary">
  <div class="stat"><div class="stat-value">{fetched}</div><div class="stat-label">Tickers</div></div>
  <div class="stat"><div class="stat-value">{len(categories)}</div><div class="stat-label">Categories</div></div>
</div>

{"".join(sections)}

<script>
function sortTable(th) {{
  const table = th.closest('table');
  const tbody = table.querySelector('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const idx = Array.from(th.parentNode.children).indexOf(th);
  const arrows = th.parentNode.querySelectorAll('.sort-arrow');
  arrows.forEach(a => a.textContent = '');
  const currentDir = th.getAttribute('data-sort-dir') || 'asc';
  const newDir = currentDir === 'asc' ? 'desc' : 'asc';
  th.setAttribute('data-sort-dir', newDir);
  th.querySelector('.sort-arrow').textContent = newDir === 'asc' ? ' ▲' : ' ▼';
  rows.sort((a, b) => {{
    let aVal = a.children[idx].textContent.replace(/[$,%+]/g, '').trim();
    let bVal = b.children[idx].textContent.replace(/[$,%+]/g, '').trim();
    let aNum = parseFloat(aVal), bNum = parseFloat(bVal);
    if (!isNaN(aNum) && !isNaN(bNum)) return newDir === 'asc' ? aNum - bNum : bNum - aNum;
    return newDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
  }});
  rows.forEach(r => tbody.appendChild(r));
}}
</script>
</body>
</html>"""

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Written to {OUT_PATH}")


if __name__ == "__main__":
    all_tickers = []
    for tickers in CATEGORIES.values():
        all_tickers.extend(tickers)
    all_tickers = list(set(all_tickers))

    data = fetch_data(all_tickers)
    fetched = len(data)
    print(f"\nFetched data for {fetched}/{len(all_tickers)} tickers")

    if fetched < MIN_TICKERS_REQUIRED:
        print(f"ABORT: Only {fetched} tickers fetched (min {MIN_TICKERS_REQUIRED}). Not overwriting page.")
        sys.exit(1)

    bot_itd = _load_bot_itd()
    print(f"Bot ITD data: {len(bot_itd)} tickers")
    generate_html(CATEGORIES, data, bot_itd)
