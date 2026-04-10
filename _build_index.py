import json
data_js = """[
  {ticker:"SMCI",stock:178,indiv:178,wr100:3,pnl10:176,avgPnl:49.2,ptpnl:2.17,report:"SMCI_backtest_summary.html"},
  {ticker:"DAL",stock:145,indiv:145,wr100:6,pnl10:141,avgPnl:42.8,ptpnl:1.85,report:"DAL_backtest_summary.html"},
  {ticker:"HAL",stock:375,indiv:375,wr100:0,pnl10:0,avgPnl:36.7,ptpnl:0.00,report:"HAL_backtest_summary.html"},
  {ticker:"BKR",stock:341,indiv:341,wr100:0,pnl10:0,avgPnl:33.3,ptpnl:0.00,report:"BKR_backtest_summary.html"},
  {ticker:"SLB",stock:304,indiv:304,wr100:0,pnl10:0,avgPnl:33.2,ptpnl:0.00,report:"SLB_backtest_summary.html"},
  {ticker:"CRWG",stock:88,indiv:88,wr100:5,pnl10:84,avgPnl:29.9,ptpnl:5.49,report:"CRWG_backtest_summary.html"},
  {ticker:"TSAT",stock:59,indiv:59,wr100:29,pnl10:56,avgPnl:26.9,ptpnl:5.66,report:"TSAT_backtest_summary.html"},
  {ticker:"CI",stock:73,indiv:73,wr100:5,pnl10:72,avgPnl:26.7,ptpnl:1.92,report:"CI_backtest_summary.html"},
  {ticker:"BWET",stock:23,indiv:23,wr100:2,pnl10:23,avgPnl:26.2,ptpnl:5.99,report:"BWET_backtest_summary.html"},
  {ticker:"ELV",stock:129,indiv:129,wr100:23,pnl10:116,avgPnl:24.5,ptpnl:1.60,report:"ELV_backtest_summary.html"},
  {ticker:"HUM",stock:82,indiv:82,wr100:21,pnl10:68,avgPnl:23.8,ptpnl:3.11,report:"HUM_backtest_summary.html"},
  {ticker:"UNH",stock:74,indiv:74,wr100:5,pnl10:71,avgPnl:23.6,ptpnl:1.35,report:"UNH_backtest_summary.html"},
  {ticker:"ASTS",stock:47,indiv:47,wr100:19,pnl10:36,avgPnl:21.1,ptpnl:4.05,report:"ASTS_backtest_summary.html"},
  {ticker:"CLSK",stock:61,indiv:61,wr100:32,pnl10:48,avgPnl:19.5,ptpnl:3.96,report:"CLSK_backtest_summary.html"},
  {ticker:"LNG",stock:40,indiv:40,wr100:16,pnl10:36,avgPnl:18.9,ptpnl:5.43,report:"LNG_backtest_summary.html"},
  {ticker:"USAR",stock:72,indiv:72,wr100:23,pnl10:53,avgPnl:17.9,ptpnl:3.90,report:"USAR_backtest_summary.html"},
  {ticker:"AMZN",stock:37,indiv:37,wr100:26,pnl10:29,avgPnl:11.6,ptpnl:2.54,report:"AMZN_backtest_summary.html"},
  {ticker:"CNBS",stock:17,indiv:17,wr100:17,pnl10:7,avgPnl:7.4,ptpnl:2.47,report:"CNBS_backtest_summary.html"},
  {ticker:"F",stock:5,indiv:5,wr100:4,pnl10:1,avgPnl:7.0,ptpnl:1.96,report:"F_backtest_summary.html"},
  {ticker:"DLTR",stock:9,indiv:9,wr100:6,pnl10:4,avgPnl:6.9,ptpnl:1.37,report:"DLTR_backtest_summary.html"},
  {ticker:"NKE",stock:6,indiv:6,wr100:6,pnl10:0,avgPnl:5.9,ptpnl:1.76,report:"NKE_backtest_summary.html"},
  {ticker:"PFE",stock:0,indiv:0,wr100:0,pnl10:0,avgPnl:0.0,ptpnl:0.00,report:"PFE_backtest_summary.html"}
]"""

summary = "22 tickers &#8226; 2,165 rules &#8226; 31.7%% avg PnL"

with open("gh_pages/index_template.html", "r", encoding="utf-8") as tf:
    tmpl = tf.read()

html = tmpl.replace("{{DATA}}", data_js).replace("{{SUMMARY}}", summary)

with open("gh_pages/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Built index.html")
