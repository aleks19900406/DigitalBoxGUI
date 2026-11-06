from time import monotonic
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel, QPushButton,
                             QVBoxLayout)
from .styles import ButtonStyleOff2, ButtonStyleOn2
from .compact_layout import compact_layout_wanted, enlarge_dialog

ON_OFF_BUTTON = -1   # item data of the main ON/OFF button in the list
MIN_TIME = 0.5       # seconds: the digital box is refreshed about every 100 ms or slower


class OutputToggleDialog(QDialog):
    """Switches a digital output (or the main ON/OFF button) on and off again and again, e.g. door:
    2 s on, 3 s off, until it is stopped. The real buttons are clicked, so the box, the icons and the
    session behave exactly as if the user clicked them."""
    runningChanged = pyqtSignal(bool)

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle('Toggle output')
        self.running = False
        self._target = None
        self._on_time = 1.0
        self._off_time = 1.0
        self._phase_on = True
        self._phase_end = 0.0
        self._cycle = 1

        self.outputCombo = QComboBox()
        self.timeOn = QDoubleSpinBox()
        self.timeOff = QDoubleSpinBox()
        for spin, value in ((self.timeOn, 2.0), (self.timeOff, 3.0)):
            spin.setRange(MIN_TIME, 86400.0)
            spin.setDecimals(1)
            spin.setSingleStep(1.0)
            spin.setSuffix(' s')
            spin.setValue(value)
        self.status = QLabel('')
        self.startButton = QPushButton('START')
        self.stopButton = QPushButton('STOP')
        self.startButton.setStyleSheet(ButtonStyleOff2)
        self.stopButton.setStyleSheet(ButtonStyleOff2)
        self.stopButton.setEnabled(False)

        form = QFormLayout()
        form.addRow('Output', self.outputCombo)
        form.addRow('Time on', self.timeOn)
        form.addRow('Time off', self.timeOff)
        buttons = QHBoxLayout()
        buttons.addWidget(self.startButton)
        buttons.addWidget(self.stopButton)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.status)

        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.tick)
        self.startButton.clicked.connect(self.start)
        self.stopButton.clicked.connect(lambda: self.stop())
        if compact_layout_wanted():
            enlarge_dialog(self)

    def open_dialog(self):
        if not self.running:
            self.refresh_outputs()
        self.show()
        self.raise_()
        self.activateWindow()

    def refresh_outputs(self):
        """List the ON/OFF button and the digital outputs that are shown in the main window (with their names)."""
        window = self.main_window
        previous = self.outputCombo.currentData()
        self.outputCombo.clear()
        self.outputCombo.addItem('ON / OFF button', ON_OFF_BUTTON)
        for index in range(16):
            button = getattr(window, f'OUT{index}')
            if button.isVisibleTo(window):
                self.outputCombo.addItem(button.text().strip() or f'OUT{index}', index)
        position = self.outputCombo.findData(previous)
        self.outputCombo.setCurrentIndex(position if position >= 0 else 0)

    def _button(self, target):
        return self.main_window.on_off if target == ON_OFF_BUTTON else getattr(self.main_window, f'OUT{target}')

    def _is_on(self, target):
        if target == ON_OFF_BUTTON:
            return self.main_window.index_on_off % 2 == 1
        return self.main_window.index_out[target] == 1

    def set_output(self, on):
        """Click the real button when the output is not in the wanted state."""
        if self._is_on(self._target) != on:
            self._button(self._target).click()

    def set_running(self, running):
        self.running = running
        for widget in (self.outputCombo, self.timeOn, self.timeOff):
            widget.setEnabled(not running)
        self.startButton.setEnabled(not running)
        self.stopButton.setEnabled(running)
        self.startButton.setStyleSheet(ButtonStyleOn2 if running else ButtonStyleOff2)
        self.runningChanged.emit(running)

    def start(self):
        target = self.outputCombo.currentData()
        if target is None:
            self.status.setText('No output is shown.')
            return
        if self.main_window.index_refreshing < 1:
            self.status.setText('Connect the box first.')
            return
        self._target = target
        self._on_time = self.timeOn.value()
        self._off_time = self.timeOff.value()
        self._phase_on = True
        self._cycle = 1
        self._phase_end = monotonic() + self._on_time
        self.set_running(True)
        self.set_output(True)
        self.timer.start()
        self.show_status()

    def stop(self, message='Stopped, the output is off.'):
        """The output is switched off when the toggling stops."""
        self.timer.stop()
        if self.running:
            if self.main_window.index_refreshing >= 1:
                self.set_output(False)
            self.set_running(False)
        self.status.setText(message)

    def tick(self):
        if self.main_window.index_refreshing < 1:
            self.stop('Stopped: the box is not connected.')
            return
        now = monotonic()
        if now >= self._phase_end:
            self._phase_on = not self._phase_on
            if self._phase_on:
                self._cycle += 1
            duration = self._on_time if self._phase_on else self._off_time
            # keep the rhythm, but do not catch up after a long delay
            self._phase_end = self._phase_end + duration if now - self._phase_end < duration else now + duration
            self.set_output(self._phase_on)
        self.show_status()

    def show_status(self):
        remaining = max(0.0, self._phase_end - monotonic())
        self.status.setText(f'{self.outputCombo.currentText()}: {"ON" if self._phase_on else "OFF"}   '
                            f'{remaining:.1f} s   cycle {self._cycle}')
