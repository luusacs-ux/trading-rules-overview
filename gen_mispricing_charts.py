"""Generate per-signal mispricing charts for the GitHub Pages options page.

For a given signal, produces a self-contained interactive Plotly HTML:
  - 15m candlesticks from the signal date through the latest available data
  - horizontal lines at the entry price and the OI target price
  - vertical lines at the signal (identified) date and the option expiry date
  - non-trading hours/weekends compressed out via range breaks

Output: gh_pages/charts/{TICKER}_{signal_date}.html
Called by gen_options_mispricing.py per signal; also runnable standalone for one
ticker to eyeball the mispricing's success (did price reach the target line
before the expiry vline?).

    python gen_mispricing_charts.py CAG 2026-06-17 13.16 13.88 2026-06-26 bull
"""
import os
import sys
import pandas as pd
import plotly.graph_objects as go

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GH_PAGES_DIR = os.path.dirname(os.path.abspath(__file__))
STOCKS_DIR = os.path.join(PROJECT_DIR, "backtest_data", "stocks")
CHARTS_DIR = os.path.join(GH_PAGES_DIR, "charts")

# PST regular session (data is normalized to US/Pacific 06:30-13:00)
SESSION_OPEN = "06:30:00"


def _load_15m(ticker):
    path = os.path.join(STOCKS_DIR, f"{ticker}_15m.csv")
    if not os.path.isfile(path):
        return None
    df = pd.read_csv(path)
    tcol = "open_time" if "open_time" in df.columns else df.columns[0]
    df[tcol] = pd.to_datetime(df[tcol], errors="coerce")
    df = df.dropna(subset=[tcol]).rename(columns={tcol: "ts"})
    return df[["ts", "open", "high", "low", "close", "volume"]]


def make_chart(ticker, signal_date, entry_price, target_price, expire_date,
               direction="bull", out_dir=CHARTS_DIR):
    """Build one signal chart. Returns the output filename (basename) or None."""
    df = _load_15m(ticker)
    if df is None or df.empty:
        return None
    entry_price = float(entry_price)
    target_price = float(target_price)
    start = pd.Timestamp(f"{signal_date} 00:00:00")
    df = df[df["ts"] >= start]
    if df.empty:
        return None
    last_ts = df["ts"].max()

    fig = go.Figure(go.Candlestick(
        x=df["ts"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        name=ticker, increasing_line_color="#4caf50", decreasing_line_color="#ef5350",
    ))

    # horizontal reference lines: entry + target
    fig.add_hline(y=entry_price, line=dict(color="#53c0f0", width=1.5, dash="dash"),
                  annotation_text=f"Entry ${entry_price:.2f}",
                  annotation_position="top left",
                  annotation_font_color="#53c0f0")
    tgt_color = "#ffd700"
    fig.add_hline(y=target_price, line=dict(color=tgt_color, width=1.5, dash="dot"),
                  annotation_text=f"Target ${target_price:.2f}",
                  annotation_position="bottom left",
                  annotation_font_color=tgt_color)

    # vertical lines: identified date + expiry date (placed at session open so
    # they land inside the visible range after range-breaks compress off-hours)
    v_sig = pd.Timestamp(f"{signal_date} {SESSION_OPEN}")
    v_exp = pd.Timestamp(f"{expire_date} {SESSION_OPEN}")
    for vx, label, col in [(v_sig, "Identified", "#a0a0b0"), (v_exp, "Expiry", "#e94560")]:
        fig.add_vline(x=vx.to_pydatetime().timestamp() * 1000,
                      line=dict(color=col, width=1.5, dash="dash"))
        fig.add_annotation(x=vx, y=1, yref="paper", text=label, showarrow=False,
                           font=dict(color=col, size=11), yanchor="bottom")

    # did it hit? (target reached in the correct direction before expiry)
    pre_exp = df[df["ts"] <= v_exp]
    hit = False
    if not pre_exp.empty:
        if direction == "bull":
            hit = pre_exp["high"].max() >= target_price
        else:
            hit = pre_exp["low"].min() <= target_price
    status = "✓ HIT" if hit else "✗ no-hit"

    fig.update_layout(
        title=(f"{ticker} — mispricing {signal_date} ({direction}) &nbsp; "
               f"entry ${entry_price:.2f} → target ${target_price:.2f} by {expire_date} "
               f"&nbsp; <b>{status}</b>"),
        template="plotly_dark", paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
        font=dict(color="#e0e0e0"), height=640, margin=dict(l=50, r=30, t=60, b=40),
        xaxis_rangeslider_visible=False,
        xaxis=dict(rangebreaks=[
            dict(bounds=[13, 6.5], pattern="hour"),       # hide 13:00-06:30 PT
            dict(bounds=["sat", "mon"]),                    # hide weekends
        ]),
    )

    os.makedirs(out_dir, exist_ok=True)
    fname = f"{ticker}_{signal_date}.html"
    fig.write_html(os.path.join(out_dir, fname), include_plotlyjs="cdn",
                   full_html=True)
    return fname


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 5:
        print("usage: gen_mispricing_charts.py TICKER SIGNAL_DATE ENTRY TARGET EXPIRE [dir]")
        sys.exit(1)
    ticker, sdate, entry, target, expire = a[:5]
    direction = a[5] if len(a) > 5 else "bull"
    out = make_chart(ticker, sdate, entry, target, expire, direction)
    print(f"wrote {out}" if out else "FAILED (no data / empty)")
