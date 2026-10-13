"""Application startup and shared window ownership."""

import os
import shutil
import sys
from PyQt5.QtWidgets import QApplication
from . import state
from .paths import APPLICATION_ROOT, PROJECT_ROOT
from .ui import MainWindow
from .tables import SetDacPot, CreatePotTable, CreateDacTable
from .setup_windows import HusaSetModule, Bio21PyroSetSystem
from .automation import CreateAutoTest, AutoRunScript
from .g800 import DeviceG800
from .bio24 import DeviceBio24


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
    source_folder = ['copyFile','QT_designer','config_file','data']
    for copyFile in source_folder:
        try:    
            destination_folder = fr"..\gui_application\{copyFile}"  # Adjust the source folder path
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
    copy_application_resources()
    if getattr(sys, "frozen", False):
        os.chdir(APPLICATION_ROOT)
    app = QApplication(sys.argv)
    ### CREATE AN OBJECT NAMES ###
    state.mainWindow = MainWindow()
    state.mainWindow.show()
    state.autoTest = AutoRunScript()
    #state.autoTest.show()
    state.HusaModelWindow = HusaSetModule()
    state.PyroSetSystem = Bio21PyroSetSystem()
    state.SetDacValue = SetDacPot()
    state.PotTableSet = CreatePotTable()
    state.DacTableCreate = CreateDacTable()
    state.RunAutoTest = CreateAutoTest()
    #state.RunAutoTest.show()
    state.deviceG800 = DeviceG800()
    state.deviceBio24 = DeviceBio24()
    #state.deviceG800.show()
    ##############################
    return app.exec_()

