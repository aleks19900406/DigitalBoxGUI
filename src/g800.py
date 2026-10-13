import datetime
import traceback
from pathlib import Path
from time import sleep
from PyQt5.QtWidgets import QMainWindow
from PyQt5.uic import loadUi
from DigitalBox.Connection import G800, data
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from DigitalBox.lib import *
from . import state
from .paths import QT_DESIGNER
from .styles import ButtonStyleOff2, ButtonStyleOn, ButtonStyleWhite
from .devices import listDeviceConnection
from .helpers import listLanguages


class DeviceG800(QMainWindow):
    def __init__(self):
        super().__init__()
        ########################## SCREEN PATH CONVERT #############################
        self.connected = 0
        self.counter = 0
        DacTable = QT_DESIGNER / 'H800.ui'
        loadUi(str(DacTable), self)
        self.setWindowTitle("H800")
        self.setFixedSize(700, 440)
        self.device_connect.setText('DEVICE CONNECT:')
        self.device_connect.setStyleSheet("color: gray")
        self.setLanguage.activated[str].connect(self.setlanguage)
        self.setLanguage.setStyleSheet(ButtonStyleWhite)
        self.setLanguage.setEnabled(False)
        self.setLanguage.addItems(listLanguages())
        # Create a QTextCursor object
        self.deviceDisconnect.clicked.connect(self.disconnectAll)
        self.deviceDisconnect.setStyleSheet(ButtonStyleOff2)
        self.button_production.pressed.connect(self.enter_production)
        self.button_production.setStyleSheet(ButtonStyleOff2)
        self.button_touch_all.pressed.connect(self.touch_test)
        self.button_touch_all.setStyleSheet(ButtonStyleOff2)
        self.button_agging.pressed.connect(self.agging_mode)
        self.button_agging.setStyleSheet(ButtonStyleOff2)
        self.button_demo.pressed.connect(self.demo_mode)
        self.button_demo.setStyleSheet(ButtonStyleOff2)
        self.button_reset.pressed.connect(self.reset)
        self.button_reset.setStyleSheet(ButtonStyleOff2)
        self.reset_lang.pressed.connect(self.resetLang)
        self.reset_lang.setStyleSheet(ButtonStyleOff2)
        self.reset_auto_button.pressed.connect(self.resetButton)
        self.reset_auto_button.setStyleSheet(ButtonStyleOff2)
        self.AutoLanguage = QTimer()
        self.AutoLanguage.timeout.connect(self.change_lang)  # 
        self.AutoLanguage.setInterval(state.MAIN_TIME_REFRESHING)
        self.AutoButton = QTimer()
        self.AutoButton.timeout.connect(self.timer_button)  # 
        self.AutoButton.setInterval(state.MAIN_TIME_REFRESHING)
        self.buttonAutoThread = QThreadPool()
        self.checkBox_auto_lang.stateChanged.connect(self.doCheck)
        self.checkBox_button_click.stateChanged.connect(self.doAutoButton)
        self.DeviceConnect.activated[str].connect(self.deviceBox)
        self.DeviceConnect.setEditable(True)
        self.DeviceConnect.setStyleSheet(ButtonStyleWhite)
        self.DeviceConnect.addItems(listDeviceConnection())
        self.data = data
        self.get_model_index = 0
        self.steam_button_index = 0
        self.steam_log_ON = 0
        self.activate_button_index = 0
        self.time_lang_change = 1000
        self.lang_index = 0
        self.lang_max_index = 0
        self.saveButtonPush = []
         ################## DIGITAL OUTPUT #########################################
        self.button_production.setEnabled(False)  
        self.button_touch_all.setEnabled(False)  
        self.button_agging.setEnabled(False)  
        self.button_demo.setEnabled(False)  
        self.button_reset.setEnabled(False)
    
        for index in range(22):
            eval(f'self.buttonT{index}.pressed.connect(self.button_clicked)')
            eval(f'self.buttonT{index}.setStyleSheet(ButtonStyleOff2)')
            eval(f'self.buttonT{index}.setEnabled(False)')
    
    def resetLang(self):
        self.setLanguage.clear()
        self.setLanguage.addItems(listLanguages())
    
    def resetButton(self):
        self.saveButtonPush.clear()
        self.textButton.clear()
    
    def doCheck(self):
        if self.checkBox_auto_lang.isChecked():
            # Checkbox is checked
            self.lang_max_index = max([index for index,i in enumerate(state.ALL_LANGUAGES)])
            self.AutoLanguage.start()
        else:
            self.AutoLanguage.stop()
    
    def doAutoButton(self):
        if self.checkBox_button_click.isChecked():
            # Checkbox is checked
            self.AutoButton.start()
        else:
            self.AutoButton.stop()
    
    def change_lang(self):
        self.setLanguage.clear()
        if self.lang_index == self.lang_max_index + 1:
            self.lang_index = 0
        if self.time_lang_change != self.change_language_time.value():
            self.time_lang_change = self.change_language_time.value()
            self.AutoLanguage.setInterval(int(self.change_language_time.value()*1000))
        self.device.change_language(self.lang_index)
        lang_name =''.join([i for index,i in enumerate(state.ALL_LANGUAGES) if index == self.lang_index])
        self.setLanguage.addItem(lang_name)
        self.lang_index += 1
    
    def timer_button(self):
        try:
            self.device.button_ESP(index=self.saveButtonPush[self.counter])
            self.AutoButton.setInterval(int(self.change_button_push_time.value()*1000))
            self.counter += 1
        except IndexError:
            self.counter = 0
        
    def button_clicked(self):
        self.counter += 1
        sender = int(self.sender().text().replace('T',''))
        self.saveButtonPush.append(sender)
        self.textButton.setText(f'{self.saveButtonPush}')
        self.device.button_ESP(index=sender)
    
    def enter_production(self):
        self.device.disconnectESP()
        self.device.connectESP()
        sleep(7)
        self.device.button_ESP(0)
        sleep(1)
        self.device.button_ESP(1)
        self.device.button_ESP(4)
        self.device.button_ESP(5)

    def touch_test(self):
        self.device.button_ESP(16)
        sleep(1)
        for index in range(22):
            self.device.button_ESP(index)
            sleep(0.2)
    
    def agging_mode(self):
        self.device.disconnectESP()
        self.device.connectESP()
        sleep(7)
        self.device.button_ESP(0)
        sleep(1)
        self.device.button_ESP(8)
        self.device.button_ESP(1)
        self.device.button_ESP(4)
    
    def demo_mode(self):
        self.device.disconnectESP()
        self.device.connectESP()
        sleep(7)
        self.device.button_ESP(0)
        sleep(1)
        self.device.button_ESP(1)
        self.device.button_ESP(5)
        self.device.button_ESP(9)

    def reset(self):
        self.device.disconnectESP()
        self.device.connectESP()

    def deviceBox(self, CONNECTBOX):
        """
        - connect device G800
        - show warning message if device is disconnected
        """
        try:
            if CONNECTBOX[0:3] =='COM':
                print('ok',CONNECTBOX[0:5].replace(' ',''))
                self.device = G800(CONNECTBOX[0:5].replace(' ',''),baudrate=1000000)
                self.device.connectESP()
                self.connected = 1
                sleep(1)
                self.device_connect.setText('CONNECT:')
                self.device_connect.setStyleSheet("color: green")
                self.DeviceConnect.setStyleSheet(ButtonStyleOn)
                self.DeviceConnect.setEnabled(False)
                self.setLanguage.setEnabled(True)
                     
                for index in range(22):
                    eval(f'self.buttonT{index}.setEnabled(True)')
                self.button_production.setEnabled(True)  
                self.button_touch_all.setEnabled(True)  
                self.button_agging.setEnabled(True)  
                self.button_demo.setEnabled(True)  
                self.button_reset.setEnabled(True)   
            else:
                sleep(2)
                self.device_connect.setText('DEVICE DISCONNECTED:')
                self.device_connect.setStyleSheet("color: red")
                self.connected = 0
                self.device.disconnectESP()
        except:
            self.device.disconnectESP()
            self.device_connect.setText('DEVICE DISCONNECTED:')
            self.device_connect.setStyleSheet("color: red")
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{state.errorNumber}{dateAndTime}{state.errorNumber}\n')
                f.write('Device is not conncected \n')
                f.write('Solution:\n')
                f.write('-- Connenct to the correct comport !!!\n')
                f.write(f'{state.errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{state.errorNumber*2}\n')
            f.close()
        
    def disconnectAll(self):
        self.AutoLanguage.stop()
        self.setLanguage.clear()
        self.saveButtonPush.clear()
        self.AutoButton.stop()
        self.setLanguage.addItems(listLanguages())
        sleep(1)
        self.device_connect.setText('DEVICE CONNECT:')
        self.device_connect.setStyleSheet("color: gray")
        self.DeviceConnect.setEnabled(True)
        self.setLanguage.setEnabled(False)
        for index in range(22):
            eval(f'self.buttonT{index}.setEnabled(False)')
        self.button_production.setEnabled(False)  
        self.button_touch_all.setEnabled(False)  
        self.button_agging.setEnabled(False)  
        self.button_demo.setEnabled(False)  
        self.button_reset.setEnabled(False)   
        self.DeviceConnect.setStyleSheet(ButtonStyleOff2)
        self.setLanguage.setStyleSheet(ButtonStyleOff2)
        self.DeviceConnect.clear()
        self.DeviceConnect.addItems(listDeviceConnection())
        if self.connected == 1:
            self.connected = 0
            self.device.disconnectESP()
    
    def setlanguage(self,lang):
        self.device.change_language(self.setLanguage.currentIndex())
        self.setLanguage.setStyleSheet(ButtonStyleOn)
        
    def boxOffDeviceDisconnected(self):
        if self.connected == 1:
            self.device.disconnectESP()
            self.DeviceConnect.setEnabled(False)
            self.setLanguage.setEnabled(False)
            for index in range(22):
                eval(f'self.buttonT{index}.setEnabled(False)')
            self.button_production.setEnabled(False)  
            self.button_touch_all.setEnabled(False)  
            self.button_agging.setEnabled(False)  
            self.button_demo.setEnabled(False)  
            self.button_reset.setEnabled(False)   
    
    def boxOnDeviceDisconnect(self):
        if self.connected == 1:
            sleep(1)
            self.device.connectESP()
            self.DeviceConnect.setEnabled(True)
            for index in range(22):
                eval(f'self.buttonT{index}.setEnabled(True)')
            self.button_production.setEnabled(True)  
            self.button_touch_all.setEnabled(True)  
            self.button_agging.setEnabled(True)  
            self.button_demo.setEnabled(True)  
            self.button_reset.setEnabled(True)   

    def closeEvent(self, event):
        """
        - close G800 
        """
        state.mainWindow.closeScreenG800()
        self.disconnectAll()
