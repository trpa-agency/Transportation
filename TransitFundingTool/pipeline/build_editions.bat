@echo off
rem Build the public and full editions of the funding model from model\transit-funding-model.html.
rem Run build_data.bat and copy dist\transit-funding-model.html to ..\model\ first.
setlocal
cd /d "%~dp0"
set "PROPY=propy"
where propy >nul 2>nul || set "PROPY=%ProgramFiles%\ArcGIS\Pro\bin\Python\scripts\propy.bat"
call "%PROPY%" editions\build_editions.py %*
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (echo Editions written to editions\dist\.) else (echo Build stopped with code %RC%. See the message above.)
pause
exit /b %RC%
