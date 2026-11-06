"""Application startup and shared window ownership."""

import os
import shutil
import sys
import tempfile
from PyQt6.QtCore import QCoreApplication, QLockFile, Qt
from PyQt6.QtWidgets import QApplication
from . import state
from .paths import APPLICATION_ROOT, PROJECT_ROOT
from .splash import SplashScreen
from .styles import apply_theme, saved_theme


def close_bootloader_splash():
    """Close the static PyInstaller splash (shown while the exe unpacks) once the animated splash is visible."""
    try:
        import pyi_splash
    except ImportError:
        return
    pyi_splash.close()


_instance_lock = None


def acquire_single_instance():
    """False when another Digital Box is already running (e.g. a desktop icon launched several times by one click)."""
    global _instance_lock
    lock = QLockFile(os.path.join(tempfile.gettempdir(), "digital_box_gui.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        return False
    _instance_lock = lock
    return True


def copy_application_resources():
    if getattr(sys, "frozen", False):
        for name in ("data",):
            source_root = PROJECT_ROOT / name
            destination_root = APPLICATION_ROOT / name
            destination_root.mkdir(parents=True, exist_ok=True)
            for source in source_root.rglob("*"):
                destination = destination_root / source.relative_to(source_root)
                if source.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                elif not destination.exists():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
        for name in ("saveData", "autoTest", "groups", "digitalPotTable", "dacTable", "boxMarks"):
            (APPLICATION_ROOT / "data" / name).mkdir(parents=True, exist_ok=True)
        ini_file = PROJECT_ROOT / "file.ini"
        if ini_file.is_file() and not (APPLICATION_ROOT / ini_file.name).exists():
            shutil.copy2(ini_file, APPLICATION_ROOT / ini_file.name)
        return
    source_folder = ['QT_designer','config_file','data']
    for copyFile in source_folder:
        try:    
            destination_folder = os.path.join("..", "gui_application", copyFile)  # Adjust the source folder path
            # Copy the entire folder to the destination
            if os.path.exists(destination_folder):
                shutil.rmtree(destination_folder)
            shutil.copytree(copyFile, destination_folder)
        except Exception as e:
            print(f"An error occurred: {e}")
            # Handle the exception here, or just continue
            break  # 'pass' will continue execution without stopping the program


def launch():
    os.chdir(PROJECT_ROOT)
    app = QApplication(sys.argv)
    if not acquire_single_instance():
        close_bootloader_splash()
        return 0
    app.setStyle("Fusion")
    font = app.font()
    font.setFamily("Segoe UI")
    app.setFont(font)
    apply_theme(saved_theme())
    splash = SplashScreen(12) if QCoreApplication.instance() is not None else None
    close_bootloader_splash()

    def loading(message):
        if splash is not None:
            splash.advance(message)

    loading("Preparing files...")
    copy_application_resources()
    if getattr(sys, "frozen", False):
        os.chdir(APPLICATION_ROOT)

    ### CREATE AN OBJECT NAMES ###
    # windows are imported here (not at module level) so the splash is visible while the heavy modules load
    loading("Loading main window...")
    from .ui import MainWindow
    state.mainWindow = MainWindow()
    loading("Loading automation...")
    from .automation import CreateAutoTest, AutoRunScript
    state.autoTest = AutoRunScript()
    #state.autoTest.show()
    loading("Loading HUSA set model...")
    from .setup_windows import HusaSetModule, Bio21PyroSetSystem
    state.HusaModelWindow = HusaSetModule()
    loading("Loading BIO21 pyro set system...")
    state.PyroSetSystem = Bio21PyroSetSystem()
    loading("Loading DAC values...")
    from .tables import SetDacPot, CreatePotTable, CreateDacTable
    state.SetDacValue = SetDacPot()
    loading("Loading pot table...")
    state.PotTableSet = CreatePotTable()
    loading("Loading DAC table...")
    state.DacTableCreate = CreateDacTable()
    loading("Loading auto test...")
    state.RunAutoTest = CreateAutoTest()
    #state.RunAutoTest.show()
    loading("Loading BIO21 premium...")
    from .g800 import DeviceG800
    state.deviceG800 = DeviceG800()
    loading("Loading BIO24...")
    from .bio24 import DeviceBio24
    state.deviceBio24 = DeviceBio24()
    #state.deviceG800.show()
    loading("Opening digital box...")
    if sys.platform.startswith("linux"):
        state.mainWindow.setWindowState(Qt.WindowState.WindowMaximized)  # always over the whole screen
    state.mainWindow.show()
    if splash is not None:
        splash.close_animated()
    ##############################
    return app.exec()

