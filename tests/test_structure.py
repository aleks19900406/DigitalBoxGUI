"""Regression checks for the modular GUI, without device connections."""

import ast
import importlib
import io
import os
import re
import runpy
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, call, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src import launcher, paths, state, styles
from src.analog_controls import AnalogControlsMixin
from src.automation import AutoRunScript
from src.bio24 import DeviceBio24
from src.connections import ConnectionMixin
from src.digital_controls import DigitalControlsMixin
from src.paths import AUTO_TEST_PATH, PROJECT_ROOT
from src.saving import SavingMixin
from src.setup_windows import Bio21PyroSetSystem, HusaSetModule
from src.styles import ButtonStyleOff2, ButtonStyleOn2
from src.ui import MainWindow


class ProjectStructureTests(unittest.TestCase):
    def test_qt_forms_resolve_inside_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            bundled = Path(directory).resolve() / "bundled"
            installed = Path(directory).resolve() / "installed"
            with patch.object(sys, "frozen", True, create=True), patch.object(sys, "_MEIPASS", str(bundled), create=True), patch.object(sys, "executable", str(installed / "BOX_GUI.exe")):
                resolved = runpy.run_path(str(PROJECT_ROOT / "src" / "paths.py"))
            self.assertEqual(resolved["QT_DESIGNER"], bundled / "QT_designer")
            self.assertEqual(resolved["APPLICATION_ROOT"], installed)

    def test_connection_config_import_from_unrelated_directory(self):
        code = (
            "import sys; sys.path.insert(0, " + repr(str(PROJECT_ROOT)) + "); "
            "from DigitalBox.Connection import data; assert data; print('PASS')"
        )
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-c", code], cwd=directory,
                capture_output=True, text=True, check=True,
            )
        self.assertIn("PASS", result.stdout)

    def test_connection_config_reads_bundle_and_ignores_external_file(self):
        connection_path = PROJECT_ROOT / "DigitalBox" / "Connection.py"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            (bundle / "config_file").mkdir(parents=True)
            (bundle / "config_file" / "G800_configs.json").write_text('{"source": "bundled"}', encoding="utf-8")
            with patch.object(sys, "frozen", True, create=True), patch.object(sys, "_MEIPASS", str(bundle), create=True), patch.object(sys, "executable", str(root / "BOX_GUI.exe")):
                bundled = runpy.run_path(str(connection_path))
                self.assertEqual(bundled["data"], {"source": "bundled"})
                (root / "config_file").mkdir()
                (root / "config_file" / "G800_configs.json").write_text('{"source": "external"}', encoding="utf-8")
                external = runpy.run_path(str(connection_path))
                self.assertEqual(external["data"], {"source": "bundled"})

    def test_frozen_resources_preserve_existing_data_and_create_empty_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            bundled = Path(directory) / "bundled"
            installed = Path(directory) / "installed"
            (bundled / "data" / "saveData").mkdir(parents=True)
            (bundled / "config_file").mkdir()
            (bundled / "QT_designer").mkdir()
            (bundled / "config_file" / "settings.json").write_text("bundled", encoding="utf-8")
            (bundled / "QT_designer" / "Main_screen.ui").write_text("ui", encoding="utf-8")
            (bundled / "file.ini").write_text("default", encoding="utf-8")
            (installed / "config_file").mkdir(parents=True)
            existing = installed / "config_file" / "settings.json"
            existing.write_text("user settings", encoding="utf-8")
            with patch.multiple(launcher, PROJECT_ROOT=bundled, APPLICATION_ROOT=installed), patch.object(launcher.sys, "frozen", True, create=True):
                launcher.copy_application_resources()
                launcher.copy_application_resources()
            self.assertEqual(existing.read_text(encoding="utf-8"), "user settings")
            self.assertFalse((installed / "QT_designer").exists())
            self.assertEqual((bundled / "QT_designer" / "Main_screen.ui").read_text(encoding="utf-8"), "ui")
            self.assertEqual((installed / "file.ini").read_text(encoding="utf-8"), "default")
            self.assertTrue((installed / "data" / "autoTest").is_dir())
            self.assertTrue((installed / "data" / "saveData").is_dir())
            clean_install = Path(directory) / "clean"
            with patch.multiple(launcher, PROJECT_ROOT=bundled, APPLICATION_ROOT=clean_install), patch.object(launcher.sys, "frozen", True, create=True):
                launcher.copy_application_resources()
            self.assertFalse((clean_install / "config_file").exists())
            self.assertFalse((clean_install / "QT_designer").exists())

    def test_real_startup_constructs_all_windows_without_devices(self):
        application = QApplication.instance() or QApplication([])
        names = (
            "mainWindow", "autoTest", "HusaModelWindow", "PyroSetSystem",
            "SetDacValue", "PotTableSet", "DacTableCreate", "RunAutoTest",
            "deviceG800", "deviceBio24",
        )
        original = {name: getattr(state, name) for name in names}
        original_directory = Path.cwd()
        original_open = open
        log = MagicMock()
        log.__enter__.return_value = log

        def open_without_log_changes(filename, *args, **kwargs):
            if str(filename) == "check_error.txt":
                return log
            return original_open(filename, *args, **kwargs)

        try:
            with patch.object(launcher, "QApplication", return_value=application), patch.object(launcher, "acquire_single_instance", return_value=True), patch.object(application, "exec", return_value=0), patch.object(launcher, "copy_application_resources"), patch.object(MainWindow, "start_scan"), patch.object(MainWindow, "show"), patch.object(DeviceBio24, "start_scan"), patch("serial.tools.list_ports.comports", return_value=[]), patch("builtins.open", side_effect=open_without_log_changes):
                self.assertEqual(launcher.launch(), 0)
                for name in names:
                    self.assertIsNotNone(getattr(state, name))
                self.assertEqual(log.write.call_args_list, [call("")])
        finally:
            for name, value in original.items():
                window = getattr(state, name)
                if window is not value and window is not None:
                    window.deleteLater()
                setattr(state, name, value)
            application.processEvents()
            os.chdir(original_directory)

    def test_eval_expressions_have_shared_dependencies(self):
        dependencies = {
            name for module in (styles, paths) for name in vars(module)
            if not name.startswith("_") and isinstance(getattr(module, name), (str, Path))
        }
        dependencies.update({
            "mainWindow", "autoTest", "HusaModelWindow", "PyroSetSystem",
            "SetDacValue", "PotTableSet", "DacTableCreate", "RunAutoTest",
            "deviceG800", "deviceBio24",
        })
        for path in (PROJECT_ROOT / "src").glob("*.py"):
            module = importlib.import_module("src." + path.stem)
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for call in ast.walk(tree):
                if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id not in {"eval", "exec"} or not call.args:
                    continue
                for literal in ast.walk(call.args[0]):
                    if isinstance(literal, ast.Constant) and isinstance(literal.value, str):
                        names = set(re.findall(r"(?<![\w.])\b[A-Za-z_]\w*\b", literal.value))
                        with self.subTest(module=path.name, line=call.lineno):
                            self.assertFalse((names & dependencies) - set(vars(module)))

    def test_setup_windows_initialize_button_styles(self):
        application = QApplication.instance() or QApplication([])
        original_directory = Path.cwd()
        windows = []
        try:
            os.chdir(PROJECT_ROOT)
            husa = HusaSetModule()
            windows.append(husa)
            pyro = Bio21PyroSetSystem()
            windows.append(pyro)
            self.assertEqual(husa.MODEL_1.styleSheet(), ButtonStyleOff2)
            self.assertEqual(husa.M1_LB.styleSheet(), ButtonStyleOff2)
            self.assertEqual(pyro.SYSTEM1.styleSheet(), ButtonStyleOff2)
        finally:
            for window in windows:
                window.deleteLater()
            application.processEvents()
            os.chdir(original_directory)

    def test_automation_window_loads_existing_test_directory(self):
        self.assertEqual(Path(AUTO_TEST_PATH), Path("data") / "autoTest")
        self.assertTrue((PROJECT_ROOT / AUTO_TEST_PATH).is_dir())
        application = QApplication.instance() or QApplication([])
        original_directory = Path.cwd()
        window = None
        try:
            os.chdir(PROJECT_ROOT)
            window = AutoRunScript()
            self.assertEqual(window.dir_list[1:], os.listdir(AUTO_TEST_PATH))
        finally:
            if window is not None:
                window.deleteLater()
                application.processEvents()
            os.chdir(original_directory)

    def test_all_modules_compile(self):
        for path in (PROJECT_ROOT / "src").glob("*.py"):
            with self.subTest(module=path.name):
                compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_main_window_composes_feature_modules(self):
        for feature in (ConnectionMixin, SavingMixin, DigitalControlsMixin, AnalogControlsMixin):
            self.assertTrue(issubclass(MainWindow, feature))
        for method in ("connectBox", "start_scan", "saveToCsv", "output0", "output15", "read_adc", "set_pwm1"):
            self.assertTrue(callable(getattr(MainWindow, method)))

    def test_import_does_not_create_windows(self):
        self.assertIsNone(state.mainWindow)
        self.assertIsNone(state.deviceG800)
        self.assertIsNone(state.deviceBio24)

    def test_legacy_entry_point_only_launches_under_main_guard(self):
        tree = ast.parse((PROJECT_ROOT / "BOX_GUI.py").read_text(encoding="utf-8"))
        self.assertEqual(len(tree.body), 3)
        self.assertIsInstance(tree.body[-1], ast.If)
        expected = ast.parse("__name__ == '__main__'", mode="eval").body
        self.assertEqual(ast.dump(tree.body[-1].test), ast.dump(expected))

    def test_launcher_registers_shared_windows(self):
        names = {
            "mainWindow": "MainWindow", "autoTest": "AutoRunScript",
            "HusaModelWindow": "HusaSetModule", "PyroSetSystem": "Bio21PyroSetSystem",
            "SetDacValue": "SetDacPot", "PotTableSet": "CreatePotTable",
            "DacTableCreate": "CreateDacTable", "RunAutoTest": "CreateAutoTest",
            "deviceG800": "DeviceG800", "deviceBio24": "DeviceBio24",
        }
        modules = {
            "MainWindow": "ui", "AutoRunScript": "automation", "CreateAutoTest": "automation",
            "HusaSetModule": "setup_windows", "Bio21PyroSetSystem": "setup_windows",
            "SetDacPot": "tables", "CreatePotTable": "tables", "CreateDacTable": "tables",
            "DeviceG800": "g800", "DeviceBio24": "bio24",
        }
        constructors = {name: MagicMock() for name in names.values()}
        application = MagicMock()
        application.exec.return_value = 0
        original = {name: getattr(state, name) for name in names}
        try:
            with ExitStack() as stack:
                for name, constructor in constructors.items():
                    stack.enter_context(patch(f"src.{modules[name]}.{name}", constructor))
                stack.enter_context(patch.object(launcher, "QApplication", return_value=application))
                stack.enter_context(patch.object(launcher, "acquire_single_instance", return_value=True))
                stack.enter_context(patch.object(launcher, "apply_theme"))
                stack.enter_context(patch.object(launcher, "copy_application_resources"))
                stack.enter_context(patch.object(launcher.os, "chdir"))
                self.assertEqual(launcher.launch(), 0)
                for name, constructor in names.items():
                    self.assertIs(getattr(state, name), constructors[constructor].return_value)
                    constructors[constructor].assert_called_once_with()
                state.mainWindow.show.assert_called_once_with()
                application.exec.assert_called_once_with()
        finally:
            for name, value in original.items():
                setattr(state, name, value)

    def test_main_window_connect_to_device_launches_executable(self):
        application = QApplication.instance() or QApplication([])
        original_directory = Path.cwd()
        original_open = open

        def open_without_log_reset(filename, *args, **kwargs):
            if str(filename) == "check_error.txt" and args and args[0] == "w":
                return io.StringIO()
            return original_open(filename, *args, **kwargs)

        window = None
        try:
            os.chdir(PROJECT_ROOT)
            with tempfile.TemporaryDirectory(prefix="device connect ") as directory, patch.object(MainWindow, "start_scan"), patch.object(MainWindow, "connectBox") as connect, patch("src.ui.listConnection", return_value=[]), patch("builtins.open", side_effect=open_without_log_reset), patch("src.ui.subprocess.Popen") as launch, patch("src.ui.QMessageBox.warning") as warning:
                executable = Path(directory) / "OvenDeviceConnect.exe"
                executable.touch()
                window = MainWindow()
                window.show()
                launch.return_value.poll.return_value = None
                self.assertEqual(window.ConnectToDevice.text(), "ConnectToDevice")
                self.assertEqual(window.ConnectToDevice.receivers(window.ConnectToDevice.clicked), 1)
                self.assertEqual(window.ConnectToDevice.styleSheet(), ButtonStyleOff2)
                with patch("src.ui.OVEN_DEVICE_CONNECT_PATHS", (executable,)):
                    window.ConnectToDevice.click()
                    window.ConnectToDevice.click()
                self.assertTrue(window.isVisible())
                self.assertEqual(window.ConnectToDevice.styleSheet(), ButtonStyleOn2)
                launch.assert_called_once_with(
                    [str(executable), "--single-window"],
                    cwd=str(executable.parent),
                    creationflags=getattr(launcher.subprocess if hasattr(launcher, "subprocess") else __import__("subprocess"), "CREATE_NO_WINDOW", 0),
                )
                warning.assert_not_called()
                connect.assert_not_called()
                launch.return_value.poll.return_value = 0
                window.check_device_connect()
                self.assertTrue(window.isVisible())
                self.assertEqual(window.ConnectToDevice.styleSheet(), ButtonStyleOff2)
                window.BoxConnect.textActivated.emit("test-device - 192.168.1.10")
                connect.assert_called_once_with("test-device - 192.168.1.10")
        finally:
            if window is not None:
                window.deleteLater()
                application.processEvents()
            os.chdir(original_directory)

    def test_device_connect_warns_when_executable_is_missing(self):
        window = MagicMock()
        with tempfile.TemporaryDirectory() as directory, patch("src.ui.OVEN_DEVICE_CONNECT_PATHS", (Path(directory) / "OvenDeviceConnect.exe",)), patch("src.ui.subprocess.Popen") as launch, patch("src.ui.QMessageBox.warning") as warning:
            MainWindow.open_device_connect(window)
            launch.assert_not_called()
            window.ConnectToDevice.setStyleSheet.assert_not_called()
            warning.assert_called_once()
            self.assertIn("ni najden", warning.call_args[0][2])

    def test_device_connect_warns_when_launch_fails(self):
        window = MagicMock()
        with tempfile.TemporaryDirectory() as directory, patch("src.ui.subprocess.Popen", side_effect=OSError("Access denied")), patch("src.ui.QMessageBox.warning") as warning:
            executable = Path(directory) / "OvenDeviceConnect.exe"
            executable.touch()
            with patch("src.ui.OVEN_DEVICE_CONNECT_PATHS", (executable,)):
                MainWindow.open_device_connect(window)
            warning.assert_called_once()
            window.ConnectToDevice.setStyleSheet.assert_not_called()
            self.assertIn("Access denied", warning.call_args[0][2])


if __name__ == "__main__":
    unittest.main()