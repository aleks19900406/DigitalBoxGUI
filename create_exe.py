"""Build the standalone Windows GUI with the active Python environment."""

import shutil
import subprocess
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parent
    dist_path = project_root / "dist"
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
            "--distpath", str(dist_path),
            "--workpath", str(project_root / "build"),
            str(project_root / "BOX_GUI.spec"),
        ],
        cwd=str(project_root),
        check=True,
    )
    executable = dist_path / "BOX_GUI.exe"
    if not executable.is_file():
        raise FileNotFoundError(str(executable))
    oven_executable = project_root.parent / "OvenDeviceConnect" / "dist" / "OvenDeviceConnect.exe"
    if oven_executable.is_file():
        shutil.copy2(oven_executable, dist_path / oven_executable.name)
    else:
        print("WARNING: place OvenDeviceConnect.exe beside BOX_GUI.exe to enable ConnectToDevice.")
    print(f"Executable created: {executable}")


if __name__ == "__main__":
    main()