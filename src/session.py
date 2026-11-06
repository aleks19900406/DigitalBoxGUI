"""Remember digital box settings per device (COM port / IP) between application starts."""

import json
import traceback
from .paths import APPLICATION_ROOT
from .helpers import listBoxMarks
from .devices import serial_port_name
from .styles import ButtonStyleOn2

SESSION_FILE = APPLICATION_ROOT / "last_session.json"

DIGITAL_POT_WIDGETS = [f"digital_pot{index}" for index in range(6)]
VOLTAGE_WIDGETS = [f"SetVoltage{index}" for index in range(4)]
PWM1_WIDGETS = ["setPwmBegin1", "setPwmEnd1", "SetFrequency1", "SetDuty1"]
PWM2_WIDGETS = ["setPwmBegin2", "setPwmEnd2", "SetFrequency2", "SetDuty2"]
PWM_OLD_WIDGETS = ["SetFrequencyOld", "SetDutyOld"]


def device_key(connection):
    """Identify a device by its IP, or by its COM port for serial connections."""
    if not connection:
        return None
    if connection.get("ip"):
        return str(connection["ip"]).strip()
    text = str(connection.get("text") or "").strip()
    port = serial_port_name(text)
    if port:
        return port.upper() if port.upper().startswith("COM") else port
    return text or None


def read_session_file():
    try:
        with open(SESSION_FILE, encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError):
        return {}
    devices = data.get("devices") if isinstance(data, dict) else None
    return devices if isinstance(devices, dict) else {}


def write_session_file(devices):
    with open(SESSION_FILE, "w", encoding="utf-8") as file:
        json.dump({"devices": devices}, file, indent=4, ensure_ascii=False)


class SessionMixin:
    def _widget_values(self, names):
        return {name: getattr(self, name).value() for name in names}

    def _apply_widget_values(self, values):
        for name, value in (values or {}).items():
            widget = getattr(self, name, None)
            if widget is not None and value is not None:
                widget.setValue(value)

    def collect_session(self):
        return {
            "connection": self.session_connection,
            "box_mark": self.session_box_mark,
            "digital_pot": self._widget_values(DIGITAL_POT_WIDGETS),
            "voltage": self._widget_values(VOLTAGE_WIDGETS),
            "pwm1": self._widget_values(PWM1_WIDGETS),
            "pwm2": self._widget_values(PWM2_WIDGETS),
            "pwm_old": self._widget_values(PWM_OLD_WIDGETS),
            "excel_refresh": self.excelRefresh.value(),
            "auto": [self.index_auto[index] % 2 == 1 for index in range(4)],
            "outputs": [self.index_out[index] % 2 == 1 for index in range(16)],
        }

    def save_session(self):
        """Save the settings of the currently connected device (nothing is saved before a connection)."""
        key = device_key(self.session_connection)
        if self._restoring_session or not key:
            return
        try:
            devices = read_session_file()
            devices[key] = self.collect_session()
            write_session_file(devices)
        except Exception:
            with open('check_error.txt', 'a') as f:
                f.write(traceback.format_exc())

    def restore_session(self):
        """Re-apply settings saved for the currently connected device, if it was used before."""
        self.load_device_layout(device_key(self.session_connection))
        data = read_session_file().get(device_key(self.session_connection))
        if data:
            self._restoring_session = True
            try:
                box_mark = data.get("box_mark")
                if box_mark in listBoxMarks():
                    self.BoxMarks.setCurrentText(box_mark)
                    self.boxMarks(box_mark)

                for key in ("pwm1", "pwm2", "pwm_old", "voltage", "digital_pot"):
                    self._apply_widget_values(data.get(key))
                if data.get("excel_refresh") is not None:
                    self.excelRefresh.setValue(data["excel_refresh"])

                for index, enabled in enumerate(data.get("outputs", [])[:16]):
                    self.index_out[index] = 1 if enabled else 0

                for index, enabled in enumerate(data.get("auto", [])[:4]):
                    button = getattr(self, f"AUTO{index + 1}")
                    if enabled and button.isEnabled():
                        self.index_auto[index] = 1
                        button.setStyleSheet(ButtonStyleOn2)
            except Exception:
                with open('check_error.txt', 'a') as f:
                    f.write(traceback.format_exc())
            finally:
                self._restoring_session = False
        self.save_session()
