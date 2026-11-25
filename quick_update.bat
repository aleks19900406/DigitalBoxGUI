@echo off
REM Quick update and push to GitHub
REM Usage: .\quick_update.bat 5.2.0

setlocal enabledelayedexpansion

if "%1"=="" (
    set /p version="Enter version (e.g., 5.2.0): "
) else (
    set version=%1
)

echo.
echo ============================================================
echo Updating to version %version%
echo ============================================================
echo.

REM Extract major.minor version for V-prefix
for /f "tokens=1,2 delims=." %%a in ("%version%") do (
    set v_prefix=V%%a.%%b
)

echo Updating version files...

REM Update src/state.py
powershell -Command "(Get-Content 'src\state.py') -replace \"DIGITAL_BOX_VERSION = 'V.*'\", \"DIGITAL_BOX_VERSION = '%v_prefix%'\" | Set-Content 'src\state.py'"
echo  ✓ Updated src/state.py to %v_prefix%

REM Update create_exe.py
powershell -Command "(Get-Content 'create_exe.py') -replace 'APP_VERSION = \".*\"', 'APP_VERSION = \"%version%\"' | Set-Content 'create_exe.py'"
echo  ✓ Updated create_exe.py to %version%

REM Update src/ui.py
powershell -Command "(Get-Content 'src\ui.py') -replace 'current_version=\".*\"', 'current_version=\"%version%\"' | Set-Content 'src\ui.py'"
echo  ✓ Updated src/ui.py to %version%

REM Update src/simple_update.py
powershell -Command "(Get-Content 'src\simple_update.py') -replace 'current_version: str = \".*\"', 'current_version: str = \"%version%\"' | Set-Content 'src\simple_update.py'"
echo  ✓ Updated src/simple_update.py to %version%

echo.
echo ============================================================
echo Git operations
echo ============================================================
echo.

git add .
git commit -m "v%version% - Update"
git tag -a v%version% -m "Version %version%"

echo.
echo Pushing to GitHub...
git push origin main
git push origin v%version%

if errorlevel 1 (
    echo.
    echo ✗ Push failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Upload to GitHub Releases
echo ============================================================
echo.
echo Next steps:
echo 1. Go to: https://github.com/aleks19900406/DigitalBoxGUI/releases
echo 2. Click on v%version%
echo 3. Upload file: dist\DigitalBoxGUI-Installer-%version%.exe
echo 4. Publish!
echo.
pause
