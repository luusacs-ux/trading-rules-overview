@echo off
setlocal
set LOGFILE=C:\Users\ABS Computer\Python\trading_bot_dev\logs\ticker_rankings_refresh.log
set ROOT=C:\Users\ABS Computer\Python\trading_bot_dev
set GHDIR=C:\Users\ABS Computer\Python\trading_bot_dev\gh_pages
set PY="C:\Users\ABS Computer\AppData\Local\Python\bin\python.exe"

echo [%date% %time%] Starting ticker rankings refresh >> "%LOGFILE%"

rem 1. Recompute the ranking CSV (uses cached fundamentals; refetches only stale)
cd /d "%ROOT%"
%PY% probability_engine.py >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] ABORTED: probability_engine.py failed with exit code %ERRORLEVEL% >> "%LOGFILE%"
    exit /b 1
)

rem 2. Rebuild the gh-pages HTML from the fresh CSV
cd /d "%GHDIR%"
%PY% gen_ticker_rankings.py >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] ABORTED: gen_ticker_rankings.py failed with exit code %ERRORLEVEL% >> "%LOGFILE%"
    exit /b 1
)

rem 3. Publish
if exist ".git\rebase-merge" git rebase --abort >> "%LOGFILE%" 2>&1
git pull --rebase origin main >> "%LOGFILE%" 2>&1 || git rebase --abort >> "%LOGFILE%" 2>&1
git add ticker_rankings.html >> "%LOGFILE%" 2>&1
git commit -m "Auto-refresh ticker rankings [%date%]" >> "%LOGFILE%" 2>&1
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
