"""
Build script to create standalone EXE and installer for DigitalBoxGUI application.
Requires: PyInstaller, NSIS (for installer on Windows)

Usage:
    python create_exe.py                    # Build both portable exe and installer
    python create_exe.py --portable-only    # Build only portable exe
    python create_exe.py --installer-only   # Build only installer
    python create_exe.py --skip-cleanup     # Keep temporary build files
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


class BuildConfig:
    """Build configuration for DigitalBoxGUI application."""

    APP_NAME = "DigitalBoxGUI"
    APP_VERSION = "5.4.0"

    PROJECT_ROOT = Path(__file__).resolve().parent
    BUILD_DIR = PROJECT_ROOT / "build"
    DIST_DIR = PROJECT_ROOT / "dist"
    SPEC_FILE = PROJECT_ROOT / "DigitalBoxGUI.spec"

    # Data directories to include in bundle
    DATA_DIRS = [
        ("data", "data"),
        ("QT_designer", "QT_designer"),
        ("config_file", "config_file") if (PROJECT_ROOT / "config_file").exists() else None,
    ]
    DATA_DIRS = [d for d in DATA_DIRS if d is not None]

    # Individual files to include in bundle
    DATA_FILES = [
        ("configuration.json", "."),
        ("file.ini", ".") if (PROJECT_ROOT / "file.ini").exists() else None,
        ("local_settings.json", ".") if (PROJECT_ROOT / "local_settings.json").exists() else None,
    ]
    DATA_FILES = [f for f in DATA_FILES if f is not None]

    # Hidden imports that PyInstaller might miss
    HIDDEN_IMPORTS = [
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "cv2",
        "serial",
        "paramiko",
        "openpyxl",
        "xlrd",
        "json5",
        "numpy",
        "regex",
        "voluptuous",
    ]


def create_spec_file():
    """Create PyInstaller spec file."""
    # Build datas list for directories
    datas_dirs = ",\n".join([
        f"        (r'{BuildConfig.PROJECT_ROOT / src}', r'{dest}')"
        for src, dest in BuildConfig.DATA_DIRS
    ])

    # Build datas list for individual files
    datas_files = ",\n".join([
        f"        (r'{BuildConfig.PROJECT_ROOT / src}', r'{dest}')"
        for src, dest in BuildConfig.DATA_FILES
    ])

    # Combine both lists
    if datas_dirs and datas_files:
        all_datas = datas_dirs + ",\n" + datas_files
    elif datas_dirs:
        all_datas = datas_dirs
    else:
        all_datas = datas_files

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    [r'{BuildConfig.PROJECT_ROOT / "src" / "main.py"}'],
    pathex=[r'{BuildConfig.PROJECT_ROOT}'],
    binaries=[],
    datas=[
{all_datas}
    ],
    hiddenimports={BuildConfig.HIDDEN_IMPORTS!r},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{BuildConfig.APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

    with open(BuildConfig.SPEC_FILE, 'w') as f:
        f.write(spec_content)
    print(f"✓ Created spec file: {BuildConfig.SPEC_FILE}")
    print(f"  Directories: {len(BuildConfig.DATA_DIRS)} folders")
    print(f"  Files: {len(BuildConfig.DATA_FILES)} files")


def copy_config_files():
    """Copy configuration files to dist folder."""
    files_copied = []

    for src_file, dest_dir in BuildConfig.DATA_FILES:
        src = BuildConfig.PROJECT_ROOT / src_file
        if src.exists():
            dest = BuildConfig.DIST_DIR / src_file
            shutil.copy2(src, dest)
            files_copied.append(src_file)

    if files_copied:
        print(f"\n✓ Copied configuration files:")
        for f in files_copied:
            print(f"  - {f}")
        return True
    return False


def find_oven_device_connect():
    """Find OvenDeviceConnect.exe in various locations."""
    possible_paths = [
        BuildConfig.PROJECT_ROOT.parent.parent / "OvenDeviceConnect" / "dist" / "OvenDeviceConnect.exe",
        BuildConfig.PROJECT_ROOT.parent / "OvenDeviceConnect" / "dist" / "OvenDeviceConnect.exe",
        BuildConfig.PROJECT_ROOT.parent / "OvenDeviceConnect" / "OvenDeviceConnect.exe",
        Path("C:/OvenDeviceConnect/OvenDeviceConnect.exe"),
    ]

    for path in possible_paths:
        if path.exists():
            return path
    return None


def copy_device_connect_exe():
    """Copy OvenDeviceConnect.exe to dist folder if available."""
    oven_exe = find_oven_device_connect()

    if oven_exe:
        dest = BuildConfig.DIST_DIR / "OvenDeviceConnect.exe"
        shutil.copy2(oven_exe, dest)
        size_mb = dest.stat().st_size / (1024*1024)
        print(f"✓ Copied OvenDeviceConnect.exe ({size_mb:.2f} MB)")
        print(f"  From: {oven_exe}")
        return True
    else:
        print("\n⚠ WARNING: OvenDeviceConnect.exe not found!")
        print("  The 'Connect to Device' feature will NOT work without it.")
        print("  Searched in these locations:")
        print(f"    1. {BuildConfig.PROJECT_ROOT.parent.parent / 'OvenDeviceConnect' / 'dist'}")
        print(f"    2. {BuildConfig.PROJECT_ROOT.parent / 'OvenDeviceConnect' / 'dist'}")
        print(f"    3. {BuildConfig.PROJECT_ROOT.parent / 'OvenDeviceConnect'}")
        print(f"    4. C:\\OvenDeviceConnect")
        return False


def build_portable_exe():
    """Build standalone portable EXE using PyInstaller."""
    print("\n" + "="*70)
    print("STEP 1: Building Portable EXE")
    print("="*70)

    # Create spec file
    create_spec_file()

    # Clean previous builds
    if BuildConfig.BUILD_DIR.exists():
        shutil.rmtree(BuildConfig.BUILD_DIR)
        print(f"✓ Cleaned previous build directory")

    # Run PyInstaller
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        str(BuildConfig.SPEC_FILE),
        "--distpath", str(BuildConfig.DIST_DIR),
        "--workpath", str(BuildConfig.BUILD_DIR),
    ]

    print(f"Running PyInstaller...\n")
    result = subprocess.run(cmd, cwd=BuildConfig.PROJECT_ROOT)

    if result.returncode != 0:
        print("\n✗ PyInstaller failed!")
        return False

    exe_path = BuildConfig.DIST_DIR / f"{BuildConfig.APP_NAME}.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024*1024)
        print(f"\n✓ Portable EXE created successfully!")
        print(f"  Location: {exe_path}")
        print(f"  Size: {size_mb:.2f} MB")

        # Copy configuration files
        print("\nCopying configuration files...")
        copy_config_files()

        # Copy OvenDeviceConnect if available
        print("\nLooking for OvenDeviceConnect.exe...")
        copy_device_connect_exe()

        return True
    else:
        print("✗ EXE file not found in dist directory!")
        return False


def create_nsis_installer():
    """Create NSIS installer script."""
    # Check if OvenDeviceConnect.exe exists
    oven_exe_line = ""
    oven_uninstall_line = ""
    if (BuildConfig.DIST_DIR / "OvenDeviceConnect.exe").exists():
        oven_exe_line = f'  File "{BuildConfig.DIST_DIR}\\OvenDeviceConnect.exe"'
        oven_uninstall_line = '  Delete "$INSTDIR\\OvenDeviceConnect.exe"'

    # Build config files install lines
    config_files_install = ""
    config_files_uninstall = ""
    for src_file, _ in BuildConfig.DATA_FILES:
        file_path = BuildConfig.DIST_DIR / src_file
        if file_path.exists():
            config_files_install += f'  File "{BuildConfig.DIST_DIR}\\{src_file}"\n'
            config_files_uninstall += f'  Delete "$INSTDIR\\{src_file}"\n'

    nsis_script = f'''!include "MUI2.nsh"

; No admin required - run as normal user
RequestExecutionLevel user

; App info
Name "{BuildConfig.APP_NAME} {BuildConfig.APP_VERSION}"
OutFile "{BuildConfig.DIST_DIR}\\{BuildConfig.APP_NAME}-Installer-{BuildConfig.APP_VERSION}.exe"
InstallDir "C:\\{BuildConfig.APP_NAME}"

; MUI pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; Installer section
Section "Install"
  SetOutPath "$INSTDIR"
  File "{BuildConfig.DIST_DIR}\\{BuildConfig.APP_NAME}.exe"
{oven_exe_line}
{config_files_install}
  ; Create shortcuts
  CreateDirectory "$SMPROGRAMS\\BOX_GUI"
  CreateShortcut "$SMPROGRAMS\\BOX_GUI\\BOX_GUI.lnk" "$INSTDIR\\{BuildConfig.APP_NAME}.exe" "" "$INSTDIR\\{BuildConfig.APP_NAME}.exe" 0
  CreateShortcut "$SMPROGRAMS\\BOX_GUI\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
  CreateShortcut "$DESKTOP\\BOX_GUI.lnk" "$INSTDIR\\{BuildConfig.APP_NAME}.exe" "" "$INSTDIR\\{BuildConfig.APP_NAME}.exe" 0

  ; Registry entries
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{BuildConfig.APP_NAME}" "DisplayName" "{BuildConfig.APP_NAME}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{BuildConfig.APP_NAME}" "UninstallString" "$INSTDIR\\uninstall.exe"

  WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

; Uninstaller section
Section "Uninstall"
  Delete "$INSTDIR\\{BuildConfig.APP_NAME}.exe"
{oven_uninstall_line}
{config_files_uninstall}  Delete "$INSTDIR\\uninstall.exe"
  RMDir "$INSTDIR"

  Delete "$SMPROGRAMS\\BOX_GUI\\BOX_GUI.lnk"
  Delete "$SMPROGRAMS\\BOX_GUI\\Uninstall.lnk"
  RMDir "$SMPROGRAMS\\BOX_GUI"
  Delete "$DESKTOP\\BOX_GUI.lnk"

  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{BuildConfig.APP_NAME}"
SectionEnd
'''

    nsis_file = BuildConfig.PROJECT_ROOT / f"{BuildConfig.APP_NAME}.nsi"
    with open(nsis_file, 'w') as f:
        f.write(nsis_script)

    print(f"✓ Created NSIS script: {nsis_file.name}")
    return nsis_file


def build_installer():
    """Build installer using NSIS."""
    print("\n" + "="*70)
    print("STEP 2: Building Installer with NSIS")
    print("="*70)

    # Find NSIS
    nsis_paths = [
        Path("C:\\Program Files (x86)\\NSIS\\makensis.exe"),
        Path("C:\\Program Files\\NSIS\\makensis.exe"),
    ]

    nsis_exe = None
    for path in nsis_paths:
        if path.exists():
            nsis_exe = path
            break

    if not nsis_exe:
        nsis_exe = shutil.which("makensis.exe")

    if not nsis_exe:
        print("\n⚠ NSIS not found on this system!")
        print("  To create installers, download and install NSIS:")
        print("  - Download: https://nsis.sourceforge.io/Download")
        print("  - Or via Chocolatey: choco install nsis")
        print("  - Or via Winget: winget install NSIS")
        print("\n  Skipping installer build...")
        return False

    # Create NSIS script
    nsis_file = create_nsis_installer()

    # Run NSIS
    cmd = [str(nsis_exe), "/V4", "/NOCD", str(nsis_file)]
    print(f"Running NSIS compiler...\n")
    result = subprocess.run(cmd, cwd=BuildConfig.PROJECT_ROOT)

    if result.returncode != 0:
        print("\n✗ NSIS build failed!")
        return False

    installer_path = BuildConfig.DIST_DIR / f"{BuildConfig.APP_NAME}-Installer-{BuildConfig.APP_VERSION}.exe"
    if installer_path.exists():
        size_mb = installer_path.stat().st_size / (1024*1024)
        print(f"\n✓ Installer created successfully!")
        print(f"  Location: {installer_path}")
        print(f"  Size: {size_mb:.2f} MB")
        return True
    else:
        print("✗ Installer file not found!")
        return False


def cleanup_build():
    """Clean up temporary build files."""
    print("\nCleaning up temporary files...")

    if BuildConfig.BUILD_DIR.exists():
        shutil.rmtree(BuildConfig.BUILD_DIR)
        print(f"  ✓ Removed build directory")

    spec_file = BuildConfig.SPEC_FILE
    if spec_file.exists():
        spec_file.unlink()
        print(f"  ✓ Removed spec file")

    nsi_file = BuildConfig.PROJECT_ROOT / f"{BuildConfig.APP_NAME}.nsi"
    if nsi_file.exists():
        nsi_file.unlink()
        print(f"  ✓ Removed NSIS script")


def print_summary():
    """Print build summary."""
    print("\n" + "="*70)
    print("BUILD SUMMARY")
    print("="*70)

    dist_files = sorted(BuildConfig.DIST_DIR.glob("*.exe"))
    if not dist_files:
        print("No output files found!")
        return

    print(f"\nOutput directory: {BuildConfig.DIST_DIR}\n")
    for file in dist_files:
        size_mb = file.stat().st_size / (1024*1024)
        file_type = "Installer" if "Installer" in file.name else "Portable"
        print(f"  [{file_type:12}] {file.name:<50} {size_mb:>8.2f} MB")

    print("\n" + "="*70)
    print("✓ Build completed! All files are ready in the 'dist' directory.")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Build DigitalBoxGUI as portable EXE and/or installer"
    )
    parser.add_argument(
        "--portable-only",
        action="store_true",
        help="Build only portable EXE"
    )
    parser.add_argument(
        "--installer-only",
        action="store_true",
        help="Build only installer (requires existing EXE)"
    )
    parser.add_argument(
        "--skip-cleanup",
        action="store_true",
        help="Keep temporary build files"
    )

    args = parser.parse_args()

    # Ensure dist directory exists
    BuildConfig.DIST_DIR.mkdir(exist_ok=True)

    build_portable = not args.installer_only
    build_inst = not args.portable_only

    success = True

    # Build portable EXE
    if build_portable:
        if not build_portable_exe():
            success = False
            if not args.installer_only:
                return 1

    # Build installer
    if build_inst and success:
        build_installer()

    # Cleanup
    if not args.skip_cleanup:
        cleanup_build()

    print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
