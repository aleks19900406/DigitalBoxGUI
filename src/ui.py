import datetime
import os
import subprocess
import traceback
from pathlib import Path
from time import sleep, time
from PyQt5 import QtGui
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.uic import loadUi
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from DigitalBox.lib import *
from . import state
from .paths import BOX_MARKS_PATH, DATA_SAVE, IMAGE_PATH_OTHER, OVEN_DEVICE_CONNECT_PATHS, QT_DESIGNER
from .styles import ButtonStyleOff2, ButtonStyleOn, ButtonStyleOn2, ButtonStyleWhite, MainScreenStyle
from .workers import Worker
from .devices import listConnection
from .helpers import dataFile, listBoxMarks, listDigitalPotTable
from .connections import ConnectionMixin
from .saving import SavingMixin
from .digital_controls import DigitalControlsMixin
from .analog_controls import AnalogControlsMixin


class MainWindow(ConnectionMixin, SavingMixin, DigitalControlsMixin, AnalogControlsMixin, QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.signal_on = [0] * count
        self.signal_off = [0] * count
        self.periode = [0] * count
        self.current_output = [None] * count
        self.output_start = [None] * count
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
        self.setWindowTitle(f'DIGITAL BOX MAIN {state.DIGITAL_BOX_VERSION}')
        self.setGeometry(150, 40, 1530, 1050)
        #self.setSizeIncrement(1920, 1080)
        self.setStyleSheet(MainScreenStyle)
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
        #######################AUTO BUTTON #######################################
        self.AUTO1.clicked.connect(self.buttonAuto1)
        self.AUTO2.clicked.connect(self.buttonAuto2)
        self.AUTO3.clicked.connect(self.buttonAuto3)
        self.AUTO4.clicked.connect(self.buttonAuto4)
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
        self.BoxConnect.activated[str].connect(self.connectBox)
        self.BoxConnect.setEditable(True)
        self.BoxConnect.setStyleSheet(ButtonStyleWhite)
        self.BoxMarks.activated[str].connect(self.boxMarks)
        self.BoxMarks.setEditable(True)
        self.BoxMarks.setStyleSheet(ButtonStyleWhite)
        self.SelectPotTable.activated[str].connect(self.digitalPotTable)
        self.SelectPotTable.setEditable(True)
        self.SelectPotTable.setStyleSheet(ButtonStyleWhite)
        self.BoxMarks.addItems(listBoxMarks())
        self.SelectPotTable.addItems(listDigitalPotTable())
        self.AllTable = listDigitalPotTable()
        self.ExcelFile.addItems(dataFile())
        ##################### SAVE DATA ##########################################
        self.ExcelFile.activated[str].connect(self.excelFile)
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
            close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            close = close.exec()
            if  close == QMessageBox.Yes:
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
                self.thread_check_input.start(self.check_all_input)
                tend = time()
                print('time main box',int((tend-tbegin)*1000),'ms','interval:',state.MAIN_TIME_REFRESHING)
                
                # increase main time refreshing if function executing to long
                if  (tend-tbegin)*1000 >= state.MAIN_TIME_REFRESHING:
                    self.digitalPotChange = 1
                    state.MAIN_TIME_REFRESHING += 100
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

    def boxMarks(self,BOXMARKS):
        """
        open folder in data/boxMarks and get all marks name
        """
        try:
            BOX_MARKS = open(f"{BOX_MARKS_PATH}/{BOXMARKS}.txt", "r")
            self.BoxMarks.setStyleSheet(ButtonStyleOn)
            self.read_all_lines=BOX_MARKS.readlines()
            for name in self.read_all_lines:
                if name == f'INPUT{state.SPACE}':
                    try:
                        for index in range(state.DigitalInput):
                            input_text = eval(f'self.INPUT_{index}')
                            if self.read_all_lines[1].replace('\n','').split(',')[index] == '':
                                input_text.setText(f'IN{index}')
                            else:
                                input_text.setText(self.read_all_lines[1].replace('\n','').split(',')[index])
                    except IndexError:
                        input_text.setText(f'IN{index}')
                        
                if name == f'OUTPUT{state.SPACE}':
                    try:
                        for index in range(16):
                            output_text = eval(f'self.OUT{index}')
                            if self.read_all_lines[3].replace('\n','').split(',')[index] == '':
                                output_text.setText(f'out{index}')
                            else:
                                output_text.setText(self.read_all_lines[3].replace('\n','').split(',')[index])
                    except IndexError:
                        output_text.setText(f'out{index}')
                
                if name == f'DIGITAL_POT{state.SPACE}':
                    try:
                        for index in range(6):
                            digital_pot_text = eval(f'self.labelDigitalPot{index}')
                            if self.read_all_lines[5].replace('\n','').split(',')[index] == '':
                                digital_pot_text.setText(f'digitalPot{index}')
                            else:
                                digital_pot_text.setText(self.read_all_lines[5].replace('\n','').split(',')[index])
                            digital_pot_text.setFont(QFont('Arial', 10))
                    except IndexError:
                        digital_pot_text.setText(f'digitalPot{index}')
                    except AttributeError:
                        print('!!! POT not enough slider !!!')
                
                if name == f'DAC_POT{state.SPACE}':
                    try:
                        for index in range(8):
                            digital_pot_text = eval(f'state.SetDacValue.labelDac{index}')
                            if self.read_all_lines[7].replace('\n','').split(',')[index] == '':
                                digital_pot_text.setText(f'Table{index}')
                            else:
                                digital_pot_text.setText(self.read_all_lines[7].replace('\n','').split(',')[index])
                            digital_pot_text.setFont(QFont('Arial', 10))
                    except IndexError:
                        digital_pot_text.setText(f'Table{index}')
                    except AttributeError:
                        print('!!! DAC not enough slider !!!')
                
                if name == f'READ_ADC{state.SPACE}':
                    try:
                        for index in range(4):
                            digital_pot_text = eval(f'self.labelADC{index}')
                            if self.read_all_lines[9].replace('\n','').split(',')[index] == '':
                                digital_pot_text.setText(f'ADC{index}')
                            else:
                                digital_pot_text.setText(self.read_all_lines[9].replace('\n','').split(',')[index])
                            digital_pot_text.setFont(QFont('Arial', 10))
                    except IndexError:
                        digital_pot_text.setText(f'ADC{index}')
                
                if name == f'SET_VOLTAGE{state.SPACE}':
                    try:
                        for index in range(4):
                            digital_pot_text = eval(f'self.labelSetVoltage{index}')
                            if self.read_all_lines[11].replace('\n','').split(',')[index] == '':
                                digital_pot_text.setText(f'VOLTAGE{index}')
                            else:    
                                digital_pot_text.setText(self.read_all_lines[11].replace('\n','').split(',')[index])
                            digital_pot_text.setFont(QFont('Arial', 10))
                    except IndexError:
                        digital_pot_text.setText(f'VOLTAGE{index}')
            
                if name == f'READ_PWM1{state.SPACE}':
                    for index in range(2):
                        digital_pot_text = eval(f'self.labelPwm1_{index}')
                        digital_pot_text.setText(self.read_all_lines[13].replace('\n','').split(',')[index])
                        digital_pot_text.setFont(QFont('Arial', 10))
                
                if name == f'READ_PWM2{state.SPACE}':
                    for index in range(2):
                        digital_pot_text = eval(f'self.labelPwm2_{index}')
                        digital_pot_text.setText(self.read_all_lines[15].replace('\n','').split(',')[index])
                        digital_pot_text.setFont(QFont('Arial', 10)) 
            
                if name == f'SET_PWM1{state.SPACE}':
                    for index in range(2):
                        digital_pot_text = eval(f'self.labelSetPwm1_{index}')
                        digital_pot_text.setText(self.read_all_lines[17].replace('\n','').split(',')[index])
                        digital_pot_text.setFont(QFont('Arial', 10))  
                
                if name == f'SET_PWM2{state.SPACE}':
                    for index in range(2):
                        digital_pot_text = eval(f'self.labelSetPwm2_{index}')
                        digital_pot_text.setText(self.read_all_lines[19].replace('\n','').split(',')[index])
                        digital_pot_text.setFont(QFont('Arial', 10))
                if name == f'SET_FREQ{state.SPACE}':
                        digital_pot_text = eval('self.labelSetPwm3_0')
                        digital_pot_text.setText(self.read_all_lines[21].replace('\n',''))
                        digital_pot_text.setFont(QFont('Arial', 10))
                if name == f'SET_DUTY{state.SPACE}':
                        digital_pot_text = eval('self.labelSetPwm3_1')
                        digital_pot_text.setText(self.read_all_lines[23].replace('\n',''))
                        digital_pot_text.setFont(QFont('Arial', 10))
                if name == f'AUTO1{state.SPACE}':
                    self.param_auto1 = self.read_all_lines[25].replace('\n','').split(',')
                    digital_pot_text = eval('self.AUTO1')
                    digital_pot_text.setText(self.param_auto1[0])
                    digital_pot_text.setFont(QFont('Arial', 10))
                if name == f'AUTO2{state.SPACE}':
                    self.param_auto2 = self.read_all_lines[27].replace('\n','').split(',')
                    digital_pot_text = eval('self.AUTO2')
                    digital_pot_text.setText(self.param_auto2[0])
                    digital_pot_text.setFont(QFont('Arial', 10))
                if name == f'AUTO3{state.SPACE}':
                    self.param_auto3 = self.read_all_lines[29].replace('\n','').split(',')
                    digital_pot_text = eval('self.AUTO3')
                    digital_pot_text.setText(self.param_auto3[0])
                    digital_pot_text.setFont(QFont('Arial', 10))
                if name == f'AUTO4{state.SPACE}':
                    self.param_auto4 = self.read_all_lines[31].replace('\n','').split(',')
                    digital_pot_text = eval('self.AUTO4')
                    digital_pot_text.setText(self.param_auto4[0])
                    digital_pot_text.setFont(QFont('Arial', 10))
        except IndexError:
            
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{state.errorNumber}{dateAndTime}{state.errorNumber}\n')
                f.write('!!!Some name(INPUT,OUTPUT,DIGITAL_POT,...) do not have arguments!!!\n')
                f.write('Solution:\n')
                f.write(f'-- Check data/{BOXMARKS}.txt file and do as instructed(check readMe.txt file) \n')
                f.write(f'{state.errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{state.errorNumber*2}\n')
            f.close()
        
        except:
                with open('check_error.txt', 'a') as f:
                    f.write(traceback.format_exc())
                f.close()

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
        update = QMessageBox()
        update.setText("Confirm GUI update ?")
        update.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        response = update.exec()
        if response == QMessageBox.Yes:
            #close all screen if main app close
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
            command = 'update.exe'
            # Run the script
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

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
            subprocess.Popen(f"conda activate {self.SetEnvirement.text()} && python -m tester.executables.test", shell=True)
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
