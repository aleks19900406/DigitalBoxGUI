from time import monotonic
from PyQt6.QtCore import QTime, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox,
                             QTimeEdit, QVBoxLayout)
from .styles import ButtonStyleOff2, ButtonStyleOn2
from .compact_layout import compact_layout_wanted, enlarge_dialog

# low / high temperature are this far below / above the current temperature when the window is opened
DEFAULT_SPAN = 10
# the up / down arrows of the temperature fields change the value by this much
TEMP_STEP = 10


class TemperatureRegulationDialog(QDialog):
    """Moves a digital pot (temperature) slider up and down between two temperatures again and again
    (e.g. 190 - 210 around the oven set point of 200) until it is stopped."""
    runningChanged = pyqtSignal(bool)

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle('Temperature regulation')
        self.running = False
        self._slider = None
        self._low = 0
        self._high = 0
        self._up = 1.0
        self._down = 1.0
        self._t0 = 0.0

        self.potCombo = QComboBox()
        self.lowTemp = QSpinBox()
        self.highTemp = QSpinBox()
        for spin in (self.lowTemp, self.highTemp):
            spin.setSingleStep(TEMP_STEP)
        self.timeUp = QTimeEdit()
        self.timeDown = QTimeEdit()
        for edit in (self.timeUp, self.timeDown):
            edit.setDisplayFormat('hh:mm:ss')
            edit.setTime(QTime(0, 5, 0))
        self.status = QLabel('')
        self.startButton = QPushButton('START')
        self.stopButton = QPushButton('STOP')
        self.startButton.setStyleSheet(ButtonStyleOff2)
        self.stopButton.setStyleSheet(ButtonStyleOff2)
        self.stopButton.setEnabled(False)

        form = QFormLayout()
        form.addRow('Slider', self.potCombo)
        form.addRow('Low temperature', self.lowTemp)
        form.addRow('High temperature', self.highTemp)
        form.addRow('Time low -> high (hh:mm:ss)', self.timeUp)
        form.addRow('Time high -> low (hh:mm:ss)', self.timeDown)
        buttons = QHBoxLayout()
        buttons.addWidget(self.startButton)
        buttons.addWidget(self.stopButton)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.status)

        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.tick)
        self.potCombo.currentIndexChanged.connect(self.on_pot_changed)
        self.startButton.clicked.connect(self.start)
        self.stopButton.clicked.connect(lambda: self.stop())
        if compact_layout_wanted():
            enlarge_dialog(self)

    def open_dialog(self):
        if not self.running:
            self.refresh_pots()
        self.show()
        self.raise_()
        self.activateWindow()

    def refresh_pots(self):
        """List the sliders that are shown in the main window."""
        window = self.main_window
        previous = self.potCombo.currentData()
        self.potCombo.blockSignals(True)
        self.potCombo.clear()
        for index in range(6):
            if getattr(window, f'digital_pot{index}').isVisibleTo(window):
                label = getattr(window, f'labelDigitalPot{index}').text().strip() or f'Table {index + 1}'
                self.potCombo.addItem(label, index)
        position = self.potCombo.findData(previous)
        self.potCombo.setCurrentIndex(position if position >= 0 else 0)
        self.potCombo.blockSignals(False)
        self.on_pot_changed()

    def on_pot_changed(self):
        """The temperatures are limited to the range of the selected slider."""
        index = self.potCombo.currentData()
        if index is None:
            return
        slider = getattr(self.main_window, f'digital_pot{index}')
        for spin in (self.lowTemp, self.highTemp):
            spin.setRange(slider.minimum(), slider.maximum())
        self.lowTemp.setValue(max(slider.minimum(), slider.value() - DEFAULT_SPAN))
        self.highTemp.setValue(min(slider.maximum(), slider.value() + DEFAULT_SPAN))

    def set_running(self, running):
        self.running = running
        for widget in (self.potCombo, self.lowTemp, self.highTemp, self.timeUp, self.timeDown):
            widget.setEnabled(not running)
        self.startButton.setEnabled(not running)
        self.stopButton.setEnabled(running)
        self.startButton.setStyleSheet(ButtonStyleOn2 if running else ButtonStyleOff2)
        self.runningChanged.emit(running)

    def start(self):
        index = self.potCombo.currentData()
        if index is None:
            self.status.setText('No slider is shown.')
            return
        if self.main_window.index_refreshing < 1:
            self.status.setText('Connect the box first.')
            return
        if self.main_window.rampDialog.running:
            self.status.setText('Stop TEMP RAMP first.')
            return
        up = QTime(0, 0).secsTo(self.timeUp.time())
        down = QTime(0, 0).secsTo(self.timeDown.time())
        if up <= 0 or down <= 0:
            self.status.setText('Times must be longer than 0.')
            return
        low, high = sorted((self.lowTemp.value(), self.highTemp.value()))
        if low == high:
            self.status.setText('Low and high temperature must differ.')
            return
        self._slider = getattr(self.main_window, f'digital_pot{index}')
        self._low, self._high = low, high
        self._up, self._down = float(up), float(down)
        self._t0 = monotonic()
        self.set_running(True)
        self.tick()
        self.timer.start()

    def stop(self, message='Stopped.'):
        self.timer.stop()
        if self.running:
            self.set_running(False)
        self.status.setText(message)

    def tick(self):
        if self.main_window.index_refreshing < 1:
            self.stop('Stopped: the box is not connected.')
            return
        cycle, position = divmod(monotonic() - self._t0, self._up + self._down)
        span = self._high - self._low
        if position < self._up:
            value = round(self._low + span * position / self._up)
            direction = 'up'
        else:
            value = round(self._high - span * (position - self._up) / self._down)
            direction = 'down'
        self._slider.setValue(value)
        self.status.setText(f'{self.potCombo.currentText()}: {value} ({direction})   cycle {int(cycle) + 1}')
