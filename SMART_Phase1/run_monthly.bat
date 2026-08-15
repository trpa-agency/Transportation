@echo off
REM ---------------------------------------------------------------------------
REM SMART Phase 1 ETL -- monthly scheduled run.
REM
REM Windows Task Scheduler setup:
REM   Program/script:    C:\...\SMART_Phase1\run_monthly.bat
REM   Start in:          C:\...\SMART_Phase1
REM   Run whether user is logged on or not; "Run with highest privileges" is
REM   NOT required.
REM
REM The machine must be able to reach BOTH api-external.cloud.derq.com and
REM maps.trpa.org, and needs a .env alongside this file (see .env.template).
REM
REM Exits non-zero on failure so Task Scheduler reports "Last Run Result"
REM correctly instead of always showing 0x0.
REM ---------------------------------------------------------------------------

setlocal

REM Point this at the env that has requests/pandas/python-dotenv/pyyaml.
REM Do NOT pip install into the ArcGIS Pro base env -- clone it first.
set PYTHON=%LOCALAPPDATA%\ESRI\conda\envs\arcgispro-py3-clone\python.exe

if not exist "%PYTHON%" (
    echo ERROR: Python not found at %PYTHON%
    echo Edit run_monthly.bat and set PYTHON to your environment's python.exe.
    exit /b 1
)

cd /d "%~dp0"

if not exist ".env" (
    echo ERROR: .env not found in %CD%. Copy .env.template and fill it in.
    exit /b 1
)

echo Starting SMART ETL at %DATE% %TIME%
"%PYTHON%" scripts\run_etl.py --live
set RESULT=%ERRORLEVEL%

echo Finished at %DATE% %TIME% with exit code %RESULT%
exit /b %RESULT%
