@echo off
REM Complete update with automatic version bump
REM Usage: .\full_update.bat          (auto bump version)
REM        .\full_update.bat 5.2.0   (specific version)

setlocal enabledelayedexpansion

if "%1"=="" (
    echo Reading current version...

    REM Preberi trenutno verzijo iz create_exe.py
    for /f "tokens=2 delims==" %%a in ('findstr "APP_VERSION" create_exe.py') do (
        set current=%%a
        set current=!current:"=!
        set current=!current: =!
    )

    echo Current version: !current!

    REM Dvigni verzijo (5.2.0 -> 5.3.0)
    for /f "tokens=1,2,3 delims=." %%a in ("!current!") do (
        set major=%%a
        set minor=%%b
        set patch=%%c
        set /a minor=!minor!+1
        set version=!major!.!minor!.0
    )

    echo New version: !version! (auto bumped)
) else (
    set version=%1
    echo Using specified version: !version!
)

echo.
echo ============================================================
echo Full Update to version %version%
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
echo Building application
echo ============================================================
echo.

python create_exe.py

if errorlevel 1 (
    echo.
    echo ✗ Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Git operations
echo ============================================================
echo.

git add .
git commit -m "v%version% - Release"
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
echo New update AVAILABLE: v%version%
echo Users will see: "Update available!" when they click Update button
echo.
pause
