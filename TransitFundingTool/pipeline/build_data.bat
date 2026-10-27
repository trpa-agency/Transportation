@echo off
rem Build the transit funding model data and page with ArcGIS Pro Python.
rem Usage: double-click, or run "build_data.bat --strict" or "build_data.bat --check".
setlocal
cd /d "%~dp0"
set "PROPY=propy"
where propy >nul 2>nul || set "PROPY=%ProgramFiles%\ArcGIS\Pro\bin\Python\scripts\propy.bat"
call "%PROPY%" etl\build_model_data.py %*
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (echo Build finished. Read data\build-report.md, then copy dist\transit-funding-model.html to ..\model\.) else (echo Build stopped with code %RC%. See the messages above and data\build-report.md.)
pause
exit /b %RC%
