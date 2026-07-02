@echo off
setlocal
set LOGFILE=C:\Users\ABS Computer\Python\trading_bot_dev\logs\ai_supply_chain_refresh.log
set GHDIR=C:\Users\ABS Computer\Python\trading_bot_dev\gh_pages

echo [%date% %time%] Starting AI Supply Chain refresh >> "%LOGFILE%"

cd /d "%GHDIR%"

"C:\Users\ABS Computer\AppData\Local\Python\bin\python.exe" gen_ai_supply_chain.py >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] ABORTED: Python script failed with exit code %ERRORLEVEL% >> "%LOGFILE%"
    exit /b 1
)

if exist ".git\rebase-merge" git rebase --abort >> "%LOGFILE%" 2>&1
git pull --rebase origin main >> "%LOGFILE%" 2>&1 || git rebase --abort >> "%LOGFILE%" 2>&1
git add ai_supply_chain.html ai_supply_chain_meta.json >> "%LOGFILE%" 2>&1
git commit -m "Auto-refresh AI Supply Chain data [%date%]" >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] No changes to commit >> "%LOGFILE%"
    exit /b 0
)

git push origin main >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] WARNING: git push failed, will retry next cycle >> "%LOGFILE%"
    exit /b 1
)

echo [%date% %time%] Refresh complete >> "%LOGFILE%"
