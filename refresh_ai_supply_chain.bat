@echo off
cd /d "C:\Users\ABS Computer\Python\trading_bot_dev\gh_pages"
"C:\Users\ABS Computer\AppData\Local\Python\bin\python.exe" gen_ai_supply_chain.py
cd /d "C:\Users\ABS Computer\Python\trading_bot_dev\gh_pages"
git add ai_supply_chain.html
git commit -m "Auto-refresh AI Supply Chain data"
git push origin main
