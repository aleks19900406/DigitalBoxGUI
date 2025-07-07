import subprocess
import os
import shutil
from pathlib import Path

# === Base path ===
home = Path.home()
documents = home / "Documents" / "Automatic_test_UI" / "DigitalBoxGUI"

# === Paths ===
script_location = documents / "gui_project" / "BOX_GUI.py"
icon_path = documents / "gui_application" / "data" / "images" / "other" / "blackBox.ico"
dist_path = documents / "gui_application"

# Folders to bundle (relative to GUI_Project)
project_path = documents / "GUI_Project"
additional_paths = [
    ("DigitalBox", project_path / "DigitalBox"),
    ("package", project_path / "package"),
    ("config_file", project_path / "config_file"),
    ("data", project_path / "data"),
    ("QT_designer", project_path / "QT_designer"),
    ("config_file", project_path / "config_file"),  # included again just in case
]

# === Convert to PyInstaller --add-data format ===
add_data_args = []
for name, full_path in additional_paths:
    add_data_args.append(f"--add-data={full_path};{name}")

# === PyInstaller Command ===
cmd = [
    "pyinstaller",
    "--noconfirm",
    "--onefile",
    "--windowed",
    f"--icon={icon_path}",
    f"--distpath={dist_path}",
    *add_data_args,
    str(script_location)
]

# === Run the command ===
print("Running PyInstaller...\n")
subprocess.run(cmd)

# === Clean up build and spec ===
try:
    shutil.rmtree("build")
    os.remove("BOX_GUI.spec")
except Exception:
    pass

print(f"\n✅ Executable created in: {dist_path}")