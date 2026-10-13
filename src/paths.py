"""Project resource locations."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
APPLICATION_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else PROJECT_ROOT
OVEN_DEVICE_CONNECT_PATHS = (
	APPLICATION_ROOT / "OvenDeviceConnect.exe",
	APPLICATION_ROOT.parent / "OvenDeviceConnect" / "dist" / "OvenDeviceConnect.exe",
)

QT_DESIGNER = PROJECT_ROOT / "QT_designer"

BOX_MARKS_PATH = os.path.join("data","boxMarks")

BOX_DIGITAL_POT_PATH = os.path.join("data","digitalPotTable")

BOX_DIGITAL_DAC_PATH = os.path.join("data","dacTable")

IMAGES_PATH = os.path.join("data","images","system")

IMAGE_PATH_OTHER =os.path.join("data","images","other")

DATA_SAVE = os.path.join("data","saveData")

AUTO_TEST_PATH = os.path.join("data","autoTest")
