"""Build the standalone Windows updater (update.exe) with the active Python environment."""

import os
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
            str(project_root / "update.spec"),
        ],
        cwd=str(project_root),
        check=True,
    )
    executable = dist_path / ("update.exe" if os.name == "nt" else "update")
    if not executable.is_file():
        raise FileNotFoundError(str(executable))
    print(f"Executable created: {executable}")


if __name__ == "__main__":
    main()
