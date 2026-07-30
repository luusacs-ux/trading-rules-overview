@echo off
setlocal
set LOGFILE=C:\Users\ABS Computer\Python\trading_bot_dev\logs\events_calendar_refresh.log
set ROOT=C:\Users\ABS Computer\Python\trading_bot_dev
set GHDIR=C:\Users\ABS Computer\Python\trading_bot_dev\gh_pages
set PY="C:\Users\ABS Computer\AppData\Local\Python\bin\python.exe"

echo [%date% %time%] Starting event calendar refresh >> "%LOGFILE%"

rem The two JSON caches are refreshed by their own earlier tasks:
rem   RefreshUpcomingEvents (05:00) -> upcoming_events.json
rem   MacroEventsDigest     (06:00) -> macro_events.json
rem This task runs after both and only rebuilds the pages, so it stays fast.
rem Macro cache is cheap, so re-refresh it here as a safety net if that task was skipped.
cd /d "%ROOT%"
%PY% -c "import macro_events as M; M.refresh_cache()" >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% NEQ 0 echo [%date% %time%] WARNING: macro cache refresh failed, using last good cache >> "%LOGFILE%"

cd /d "%GHDIR%"
%PY% gen_events_calendar.py >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] ABORTED: gen_events_calendar.py failed with exit code %ERRORLEVEL% >> "%LOGFILE%"
    exit /b 1
)

%PY% gen_hub.py >> "%LOGFILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] ABORTED: gen_hub.py failed with exit code %ERRORLEVEL% >> "%LOGFILE%"
    exit /b 1
)

rem Publish
if exist ".git\rebase-merge" git rebase --abort >> "%LOGFILE%" 2>&1
git pull --rebase origin main >> "%LOGFILE%" 2>&1 || git rebase --abort >> "%LOGFILE%" 2>&1
git add events_calendar.html hub.html >> "%LOGFILE%" 2>&1
git commit -m "Auto-refresh event calendar + hub [%date%]" >> "%LOGFILE%" 2>&1
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
