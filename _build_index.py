import json
data_js = """[
  {ticker:"BWET",stock:69,indiv:69,wr100:8,pnl10:68,avgPnl:46.66,ptpnl:5.31,report:"BWET_backtest_summary.html"}
  {ticker:"MP",stock:489,indiv:489,wr100:48,pnl10:482,avgPnl:45.55,ptpnl:2.88,report:"MP_backtest_summary.html"}
  {ticker:"ASTS",stock:307,indiv:307,wr100:50,pnl10:292,avgPnl:42.7,ptpnl:3.38,report:"ASTS_backtest_summary.html"}
  {ticker:"SMCI",stock:509,indiv:509,wr100:32,pnl10:499,avgPnl:40.2,ptpnl:2.56,report:"SMCI_backtest_summary.html"}
  {ticker:"TSAT",stock:319,indiv:319,wr100:80,pnl10:308,avgPnl:38.9,ptpnl:4.52,report:"TSAT_backtest_summary.html"}
  {ticker:"GLW",stock:360,indiv:360,wr100:63,pnl10:338,avgPnl:37.58,ptpnl:3.34,report:"GLW_backtest_summary.html"}
  {ticker:"HAL",stock:374,indiv:374,wr100:66,pnl10:368,avgPnl:36.71,ptpnl:3.48,report:"HAL_backtest_summary.html"}
  {ticker:"CLSK",stock:265,indiv:265,wr100:80,pnl10:234,avgPnl:34.25,ptpnl:3.04,report:"CLSK_backtest_summary.html"}
  {ticker:"DAL",stock:383,indiv:383,wr100:23,pnl10:370,avgPnl:34.16,ptpnl:2.19,report:"DAL_backtest_summary.html"}
  {ticker:"BKR",stock:341,indiv:341,wr100:48,pnl10:327,avgPnl:33.36,ptpnl:3.04,report:"BKR_backtest_summary.html"}
  {ticker:"LLY",stock:356,indiv:356,wr100:95,pnl10:327,avgPnl:33.33,ptpnl:3.63,report:"LLY_backtest_summary.html"}
  {ticker:"SLB",stock:302,indiv:302,wr100:46,pnl10:301,avgPnl:33.2,ptpnl:3.27,report:"SLB_backtest_summary.html"}
  {ticker:"USO",stock:451,indiv:451,wr100:62,pnl10:437,avgPnl:31.31,ptpnl:2.67,report:"USO_backtest_summary.html"}
  {ticker:"CNBS",stock:174,indiv:174,wr100:44,pnl10:152,avgPnl:29.99,ptpnl:3.22,report:"CNBS_backtest_summary.html"}
  {ticker:"CRWG",stock:208,indiv:208,wr100:33,pnl10:194,avgPnl:29.62,ptpnl:5.45,report:"CRWG_backtest_summary.html"}
  {ticker:"USAR",stock:255,indiv:255,wr100:58,pnl10:226,avgPnl:28.05,ptpnl:4.04,report:"USAR_backtest_summary.html"}
  {ticker:"DLTR",stock:147,indiv:147,wr100:38,pnl10:127,avgPnl:24.67,ptpnl:2.69,report:"DLTR_backtest_summary.html"}
  {ticker:"HUM",stock:394,indiv:394,wr100:99,pnl10:344,avgPnl:23.6,ptpnl:2.92,report:"HUM_backtest_summary.html"}
  {ticker:"CI",stock:329,indiv:329,wr100:101,pnl10:303,avgPnl:23.56,ptpnl:3.49,report:"CI_backtest_summary.html"}
  {ticker:"ITA",stock:234,indiv:234,wr100:55,pnl10:203,avgPnl:22.05,ptpnl:2.96,report:"ITA_backtest_summary.html"}
  {ticker:"UNH",stock:225,indiv:225,wr100:27,pnl10:204,avgPnl:21.66,ptpnl:1.58,report:"UNH_backtest_summary.html"}
  {ticker:"ELV",stock:461,indiv:461,wr100:135,pnl10:391,avgPnl:21.4,ptpnl:2.22,report:"ELV_backtest_summary.html"}
  {ticker:"ORCL",stock:261,indiv:261,wr100:69,pnl10:233,avgPnl:20.99,ptpnl:3.2,report:"ORCL_backtest_summary.html"}
  {ticker:"LMT",stock:386,indiv:386,wr100:134,pnl10:326,avgPnl:20.86,ptpnl:3.48,report:"LMT_backtest_summary.html"}
  {ticker:"LNG",stock:206,indiv:206,wr100:70,pnl10:181,avgPnl:20.41,ptpnl:3.79,report:"LNG_backtest_summary.html"}
  {ticker:"PFE",stock:120,indiv:120,wr100:67,pnl10:102,avgPnl:20.1,ptpnl:4.04,report:"PFE_backtest_summary.html"}
  {ticker:"F",stock:111,indiv:111,wr100:34,pnl10:98,avgPnl:19.12,ptpnl:3.43,report:"F_backtest_summary.html"}
  {ticker:"MSFT",stock:113,indiv:113,wr100:48,pnl10:84,avgPnl:17.1,ptpnl:2.61,report:"MSFT_backtest_summary.html"}
  {ticker:"AMZN",stock:199,indiv:199,wr100:79,pnl10:159,avgPnl:16.57,ptpnl:2.39,report:"AMZN_backtest_summary.html"}
  {ticker:"NKE",stock:184,indiv:184,wr100:69,pnl10:137,avgPnl:15.7,ptpnl:2.11,report:"NKE_backtest_summary.html"}
  {ticker:"MKC",stock:228,indiv:228,wr100:76,pnl10:182,avgPnl:14.65,ptpnl:1.86,report:"MKC_backtest_summary.html"}
  {ticker:"CVNA",stock:96,indiv:96,wr100:36,pnl10:0,avgPnl:3.14,ptpnl:0.49,report:"CVNA_backtest_summary.html"}
  {ticker:"APLD",stock:588,indiv:588,wr100:44,pnl10:10,avgPnl:2.98,ptpnl:2.98,report:"APLD_backtest_summary.html"}
  {ticker:"ASML",stock:63,indiv:63,wr100:21,pnl10:0,avgPnl:2.1,ptpnl:0.31,report:"ASML_backtest_summary.html"}
]"""

summary = "34 tickers &#8226; 9,579 rules &#8226; 26.5%% avg PnL"

with open("gh_pages/index_template.html", "r", encoding="utf-8") as tf:
    tmpl = tf.read()

html = tmpl.replace("{{DATA}}", data_js).replace("{{SUMMARY}}", summary)

with open("gh_pages/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Built index.html")
