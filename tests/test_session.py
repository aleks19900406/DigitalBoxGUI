"""Round-trip check for last_session.json without a connected device."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src import layout_editor, session
from src.paths import PROJECT_ROOT
from src.ui import MainWindow


class SessionRoundTripTests(unittest.TestCase):
    def test_settings_are_restored_only_when_the_same_device_is_selected_again(self):
        application = QApplication.instance() or QApplication([])
        original_directory = Path.cwd()
        windows = []
        try:
            os.chdir(PROJECT_ROOT)
            with tempfile.TemporaryDirectory() as directory, \
                    patch.object(session, "SESSION_FILE", Path(directory) / "last_session.json"), \
                    patch.object(layout_editor, "LAYOUT_FILE", Path(directory) / "box_layout.json"), \
                    patch.object(MainWindow, "start_scan"):
                first = MainWindow()
                windows.append(first)
                first.save_session()
                self.assertFalse(session.SESSION_FILE.exists(), "nothing is saved before a device was connected")

                first.session_connection = {"text": "BIO24-G800 - 192.168.88.20", "ip": "192.168.88.20"}
                first.boxMarks("BIO24_Elements_CraftF")
                self.assertTrue(first.AUTO1.isEnabled())
                self.assertTrue(first.AUTO2.isEnabled())
                self.assertFalse(first.AUTO3.isEnabled())
                first.buttonAuto1()
                first.buttonAuto2()
                first.output3()
                first.SetVoltage1.setValue(first.SetVoltage1.maximum())
                first.SetDuty1.setValue(first.SetDuty1.maximum())
                first.save_session()
                self.assertTrue(session.SESSION_FILE.exists())

                other = MainWindow()
                windows.append(other)
                default_voltage = other.SetVoltage1.value()
                other.session_connection = {"text": "COM3 - NodeMCU ESP32", "ip": None}
                other.restore_session()
                self.assertEqual(other.SetVoltage1.value(), default_voltage)
                self.assertEqual(other.index_auto, [0, 0, 0, 0])
                self.assertEqual(other.index_out[3], 0)

                same = MainWindow()
                windows.append(same)
                same.session_connection = {"text": "BIO24-G800 - 192.168.88.20", "ip": "192.168.88.20"}
                same.restore_session()
                self.assertEqual(same.SetVoltage1.value(), first.SetVoltage1.value())
                self.assertEqual(same.SetDuty1.value(), first.SetDuty1.value())
                self.assertEqual(same.index_auto, [1, 1, 0, 0])
                self.assertEqual(same.index_out[3], 1)

                # the layout is remembered per device; the whole box is shown for a new device
                first.OUT0.move(first.OUT0.x() + 100, first.OUT0.y())
                first.custom_positions["OUT0"] = (first.OUT0.x(), first.OUT0.y())
                first._save_layout()
                again = MainWindow()
                windows.append(again)
                default_position = again.OUT0.pos()
                again.session_connection = {"text": "BIO24-G800 - 192.168.88.20", "ip": "192.168.88.20"}
                again.restore_session()
                self.assertEqual(again.OUT0.x(), default_position.x() + 100)
                third = MainWindow()
                windows.append(third)
                third.session_connection = {"text": "COM3 - NodeMCU ESP32", "ip": None}
                third.restore_session()
                self.assertEqual(third.OUT0.pos(), default_position)
        finally:
            for window in windows:
                window.deleteLater()
            application.processEvents()
            os.chdir(original_directory)


if __name__ == "__main__":
    unittest.main()
