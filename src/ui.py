import datetime
import ipaddress
import os
import shlex
import subprocess
import traceback
from pathlib import Path
from time import sleep, time
from PyQt6 import QtGui
from PyQt6.QtWidgets import QFrame, QInputDialog, QLabel, QMainWindow, QMessageBox, QPushButton
from PyQt6.uic import loadUi
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QDateTime, QSettings, QThreadPool, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QFont
from DigitalBox.lib import select_model, select_model_LB, select_system
from . import state
from .paths import APPLICATION_ROOT, BOX_MARKS_PATH, DATA_SAVE, IMAGE_PATH_OTHER, OVEN_DEVICE_CONNECT_PATHS, QT_DESIGNER, SERVICES_DEFAULT_IP, SERVICES_PORT, update_command
from .styles import ButtonStyleOff2, ButtonStyleOn, ButtonStyleOn2, ButtonStyleWhite, MainScreenStyle, apply_theme, saved_theme
from .workers import Worker
from .temperature_ramp import TemperatureRampDialog
from .temperature_regulation import TemperatureRegulationDialog
from .output_toggle import OutputToggleDialog
from .devices import listConnection
from .helpers import dataFile, listBoxMarks, listDigitalPotTable
from .box_marks import box_mark_name, load_box_mark
from .connections import ConnectionMixin
from .saving import SavingMixin
from .digital_controls import DigitalControlsMixin
from .analog_controls import AnalogControlsMixin
from .session import SessionMixin
from .layout_mode import LayoutModeMixin, FULL_SYSTEMS_LABEL, FULL_WINDOW_WIDTH, FULL_WINDOW_HEIGHT
from .compact_layout import compact_layout_wanted, enlarge_dialog
from .layout_editor import LayoutEditMixin
from .scaling import fit_window_to_screen
from .heater_systems import load_heater_systems


class MainWindow(ConnectionMixin, SavingMixin, DigitalControlsMixin, AnalogControlsMixin, SessionMixin, LayoutModeMixin, LayoutEditMixin, QMainWindow):
    saveFinished = pyqtSignal(str)   # emitted from the save thread, handled in the GUI thread

    def __init__(self):
        super().__init__()
        self.saveFinished.connect(self.onSaveFinished)
        Window1 = QT_DESIGNER / 'Main_screen.ui'
        loadUi(str(Window1),self)
        f = open("check_error.txt", "w")
        f.write("")
        f.close()
        self.refreshSaving = 1000
        self.index_on_off = 0
        self.index_out = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.index_auto =[0,0,0,0]
        self.index_extras = [0,0,0,0,0,0,0,0,0,0]
        #####################auto button##################
        count = 4
        self.read_input = [0] * 32   # adjust size to your actual number of inputs
        # defaults so saving works before the first successful device read
        self.read_adc_all = [0, 0, 0, 0]
        self.read_pwm_all = [{'f': 0, 'd': 0}, {'f': 0, 'd': 0}]
        self.readVoltage = [0, 0, 0, 0]
        self.readPwm1 = [0, 0]
        self.readPwm2 = [0, 0]
        self.readPwmOld = [0, 0]
        self.readDigitalPot0 = self.readDigitalPot1 = self.readDigitalPot2 = 0
        self.readDigitalPot3 = self.readDigitalPot4 = self.readDigitalPot5 = 0
        self.readDac0 = self.readDac1 = self.readDac2 = self.readDac3 = 0
        self.readDac4 = self.readDac5 = self.readDac6 = self.readDac7 = 0
        self.signal_on = [0] * count
        self.signal_off = [0] * count
        self.periode = [0] * count
        self.current_output = [None] * count
        self.output_start = [None] * count
        self.pulse_start = [None] * count
        self.pulse_ticks = [0] * count
        self.pulse_last_input = [False] * count
        self.param_auto1 = 0
        self.param_auto2 = 0
        self.param_auto3 = 0
        self.param_auto4 = 0
        ##################################################
        self.connectParameters = 0
        self.box_is_connected = 0
        self.index_refreshing = 0
        self.digitalPotChange = 0
        self.digitalPotIndex = 0
        self.indexSaveData = 0
        self.indexButtonSave = 0
        self.repeatSaveData = 0
        self.indexBackup = 0
        self.indexUpdate = 0
        self.session_connection = None
        self.session_box_mark = None
        self.box_mark_data = None
        self._pot_connected = set()
        self.pots_active = False
        self.active_pots = None  # None = all sliders, otherwise indexes of sliders with a name in the box marks
        self._restoring_session = False
        self.heater_systems = []
        self.serial_input = None
        self.setWindowTitle(f'DIGITAL BOX MAIN {state.DIGITAL_BOX_VERSION}')
        self.setGeometry(150, 40, 1530, 1050)
        self.enable_screen_scaling()
        fit_window_to_screen(self, FULL_WINDOW_WIDTH, FULL_WINDOW_HEIGHT, 150, 40)
        #self.setSizeIncrement(1920, 1080)
        # bigger digital input/output buttons so longer box marks are not cut off
        for index in range(32):
            button = getattr(self, f'INPUT_{index}')
            column = (button.x() - 20) // 70
            button.setGeometry(15 + column * 76, button.y() - 2, 70, 36)
        for index in range(16):
            button = getattr(self, f'OUT{index}')
            column = (button.x() - 660) // 90
            button.setGeometry(645 + column * 90, button.y() - 2, 82, 44)
        lines = [frame for frame in self.findChildren(QFrame)
                 if type(frame) is QFrame and frame.frameShape() in (QFrame.Shape.HLine, QFrame.Shape.VLine)]
        for line in lines:
            line.lower()
        for label in self.findChildren(QLabel):
            if label.text() and any(line.geometry().intersects(label.geometry()) for line in lines):
                label.setProperty("sectionTitle", True)
        self.setStyleSheet(MainScreenStyle)
        self.setup_theme_button()
        self.setup_temperature_ramp()
        self.on_off.clicked.connect(self.button_OnOff)
        self.RefreshingConnection.clicked.connect(self.BoxRefreshing)
        self.RefreshingConnection.setStyleSheet(ButtonStyleOff2)
        self.SetPwmBar1.valueChanged.connect(self.SetFrequencyBar1)
        self.SetPwmBar2.valueChanged.connect(self.SetFrequencyBar2)
        ################## ERROR MESSAGE #########################################
        self.BOX_VERSION.setVisible(False)
        self.BOX_VERSION.setFont(QFont('Arial', 14))
        self.BOX_VERSION.setStyleSheet("color: red")
        self.warningMessagePot.setVisible(False)
        self.warningMessagePot.setFont(QFont('Arial', 12))
        self.warningMessagePot.setStyleSheet("color: red")
        self.warningMessageDac.setVisible(False)
        self.warningMessageDac.setFont(QFont('Arial', 12))
        self.warningMessageDac.setStyleSheet("color: red")
        self.label_errorSaveFile.setVisible(False)
        self.label_errorSaveFile.setFont(QFont('Arial', 12))
        self.label_errorSaveFile.setStyleSheet("color: red")
        self.labelTableOpenError.setVisible(False)
        self.labelTableOpenError.setFont(QFont('Arial', 20))
        self.labelTableOpenError.setStyleSheet("color: red")
        self.connectBar.setVisible(False)
        self.digital_input_label_geometry = self.label_marks_2.geometry()
        self.digital_input_systems_geometry = FULL_SYSTEMS_LABEL
        self.digital_input_label_alignment = self.label_marks_2.alignment()
        self.digital_input_label_font = self.label_marks_2.font()
        self.label_marks_2.setWordWrap(True)
        ################## DIGITAL OUTPUT #########################################
        self.OUT0.clicked.connect(self.output0)
        self.OUT1.clicked.connect(self.output1)
        self.OUT2.clicked.connect(self.output2)
        self.OUT3.clicked.connect(self.output3)
        self.OUT4.clicked.connect(self.output4)
        self.OUT5.clicked.connect(self.output5)
        self.OUT6.clicked.connect(self.output6)
        self.OUT7.clicked.connect(self.output7)
        self.OUT8.clicked.connect(self.output8)
        self.OUT9.clicked.connect(self.output9)
        self.OUT10.clicked.connect(self.output10)
        self.OUT11.clicked.connect(self.output11)
        self.OUT12.clicked.connect(self.output12)
        self.OUT13.clicked.connect(self.output13)
        self.OUT14.clicked.connect(self.output14)
        self.OUT15.clicked.connect(self.output15)
        for index in range(16):
            getattr(self, f'OUT{index}').clicked.connect(self.save_session)
        #######################AUTO BUTTON #######################################
        self.AUTO1.clicked.connect(self.buttonAuto1)
        self.AUTO2.clicked.connect(self.buttonAuto2)
        self.AUTO3.clicked.connect(self.buttonAuto3)
        self.AUTO4.clicked.connect(self.buttonAuto4)
        for auto_button in (self.AUTO1, self.AUTO2, self.AUTO3, self.AUTO4):
            auto_button.setEnabled(False)
        ###################### BUTTON OPEN ADDITIONAL SCREEN ######################
        self.ButtonHusaModel.clicked.connect(self.buttonHusaModel)
        self.ButtonG800.clicked.connect(self.buttonG800)
        self.ButtonBIO24.clicked.connect(self.buttonBio24)
        self.ButtonPyroSystem.clicked.connect(self.buttonPyroSystem)
        self.ButtonDacSet.clicked.connect(self.buttonDacSet)
        self.ButtonSetPot.clicked.connect(self.buttonSetPot)
        self.ButtonSetDac.clicked.connect(self.buttonSetDac)
        self.ButtonAutomation.clicked.connect(self.buttonAutomation)
        self._device_connect_process = None
        self._device_connect_timer = QTimer(self)
        self._device_connect_timer.setInterval(500)
        self._device_connect_timer.timeout.connect(self.check_device_connect)
        self.ConnectToDevice.clicked.connect(self.open_device_connect)
        self.ConnectToDevice.setStyleSheet(ButtonStyleOff2)
        #self.ButtonCreateAutoTest.clicked.connect(self.buttonCreateAutoTest)
        self.ButtonCreateAutoTest.setVisible(False)
        self.barOpenAutoTest.setVisible(False)
        self.SetEnvirement.setVisible(False)
        self.setEnvironmentText.setVisible(False)
        self.update_gui.clicked.connect(self.updateGui)
        self.update_gui.setStyleSheet(ButtonStyleOff2)
        ########################### BOX CONNECTED #################################
        self.BoxConnect.textActivated.connect(self.connectBox)
        self.BoxConnect.setEditable(True)
        self.BoxConnect.setStyleSheet(ButtonStyleWhite)
        self.BoxMarks.textActivated.connect(self.boxMarks)
        self.BoxMarks.setEditable(True)
        self.BoxMarks.setStyleSheet(ButtonStyleWhite)
        self.BoxMarks.addItems(listBoxMarks())
        self.ExcelFile.addItems(dataFile())
        ##################### SAVE DATA ##########################################
        self.ExcelFile.textActivated.connect(self.excelFile)
        self.ExcelFile.setEditable(True)
        self.ExcelFile.setStyleSheet(ButtonStyleWhite)
        self.startStopSaving.clicked.connect(self.startStopSave)
        self.startStopSaving.setEnabled(False)
        self.startStopSaving.setStyleSheet(ButtonStyleOff2)
        self.backupSave.setVisible(False)
        self.backupSave.setStyleSheet("color: red")
        ################### TIMER ################################################
        self.saveBarThread = QThread()
        self.worker = Worker()
        self.worker.stepIncreased.connect(self.SaveBarShow)
        self.worker.moveToThread(self.saveBarThread)
        self.saveBarThread.started.connect(self.worker.task)
        self.worker.finished.connect(self.saveBarThread.quit)
        self.DIGITAL_BOX_MAIN = QTimer()
        self.DIGITAL_BOX_MAIN.timeout.connect(self.timerDigitalBox)  # 
        self.DIGITAL_BOX_MAIN.setInterval(state.MAIN_TIME_REFRESHING)
        self.ReadSetPotDac = QTimer()
        self.ReadSetPotDac.timeout.connect(self.timerCreatePotDacTable)  # 
        self.ReadSetPotDac.setInterval(state.MAIN_TIME_REFRESHING)
        self.refreshSaveData = QTimer()
        self.refreshSaveData.timeout.connect(self.savingData)  # 
        self.refreshSaveData.setInterval(state.MAIN_TIME_REFRESHING)
        self.dateTimeTimer = QTimer()
        self.dateTimeTimer.timeout.connect(self.showTime)  # 
        self.dateTimeTimer.setInterval(state.MAIN_TIME_REFRESHING)
        self.thread_check_input = QThreadPool()
        # one reader at a time: slow answers of the box must not pile up tasks and threads
        self.thread_check_input.setMaxThreadCount(1)
        self.reading_inputs = False
        #self.time_show = QThreadPool()
        self.saveDataThread = QThreadPool()
        self.connectAnimation = QThreadPool()
        ###########################################################################
        self.date_and_time.setText("")
        self.savingBar.setVisible(False)
        ############################## BUTTON ICON ###############################
        self.on_off.setStyleSheet(ButtonStyleOff2)
        
        self.iconSwitchOff = QtGui.QIcon()
        self.iconSwitchOff.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/switchOff.png')))
    
        self.iconSwitchOn = QtGui.QIcon()
        self.iconSwitchOn.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/switchOn.png')))
        
        self.iconOff = QtGui.QIcon()
        self.iconOff.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/offButton.png')))
        self.on_off.setIcon(self.iconOff)
        self.iconOn = QtGui.QIcon()
        self.iconOn.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/OnButton.png')))
        
        self.iconRefresh = QtGui.QIcon()
        self.iconRefresh.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/ButtonRefresh.png')))
        self.RefreshingConnection.setIcon(self.iconRefresh)
        
        self.iconSaveData = QtGui.QIcon()
        self.iconSaveData.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOn.png')))
        self.startStopSaving.setIcon(self.iconSaveData)
        
        self.iconUpdate = QtGui.QIcon()
        self.iconUpdate.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/update.png')))
        self.update_gui.setIcon(self.iconUpdate)
        self.scan_thread = None
        self.scanner = None
        self.worker = Worker()
        self.worker.stepIncreased.connect(self.SaveBarShow)
        self.worker.moveToThread(self.saveBarThread)
        self.saveBarThread.started.connect(self.worker.task)
        self.ip_scanning.setVisible(True)
        self.setup_layout_mode()
        self.apply_pot_tables()
        self.start_scan()
        self.BoxConnect.addItems(listConnection())

    def open_device_connect(self):
        process = getattr(self, "_device_connect_process", None)
        if process is not None and process.poll() is None:
            return
        executable = next((path for path in OVEN_DEVICE_CONNECT_PATHS if path.is_file()), None)
        if executable is None:
            locations = "\n".join(str(path) for path in OVEN_DEVICE_CONNECT_PATHS)
            QMessageBox.warning(self, "ConnectToDevice", f"OvenDeviceConnect.exe ni najden.\n\n{locations}")
            return
        try:
            process = subprocess.Popen(
                [str(executable), "--single-window"],
                cwd=str(executable.parent),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError as error:
            QMessageBox.warning(self, "ConnectToDevice", f"OvenDeviceConnect.exe ni bilo mogoce zagnati.\n\n{error}")
            return
        self._device_connect_process = process
        self.ConnectToDevice.setStyleSheet(ButtonStyleOn2)
        self._device_connect_timer.start()

    def check_device_connect(self):
        if self._device_connect_process is None or self._device_connect_process.poll() is None:
            return
        self._device_connect_timer.stop()
        self._device_connect_process = None
        self.ConnectToDevice.setStyleSheet(ButtonStyleOff2)

    def closeEvent(self, event):
        """
        show the message when you close the application
        """
        self.DIGITAL_BOX_MAIN.stop()
        if not self.indexUpdate:
            close = QMessageBox()
            close.setText("Are you sure you want to close digital box ?")
            close.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
            close = close.exec()
            if  close == QMessageBox.StandardButton.Yes:
                self.save_session()
                #close all screen if main app close
                try:
                    if self.indexButtonSave == 1: #backup
                        self.wb.save(f"{DATA_SAVE}/{self.fileName}_backup.csv")
                        
                except PermissionError:
                    self.wb.save(f"{DATA_SAVE}/{self.fileName}_backup.csv")
                
                with open("check_error.txt") as f:
                    with open("ALL_ERROR.txt", "a") as f1:
                        for line in f:
                            f1.write(line)
                event.accept()
                state.mainWindow.close()
                state.HusaModelWindow.close()
                state.deviceG800.close()
                state.PyroSetSystem.close()
                state.SetDacValue.close()
                state.PotTableSet.close()
                state.DacTableCreate.close()
                state.RunAutoTest.close()
                state.deviceBio24.close()
                
                
            else:
                event.ignore()
                if self.index_refreshing == 1:
                    self.DIGITAL_BOX_MAIN.start()

    def timerCreatePotDacTable(self):
        """
        run in timer set Dac and Pot table
        """
        self.createPotTable()
        self.thread_check_input.start(self.createDacTable)

    def showTime(self):
        """
        Show data/time on widget
        """
        self.time=QDateTime.currentDateTime()
        self.timeDisplay=self.time.toString('dd-MM-yyyy hh:mm:ss dddd')
        self.date_and_time.setText(self.timeDisplay)
        if  self.indexButtonSave == 1:
            if(self.index_extras[5] % 2) == 0:
                self.iconSaveData.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOn.png')))
                self.startStopSaving.setIcon(self.iconSaveData)
                #self.startStopSaving.setStyleSheet(ButtonStyleOn2)
            else:
                self.iconSaveData.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOn1.png')))
                self.startStopSaving.setIcon(self.iconSaveData)
                #self.startStopSaving.setStyleSheet(ButtonStyleOff2)
        self.index_extras[5] += 1
        if self.index_extras[5] >=2:
            self.index_extras[5] =0

    def timerDigitalBox(self):
        """
        Main timer
        """
        
        if self.digitalPotIndex == 0:
          
            tbegin = time()
            try:
                #self.time_show.start(self.showTime)
                self.check_output()
                self.set_voltage()
                self.set_pwm1()
                self.set_pwm2()
                self.set_frequency_and_duty_old()
                self.input_state_indicate()
                if not self.reading_inputs:  # the previous reading is still running -> skip this one
                    self.reading_inputs = True
                    self.thread_check_input.start(self.check_all_input)
                tend = time()
                print('time main box',int((tend-tbegin)*1000),'ms','interval:',state.MAIN_TIME_REFRESHING)
                
                # increase main time refreshing if function executing to long (but not without a limit)
                if  (tend-tbegin)*1000 >= state.MAIN_TIME_REFRESHING:
                    self.digitalPotChange = 1
                    state.MAIN_TIME_REFRESHING = min(state.MAIN_TIME_REFRESHING + 100, state.MAX_TIME_REFRESHING)
                    self.DIGITAL_BOX_MAIN.setInterval(state.MAIN_TIME_REFRESHING)
                # decrease main time refreshing if execute function is short
                else:
                    if (tend-tbegin)*1000 < state.MAIN_TIME_REFRESHING - 100:
                        self.DIGITAL_BOX_MAIN.setInterval(state.MAIN_TIME_REFRESHING)
                        state.MAIN_TIME_REFRESHING -= 100
                        self.digitalPotChange = 0
                
            # save value error to check_error.txt file
            except ValueError:
                x = datetime.datetime.now()
                dateAndTime = x.strftime("%c")
                with open('check_error.txt', 'a') as f:
                    f.write(f'{state.errorNumber}{dateAndTime}{state.errorNumber}\n')
                    f.write('!!! Can not set any parameters(set_voltage,set_pwm1,2...)!!!\n')
                    f.write('Solution:\n')
                    f.write(f'-- Check digital box version(RPI - {state.VERZIJA_RPI} ESP - {state.VERZIJA_ESP}) and\n')
                    f.write(f'{state.errorNumber*2}\n')
                    f.write(traceback.format_exc())
                    f.write(f'{state.errorNumber*2}\n')
                    f.close()
            except:
                with open('check_error.txt', 'a') as f:
                    f.write(traceback.format_exc())
                f.close()

    def setup_temperature_ramp(self):
        """Button that opens the temperature ramp (slider moves slowly from the start to the end temperature)."""
        self.rampButton = QPushButton('TEMP RAMP', self.content_widget)
        self.rampButton.setObjectName('rampButton')
        self.rampButton.setGeometry(440, 58, 86, 38)
        self.rampButton.show()
        self.rampButton.setStyleSheet(ButtonStyleOff2)
        self.rampDialog = TemperatureRampDialog(self)
        self.rampButton.clicked.connect(self.rampDialog.open_dialog)
        self.rampDialog.runningChanged.connect(
            lambda running: self.rampButton.setStyleSheet(ButtonStyleOn2 if running else ButtonStyleOff2))
        # REG TEMP: the slider moves up and down between two temperatures until it is stopped
        self.regButton = QPushButton('REG TEMP', self.content_widget)
        self.regButton.setObjectName('regButton')
        self.regButton.setGeometry(530, 58, 86, 38)
        self.regButton.show()
        self.regButton.setStyleSheet(ButtonStyleOff2)
        self.regDialog = TemperatureRegulationDialog(self)
        self.regButton.clicked.connect(self.regDialog.open_dialog)
        self.regDialog.runningChanged.connect(
            lambda running: self.regButton.setStyleSheet(ButtonStyleOn2 if running else ButtonStyleOff2))
        # TOGGLE OUTPUT: an output (or the ON/OFF button) is switched on and off again and again until it is stopped
        self.toggleButton = QPushButton('TOGGLE OUT', self.content_widget)
        self.toggleButton.setObjectName('toggleButton')
        self.toggleButton.setGeometry(895, 737, 90, 34)
        self.toggleButton.show()
        self.toggleButton.setStyleSheet(ButtonStyleOff2)
        self.toggleDialog = OutputToggleDialog(self)
        self.toggleButton.clicked.connect(self.toggleDialog.open_dialog)
        self.toggleDialog.runningChanged.connect(
            lambda running: self.toggleButton.setStyleSheet(ButtonStyleOn2 if running else ButtonStyleOff2))
        # SERVICES: opens the web page where the services of the box can be restarted after an error
        self.servicesButton = QPushButton('SERVICES', self.content_widget)
        self.servicesButton.setObjectName('servicesButton')
        self.servicesButton.setGeometry(1415, 106, 111, 30)
        self.servicesButton.setToolTip('Choose the box and open its page (restart the services after an error)')
        self.servicesButton.show()
        self.servicesButton.setStyleSheet(ButtonStyleOff2)
        self.servicesButton.clicked.connect(self.open_services)

    def open_services(self):
        """Ask which box (the scanned ones, the connected one is preselected; an IP can be typed too) and open
        the page for restarting its services in the browser."""
        settings = QSettings('DigitalBox', 'BOX_GUI')
        boxes = {}  # list text -> ip
        for index in range(self.BoxConnect.count()):
            ip = self.BoxConnect.itemData(index)
            if isinstance(ip, str) and ip:
                boxes[self.BoxConnect.itemText(index)] = ip
        last_ip = str(settings.value('services_ip', SERVICES_DEFAULT_IP))
        if last_ip not in boxes.values():
            boxes[last_ip] = last_ip
        current = str(getattr(self, 'Connection', ''))
        names = list(boxes)
        start = names.index(current) if current in boxes else next(
            (position for position, name in enumerate(names) if boxes[name] == last_ip), 0)
        dialog = QInputDialog(self)
        dialog.setWindowTitle('SERVICES')
        dialog.setLabelText('Choose the box or type its IP:')
        dialog.setComboBoxItems(names)
        dialog.setComboBoxEditable(True)
        dialog.setTextValue(names[start])
        if compact_layout_wanted():
            enlarge_dialog(dialog)
        if dialog.exec() != QInputDialog.DialogCode.Accepted:
            return
        choice = dialog.textValue()
        ip = boxes.get(choice, choice).strip()
        try:
            ip = str(ipaddress.ip_address(ip))
        except ValueError:
            QMessageBox.warning(self, 'SERVICES', f'"{ip}" is not a valid IP address.')
            return
        settings.setValue('services_ip', ip)
        url = f'http://{ip}:{SERVICES_PORT}/'
        if not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.warning(self, 'SERVICES', f'The browser could not be opened.\n\n{url}')

    def setup_theme_button(self):
        """Button for switching between the light and the dark theme (choice is remembered)."""
        self.themeButton = QPushButton(self.content_widget)
        self.themeButton.setObjectName('themeButton')
        self.themeButton.setGeometry(1415, 160, 111, 38)
        self.themeButton.show()
        self.themeButton.setStyleSheet(ButtonStyleOff2)
        self.themeButton.clicked.connect(self.toggle_theme)
        self.update_theme_button()

    def toggle_theme(self):
        apply_theme("light" if saved_theme() == "dark" else "dark")
        self.update_theme_button()

    def update_theme_button(self):
        self.themeButton.setText("Light theme" if saved_theme() == "dark" else "Dark theme")

    def boxMarks(self,BOXMARKS):
        """
        load the box marks data/boxMarks/<name>.json and write its names to the GUI
        """
        try:
            data = load_box_mark(BOXMARKS)
            self.BoxMarks.setStyleSheet(ButtonStyleOn)
            self.box_mark_data = data
            self.session_box_mark = BOXMARKS
            self.heater_systems = load_heater_systems(BOXMARKS)
            self.show_detected_heaters([])
            for auto_index in range(1, 5):
                self.index_auto[auto_index - 1] = 0
                setattr(self, f'param_auto{auto_index}', 0)
                button = getattr(self, f'AUTO{auto_index}')
                button.setText(f'AUTO{auto_index}')
                button.setStyleSheet(ButtonStyleOff2)
                button.setEnabled(False)
            self.save_session()
            self.io_show_all = False
            self.active_pots = None
            self.update_digital_pot_visibility()
            if 'INPUT' in data:
                for index in range(state.DigitalInput):
                    getattr(self, f'INPUT_{index}').setText(box_mark_name(data, 'INPUT', index, f'IN{index}'))
            if 'OUTPUT' in data:
                for index in range(16):
                    getattr(self, f'OUT{index}').setText(box_mark_name(data, 'OUTPUT', index, f'out{index}'))
            if 'DIGITAL_POT' in data:
                pot_names = data['DIGITAL_POT']
                self.active_pots = [index for index in range(6) if index < len(pot_names) and pot_names[index]]
                self.update_digital_pot_visibility()
                try:
                    for index in range(6):
                        label = getattr(self, f'labelDigitalPot{index}')
                        label.setText(box_mark_name(data, 'DIGITAL_POT', index, f'digitalPot{index}'))
                        label.setFont(QFont('Arial', 10))
                except AttributeError:
                    print('!!! POT not enough slider !!!')
            if 'DAC_POT' in data:
                try:
                    for index in range(8):
                        label = getattr(state.SetDacValue, f'labelDac{index}')
                        label.setText(box_mark_name(data, 'DAC_POT', index, f'Table{index}'))
                        label.setFont(QFont('Arial', 10))
                except AttributeError:
                    print('!!! DAC not enough slider !!!')
            for section, label_name, default, count in (('READ_ADC', 'labelADC', 'ADC', 4),
                                                        ('SET_VOLTAGE', 'labelSetVoltage', 'VOLTAGE', 4)):
                if section in data:
                    for index in range(count):
                        label = getattr(self, f'{label_name}{index}')
                        label.setText(box_mark_name(data, section, index, f'{default}{index}'))
                        label.setFont(QFont('Arial', 10))
            for section, label_name in (('READ_PWM1', 'labelPwm1_'), ('READ_PWM2', 'labelPwm2_'),
                                        ('SET_PWM1', 'labelSetPwm1_'), ('SET_PWM2', 'labelSetPwm2_')):
                if section in data:
                    for index in range(2):
                        label = getattr(self, f'{label_name}{index}')
                        label.setText(box_mark_name(data, section, index, label.text()))
                        label.setFont(QFont('Arial', 10))
            for section, label_name in (('SET_FREQ', 'labelSetPwm3_0'), ('SET_DUTY', 'labelSetPwm3_1')):
                if section in data:
                    label = getattr(self, label_name)
                    label.setText(data[section])
                    label.setFont(QFont('Arial', 10))
            for auto_index in range(1, 5):
                params = data.get(f'AUTO{auto_index}')
                if params:
                    setattr(self, f'param_auto{auto_index}', params)
                    button = getattr(self, f'AUTO{auto_index}')
                    button.setText(params[0])
                    button.setFont(QFont('Arial', 10))
                    button.setEnabled(len(params) >= 4 and params[1].isdigit() and params[2].isdigit())
            self.apply_box_mark_labels(data.get('LABELS', {}))
            self.update_digital_pot_visibility()  # shows only the inputs/outputs/sliders with a name
        except (IndexError, ValueError):
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{state.errorNumber}{dateAndTime}{state.errorNumber}\n')
                f.write('!!!Box marks file is not valid!!!\n')
                f.write('Solution:\n')
                f.write(f'-- Check data/boxMarks/{BOXMARKS}.json file and do as instructed(check readMe.txt file) \n')
                f.write(f'{state.errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{state.errorNumber*2}\n')
        except:
            with open('check_error.txt', 'a') as f:
                f.write(traceback.format_exc())

    def buttonHusaModel(self):
        """
        - show screen husa if box is connected
        - if box is not connected show massage error
        """
        if self.index_refreshing >= 1:
            if (self.index_extras[0] % 2) == 0:
                self.ButtonHusaModel.setStyleSheet(ButtonStyleOn2)
                state.HusaModelWindow.show()
            else: 
                self.ButtonHusaModel.setStyleSheet(ButtonStyleOff2)
                state.HusaModelWindow.close()
        else:
            self.warningMessageAddFunction.setStyleSheet("color: red")
            self.warningMessageAddFunction.setText("!!! CONNECT DIGITAL BOX !!!") 
            self.ButtonHusaModel.setStyleSheet(ButtonStyleOff2)
        self.index_extras[0] +=1
        if self.index_extras[0] >=2:
            self.index_extras[0] =0

    def updateGui(self):
        """Check GitHub for updates and update application."""
        from .simple_update import check_github_updates
        check_github_updates(self, current_version="5.3.0")

    def perform_github_update(self, update_info: dict):
        """Download and apply update from GitHub."""
        from .simple_update import download_and_update
        from pathlib import Path

        download_url = update_info.get("download_url")
        if not download_url:
            QMessageBox.warning(self, "Error", "No download URL found")
            return

        # Close all windows
        self.indexUpdate = 1
        state.mainWindow.close()
        state.HusaModelWindow.close()
        state.deviceG800.close()
        state.PyroSetSystem.close()
        state.SetDacValue.close()
        state.PotTableSet.close()
        state.DacTableCreate.close()
        state.RunAutoTest.close()
        state.deviceBio24.close()

        # Download and update
        exe_path = Path(sys.executable)
        if download_and_update(download_url, exe_path):
            # Restart application
            subprocess.Popen([str(exe_path)])
            sys.exit(0)
        else:
            QMessageBox.critical(self, "Update Failed", "Could not download update")

    def buttonG800(self):
        """
        - show screen G800 
        """
        if (self.index_extras[8] % 2) == 0:
            self.ButtonG800.setStyleSheet(ButtonStyleOn2)
            state.deviceG800.show()
        else: 
            self.ButtonG800.setStyleSheet(ButtonStyleOff2)
            state.deviceG800.close()
        self.index_extras[8] +=1
     
        if self.index_extras[8] >=2:
            self.index_extras[8] =0

    def buttonBio24(self):
        """
        - show screen Bio24 
        """
        if (self.index_extras[9] % 2) == 0:
            self.ButtonBIO24.setStyleSheet(ButtonStyleOn2)
            state.deviceBio24.show()
        else: 
            self.ButtonBIO24.setStyleSheet(ButtonStyleOff2)
            state.deviceBio24.close()
        self.index_extras[9] +=1
     
        if self.index_extras[9] >=2:
            self.index_extras[9] =0

    def closeScreenBio24(self):
        """
        close G800 close
        """
        self.index_extras[9] +=1
        self.ButtonBIO24.setStyleSheet(ButtonStyleOff2)

    def closeScreenG800(self):
        """
        close G800 close
        """
        self.index_extras[8] +=1
        self.ButtonG800.setStyleSheet(ButtonStyleOff2)

    def closeHusaScreen(self):
        """
        close husa screen
        """
        self.index_extras[0] +=1
        self.ButtonHusaModel.setStyleSheet(ButtonStyleOff2)

    def buttonPyroSystem(self):
        """
        - show screen pyro system if box is connected
        - if box is not connected show massage error
        """
        if self.index_refreshing >= 1:
            if (self.index_extras[1] % 2) == 0:
                self.ButtonPyroSystem.setStyleSheet(ButtonStyleOn2)
                state.PyroSetSystem.show()
            else: 
                self.ButtonPyroSystem.setStyleSheet(ButtonStyleOff2)
                state.PyroSetSystem.close()
        else:
            self.warningMessageAddFunction.setStyleSheet("color: red")
            self.warningMessageAddFunction.setText("!!! CONNECT DIGITAL BOX !!!") 
            self.ButtonPyroSystem.setStyleSheet(ButtonStyleOff2)
            
        self.index_extras[1] +=1
        if self.index_extras[1] >=2:
            self.index_extras[1] =0

    def closePyroScreen(self):
        """
        close pyro screen
        """
        self.index_extras[1] +=1
        self.ButtonPyroSystem.setStyleSheet(ButtonStyleOff2)

    def buttonDacSet(self):
        """
        show dac set screen
        """
        if (self.index_extras[2] % 2) == 0:
            
            self.ButtonDacSet.setStyleSheet(ButtonStyleOn2)
            state.SetDacValue.show()
        else:
            self.ButtonDacSet.setStyleSheet(ButtonStyleOff2)
            state.SetDacValue.close()
            
        self.index_extras[2] +=1
        if self.index_extras[2] >=2:
            self.index_extras[2] =0

    def closeDacScreen(self):
        """
        close dac screen
        """
        self.index_extras[2] +=1
        self.ButtonDacSet.setStyleSheet(ButtonStyleOff2)

    def husaAutoSetModule(self,model_set):
        """
        avto set PB and LB model
        """
        self.digitalPotIndex = 1
        sleep(1)
        model_PB,model_LB=select_model(self,model_set)
        sleep(0.2)
        self.box.main = 0
        self.index_on_off = 0
        sleep(3)
        self.box.main = 1
        self.index_on_off = 1
        sleep(1)
        self.digitalPotIndex = 0
        return model_PB,model_LB

    def husaSetLBModule(self,LB_model_set):
        """
        set LB model
        
        """
        self.digitalPotIndex = 1
        sleep(1)
        select_model_LB(self,LB_model_set)
        sleep(0.2)
        self.box.main = 0
        self.index_on_off = 0
        sleep(3)
        self.box.main = 1
        self.index_on_off = 1
        sleep(1)
        self.digitalPotIndex = 0

    def pyroSetSystem(self,system):
        """
        select system with digital output
        """
        self.digitalPotIndex = 1
        sleep(1)
        select_system(self,system)
        sleep(1)
        self.digitalPotIndex = 0

    def buttonSetPot(self):
        """
        - show screen set pot if box is connected
        - show error message if box is not connected
        - stop the timer
        """
        
        if self.index_refreshing >= 1:
            if (self.index_extras[3] % 2) == 0:
                self.labelTableOpenError.setText("!!! CREATE POT TABLE IS OPEN. GUI STOPPED!!!")
                self.labelTableOpenError.setVisible(True)
                self.ButtonSetPot.setStyleSheet(ButtonStyleOn2)
                state.PotTableSet.show()
                self.DIGITAL_BOX_MAIN.stop()
                self.DIGITAL_BOX_MAIN.setInterval(1000)
                self.ReadSetPotDac.start()
                
            else: 
                self.labelTableOpenError.setVisible(False)
                self.ButtonSetPot.setStyleSheet(ButtonStyleOff2)
                state.PotTableSet.close()
                self.ReadSetPotDac.stop()
                self.DIGITAL_BOX_MAIN.start()
        else:
            self.warningMessagePot.setVisible(True)
            self.warningMessagePot.setText("!!! CONNECT DIGITAL BOX !!!") 
            self.ButtonSetPot.setStyleSheet(ButtonStyleOff2)
            
        self.index_extras[3] +=1
        if self.index_extras[3] >=2:
            self.index_extras[3] =0

    def closePotTable(self):
        """
        close screen pot table and start the timer
        """
        self.index_extras[3] +=1
        self.ButtonSetPot.setStyleSheet(ButtonStyleOff2)
        self.ReadSetPotDac.stop()
        self.DIGITAL_BOX_MAIN.start()
        self.labelTableOpenError.setVisible(False)

    def buttonSetDac(self):
        """
        - if box is connected show dac table create
        - stop box timer(DIGITAL BOX MAIN) and start readSetPotDac timer
        - show error message if box is not connected
        """
        if self.index_refreshing >= 1:
            if (self.index_extras[4] % 2) == 0:
                self.labelTableOpenError.setText("!!! CREATE DAC TABLE IS OPEN. GUI STOPPED!!!")
                self.labelTableOpenError.setVisible(True)
                self.ButtonSetDac.setStyleSheet(ButtonStyleOn2)
                state.DacTableCreate.show()
                self.DIGITAL_BOX_MAIN.stop()
                self.DIGITAL_BOX_MAIN.setInterval(1000)
                self.ReadSetPotDac.start()
                
            else:
                self.labelTableOpenError.setVisible(False)
                self.ButtonSetDac.setStyleSheet(ButtonStyleOff2)
                state.DacTableCreate.close()
                self.ReadSetPotDac.stop()
                self.DIGITAL_BOX_MAIN.start()
        else:
            self.warningMessageDac.setVisible(True)
            self.warningMessageDac.setText("!!! CONNECT DIGITAL BOX !!!") 
            self.ButtonSetDac.setStyleSheet(ButtonStyleOff2)
                
        self.index_extras[4] +=1
        if self.index_extras[4] >=2:
            self.index_extras[4] =0

    def closeDacTable(self):
        """
        - close screen dac table 
        - stop readSetPotDac timer 
        - start main box timer(DIGITAL_BOX_MAIN)
        """
        self.index_extras[4] +=1
        self.ButtonSetDac.setStyleSheet(ButtonStyleOff2)
        self.ReadSetPotDac.stop()
        self.DIGITAL_BOX_MAIN.start()
        self.labelTableOpenError.setVisible(False)

    def buttonAutomation(self):
   
        if self.index_extras[6]  == 0:
            self.SetEnvirement.setVisible(True)
            self.setEnvironmentText.setVisible(True)
        elif self.index_extras[6]  == 1:
            self.SetEnvirement.setVisible(False)
            self.setEnvironmentText.setVisible(False)
            if os.name == "nt":
                subprocess.Popen(f"conda activate {self.SetEnvirement.text()} && python -m tester.executables.test", shell=True)
            else:
                subprocess.Popen(["bash", "-ic", f"conda activate {shlex.quote(self.SetEnvirement.text())} && python -m tester.executables.test"])
            self.barOpenAutoTest.setVisible(True)
            for number in range(0,100,5):
                self.barOpenAutoTest.setValue(number)
                sleep(0.2)
            self.barOpenAutoTest.setVisible(False)
            self.ButtonAutomation.setStyleSheet(ButtonStyleOn2)
        else:
            self.ButtonAutomation.setStyleSheet(ButtonStyleOff2)
            #self.pQ.kill()
        self.index_extras[6] +=1
        if self.index_extras[6] >=3:
            self.index_extras[6] =0

    def buttonCreateAutoTest(self):
        if self.index_extras[7]  == 0:
            self.ButtonCreateAutoTest.setStyleSheet(ButtonStyleOn2)
            state.RunAutoTest.show()
        else:
            self.ButtonCreateAutoTest.setStyleSheet(ButtonStyleOff2)
            state.RunAutoTest.close()
        self.index_extras[7] +=1
        if self.index_extras[7] >=2:
            self.index_extras[7] =0

    def closeRunAutoTest(self):
        """
        - close screen closeRunAutoTest
        """
        self.index_extras[6] +=1
        self.ButtonCreateAutoTest.setStyleSheet(ButtonStyleOff2)
