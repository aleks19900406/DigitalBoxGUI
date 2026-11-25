#!/usr/bin/env python
"""
Automatic version bump and update script
Usage: python auto_update.py          (auto bump)
       python auto_update.py 5.2.0    (specific version)
"""

import re
import subprocess
import sys
from pathlib import Path

def read_current_version():
    """Read current version from create_exe.py"""
    create_exe = Path("create_exe.py")
    with open(create_exe) as f:
        content = f.read()

    match = re.search(r'APP_VERSION = "([0-9.]+)"', content)
    if match:
        return match.group(1)
    return None

def bump_version(version):
    """Bump minor version: 5.2.0 -> 5.3.0"""
    parts = version.split('.')
    major = int(parts[0])
    minor = int(parts[1])
    minor += 1
    return f"{major}.{minor}.0"

def get_v_prefix(version):
    """Extract V prefix from version: 5.2.0 -> V5.2"""
    parts = version.split('.')
    return f"V{parts[0]}.{parts[1]}"

def update_version_in_file(filepath, pattern, replacement):
    """Update version in a file"""
    with open(filepath) as f:
        content = f.read()

    new_content = re.sub(pattern, replacement, content)

    with open(filepath, 'w') as f:
        f.write(new_content)

def main():
    if len(sys.argv) > 1:
        version = sys.argv[1]
        print(f"Using specified version: {version}")
    else:
        current = read_current_version()
        if not current:
            print("ERROR: Could not read current version from create_exe.py")
            return 1

        version = bump_version(current)
        print(f"Current version: {current}")
        print(f"New version: {version} (auto bumped)")

    v_prefix = get_v_prefix(version)

    print()
    print("=" * 60)
    print(f"Full Update to version {version}")
    print("=" * 60)
    print()
    print("Updating version files...")

    # Update src/state.py
    update_version_in_file(
        "src/state.py",
        r"DIGITAL_BOX_VERSION = 'V[^']*'",
        f"DIGITAL_BOX_VERSION = '{v_prefix}'"
    )
    print(f"  ✓ Updated src/state.py to {v_prefix}")

    # Update create_exe.py
    update_version_in_file(
        "create_exe.py",
        r'APP_VERSION = "[^"]*"',
        f'APP_VERSION = "{version}"'
    )
    print(f"  ✓ Updated create_exe.py to {version}")

    # Update src/ui.py
    update_version_in_file(
        "src/ui.py",
        r'current_version="[^"]*"',
        f'current_version="{version}"'
    )
    print(f"  ✓ Updated src/ui.py to {version}")

    # Update src/simple_update.py
    update_version_in_file(
        "src/simple_update.py",
        r'current_version: str = "[^"]*"',
        f'current_version: str = "{version}"'
    )
    print(f"  ✓ Updated src/simple_update.py to {version}")

    print()
    print("=" * 60)
    print("Building application")
    print("=" * 60)
    print()

    result = subprocess.run([sys.executable, "create_exe.py"])
    if result.returncode != 0:
        print("\n✗ Build failed!")
        return 1

    print()
    print("=" * 60)
    print("Git operations")
    print("=" * 60)
    print()

    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", f"v{version} - Release"])
    subprocess.run(["git", "tag", "-a", f"v{version}", "-m", f"Version {version}"])

    print()
    print("Pushing to GitHub...")
    result = subprocess.run(["git", "push", "origin", "main"])
    if result.returncode != 0:
        print("\n✗ Push failed!")
        return 1

    subprocess.run(["git", "push", "origin", f"v{version}"])

    print()
    print("=" * 60)
    print("Upload to GitHub Releases")
    print("=" * 60)
    print()
    print("Next steps:")
    print(f"1. Go to: https://github.com/aleks19900406/DigitalBoxGUI/releases")
    print(f"2. Click on v{version}")
    print(f"3. Upload file: dist/DigitalBoxGUI-Installer-{version}.exe")
    print("4. Publish!")
    print()
    print(f"✓ New update AVAILABLE: v{version}")
    print("✓ Users will see: 'Update available!' when they click Update button")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
