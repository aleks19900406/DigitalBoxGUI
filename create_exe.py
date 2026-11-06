"""Build the standalone GUI (BOX_GUI.exe on Windows, BOX_GUI on Linux) with the active Python environment."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

SUFFIX = ".exe" if os.name == "nt" else ""


def main():
    project_root = Path(__file__).resolve().parent
    dist_path = project_root / "dist"
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller", "--noconfirm",
            "--distpath", str(dist_path),
            "--workpath", str(project_root / "build"),
            str(project_root / "BOX_GUI.spec"),
        ],
        cwd=str(project_root),
        check=True,
    )
    executable = dist_path / f"BOX_GUI{SUFFIX}"
    if not executable.is_file():
        raise FileNotFoundError(str(executable))
    oven_executable = project_root.parent / "OvenDeviceConnect" / "dist" / f"OvenDeviceConnect{SUFFIX}"
    if oven_executable.is_file():
        shutil.copy2(oven_executable, dist_path / oven_executable.name)
    else:
        print(f"WARNING: place OvenDeviceConnect{SUFFIX} beside BOX_GUI{SUFFIX} to enable ConnectToDevice.")
    print(f"Executable created: {executable}")


if __name__ == "__main__":
    main()