@echo off
setlocal

REM Launcher for Yandex Panorama Downloader on Windows
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python -m yandex_panorama.cli %*
    exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -m yandex_panorama.cli %*
    exit /b %ERRORLEVEL%
)

echo [ERROR] Python не найден в переменной PATH.
echo Установите Python с https://www.python.org/ и отметьте галочку "Add Python to PATH".
exit /b 1
