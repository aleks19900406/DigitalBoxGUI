"""Project resource locations."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
APPLICATION_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else PROJECT_ROOT
EXECUTABLE_SUFFIX = ".exe" if os.name == "nt" else ""
# web page of a digital box (RPi) where its services (e.g. das_service) can be restarted after an error
SERVICES_DEFAULT_IP = "192.168.88.12"
SERVICES_PORT = 9001
OVEN_DEVICE_CONNECT_PATHS = (
	APPLICATION_ROOT / f"OvenDeviceConnect{EXECUTABLE_SUFFIX}",
	APPLICATION_ROOT.parent / "OvenDeviceConnect" / "dist" / f"OvenDeviceConnect{EXECUTABLE_SUFFIX}",
)


def update_command():
    """Command that starts the updater: the packaged update program, or update.py when running from source."""
    packaged = APPLICATION_ROOT / f"update{EXECUTABLE_SUFFIX}"
    if packaged.is_file():
        return [str(packaged)]
    return [sys.executable, str(APPLICATION_ROOT / "update.py")]

QT_DESIGNER = PROJECT_ROOT / "QT_designer"

BOX_MARKS_PATH = os.path.join("data","boxMarks")

BOX_DIGITAL_POT_PATH = os.path.join("data","digitalPotTable")

BOX_DIGITAL_DAC_PATH = os.path.join("data","dacTable")

IMAGES_PATH = os.path.join("data","images","system")

IMAGE_PATH_OTHER =os.path.join("data","images","other")

DATA_SAVE = os.path.join("data","saveData")

AUTO_TEST_PATH = os.path.join("data","autoTest")
