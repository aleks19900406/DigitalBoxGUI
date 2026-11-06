from time import monotonic
from PyQt6.QtCore import QTime, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QProgressBar,
                             QPushButton, QSpinBox, QTimeEdit, QVBoxLayout)
from .styles import ButtonStyleOff2, ButtonStyleOn2
from .compact_layout import compact_layout_wanted, enlarge_dialog

# the end temperature is this much above the start temperature until the user changes it
END_OFFSET = 40
# the up / down arrows of the temperature fields change the value by this much
TEMP_STEP = 10


class TemperatureRampDialog(QDialog):
    """Moves a digital pot (temperature) slider slowly from the start to the end temperature in the given time."""
    runningChanged = pyqtSignal(bool)

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle('Temperature ramp')
        self.running = False
        self._end_touched = False
        self._auto_end = False
        self._slider = None
        self._start = 0
        self._end = 0
        self._total = 1.0
        self._t0 = 0.0

        self.potCombo = QComboBox()
        self.startTemp = QSpinBox()
        self.endTemp = QSpinBox()
        for spin in (self.startTemp, self.endTemp):
            spin.setSingleStep(TEMP_STEP)
        self.duration = QTimeEdit()
        self.duration.setDisplayFormat('hh:mm:ss')
        self.duration.setTime(QTime(0, 10, 0))
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.status = QLabel('')
        self.startButton = QPushButton('START')
        self.stopButton = QPushButton('STOP')
        self.startButton.setStyleSheet(ButtonStyleOff2)
        self.stopButton.setStyleSheet(ButtonStyleOff2)
        self.stopButton.setEnabled(False)

        form = QFormLayout()
        form.addRow('Slider', self.potCombo)
        form.addRow('Start temperature', self.startTemp)
        form.addRow('End temperature', self.endTemp)
        form.addRow('Time (hh:mm:ss)', self.duration)
        buttons = QHBoxLayout()
        buttons.addWidget(self.startButton)
        buttons.addWidget(self.stopButton)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)

        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.tick)
        self.potCombo.currentIndexChanged.connect(self.on_pot_changed)
        self.startTemp.valueChanged.connect(self.on_start_changed)
        self.endTemp.valueChanged.connect(self.on_end_changed)
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
        """The temperatures are limited to the range of the selected slider; start is the current temperature."""
        index = self.potCombo.currentData()
        if index is None:
            return
        slider = getattr(self.main_window, f'digital_pot{index}')
        for spin in (self.startTemp, self.endTemp):
            spin.setRange(slider.minimum(), slider.maximum())
        self._end_touched = False
        self.startTemp.setValue(slider.value())
        self.on_start_changed()

    def on_start_changed(self):
        """Until the user sets the end temperature it is always END_OFFSET above the start temperature."""
        if not self._end_touched:
            self._auto_end = True
            self.endTemp.setValue(min(self.startTemp.value() + END_OFFSET, self.endTemp.maximum()))
            self._auto_end = False

    def on_end_changed(self):
        if not self._auto_end:
            self._end_touched = True

    def set_running(self, running):
        self.running = running
        self.potCombo.setEnabled(not running)
        self.startTemp.setEnabled(not running)
        self.endTemp.setEnabled(not running)
        self.duration.setEnabled(not running)
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
        if self.main_window.regDialog.running:
            self.status.setText('Stop REG TEMP first.')
            return
        seconds = QTime(0, 0).secsTo(self.duration.time())
        if seconds <= 0:
            self.status.setText('Time must be longer than 0.')
            return
        self._slider = getattr(self.main_window, f'digital_pot{index}')
        self._start = self.startTemp.value()
        self._end = self.endTemp.value()
        self._total = float(seconds)
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
        elapsed = monotonic() - self._t0
        fraction = min(1.0, elapsed / self._total)
        value = round(self._start + (self._end - self._start) * fraction)
        self._slider.setValue(value)
        self.progress.setValue(int(fraction * 100))
        remaining = max(0, int(round(self._total - elapsed)))
        self.status.setText(f'{self.potCombo.currentText()}: {value}   remaining '
                            f'{remaining // 3600:02d}:{remaining % 3600 // 60:02d}:{remaining % 60:02d}')
        if fraction >= 1.0:
            self.stop(f'Done: {self.potCombo.currentText()} is at {value}.')
