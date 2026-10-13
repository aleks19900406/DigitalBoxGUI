import datetime
import os
import traceback
from pathlib import Path
from time import sleep
import openpyxl
from PyQt5 import QtGui
from PyQt5.QtWidgets import QMainWindow
from PyQt5.uic import loadUi
from DigitalBox.Connection import BIO24
from DigitalBox.ElementsConnect import DeviceConnection
from PyQt5.QtCore import QThread
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from DigitalBox.lib import *
from . import state
from .paths import DATA_SAVE, IMAGE_PATH_OTHER, QT_DESIGNER
from .styles import ButtonStyleOff2, ButtonStyleOn, ButtonStyleWhite, InputStyleOff, InputStyleOn
from .discovery import NetworkScanner
from .workers import Worker
from .devices import listDeviceConnection
from .helpers import dataFile, listLanguageCraft, listVariantElements


class DeviceBio24(QMainWindow):
    def __init__(self):
        super().__init__()
        ########################## SCREEN PATH CONVERT #############################
        self.connected = 0
        self.connectedElements = 0
        self.counter = 0
        self.refreshSaving = 1000
        DacTable = QT_DESIGNER / 'Bio24.ui'
        loadUi(str(DacTable), self)
        self.setWindowTitle("BIO24")
        self.setFixedSize(750, 770)
        self.device_connect.setText('DEVICE CONNECT:')
        self.device_connect.setStyleSheet("color: gray")
        # Create a QTextCursor object
        self.label_errorSaveFile.setVisible(False)
        self.label_errorSaveFile.setFont(QFont('Arial', 12))
        self.label_errorSaveFile.setStyleSheet("color: red")
        self.DeviceConnect.activated[str].connect(self.deviceBox)
        self.DeviceConnect.setEditable(True)
        self.DeviceConnect.setStyleSheet(ButtonStyleWhite)
        self.DeviceConnect.addItems(listDeviceConnection())
        ############ change languages ########################
        self.time_lang_change = 1000
        self.lang_index = 0
        self.lang_max_index = 0
        self.setLanguage.activated[str].connect(self.setlanguage)
        self.setLanguage.setStyleSheet(ButtonStyleWhite)
        self.setLanguage.setEnabled(False)
        self.setLanguage.addItems(listLanguageCraft())
        self.reset_lang.pressed.connect(self.resetLang)
        self.reset_lang.setStyleSheet(ButtonStyleOff2)
        self.device_connect_lang.setText('DEVICE CONNECT:')
        self.device_connect_lang.setStyleSheet("color: gray")
        self.DeviceConnectLang.activated[str].connect(self.deviceBoxLang)
        self.DeviceConnectLang.setEditable(True)
        self.DeviceConnectLang.setStyleSheet(ButtonStyleWhite)
        self.DeviceConnectLang.addItems(listDeviceConnection())
        self.deviceDisconnect_lang.clicked.connect(self.disconnectAll_lang)
        self.deviceDisconnect_lang.setStyleSheet(ButtonStyleOff2)
        self.AutoLanguage = QTimer()
        self.AutoLanguage.timeout.connect(self.change_lang)  # 
        self.AutoLanguage.setInterval(state.MAIN_TIME_REFRESHING)
        self.buttonAutoThread = QThreadPool()
        self.checkBox_auto_lang.stateChanged.connect(self.doCheck)
        ###########################################
        self.deviceDisconnect.clicked.connect(self.disconnectAll)
        self.deviceDisconnect.setStyleSheet(ButtonStyleOff2)
        # EXCEL FILE
        self.ExcelFile.addItems(dataFile())
        ##################### SAVE DATA ##########################################
        self.ExcelFile.activated[str].connect(self.excelFile)
        self.ExcelFile.setEditable(True)
        self.ExcelFile.setStyleSheet(ButtonStyleWhite)
        self.indexButtonSave = 0
        self.index_refreshing = 0
        self.indexSaveData = 0
        self.indexButtonSave = 0
        self.repeatSaveData = 0
        self.indexBackup = 0
        self.savingBar.setVisible(False)
        self.backupSave.setVisible(False)
        self.backupSave.setStyleSheet("color: red")
        self.startStopSaving.clicked.connect(self.startStopSave)
        self.startStopSaving.setEnabled(False)
        self.startStopSaving.setStyleSheet(ButtonStyleOff2)
        self.refreshSaveData = QTimer()
        self.refreshSaveData.timeout.connect(self.savingData)  # 
        self.refreshSaveData.setInterval(state.MAIN_TIME_REFRESHING)
        self.iconSaveData = QtGui.QIcon()
        self.iconSaveData.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOn.png')))
        self.startStopSaving.setIcon(self.iconSaveData)
        self.timer_relay_state = QTimer()
        self.timer_relay_state.timeout.connect(self.check_relay_state)  # 
        self.timer_relay_state.setInterval(300)
        self.saveDataThread = QThreadPool()
        self.saveBarThread = QThread()
        ######################### Elements ################################        
        self.scan_thread = None
        self.scanner = None
        self.worker = Worker()
        self.worker.stepIncreased.connect(self.SaveBarShow)
        self.worker.moveToThread(self.saveBarThread)
        self.saveBarThread.started.connect(self.worker.task)
        self.DeviceConnecteElements.activated[str].connect(self.connectElements)
        self.DeviceConnecteElements.setEditable(True)
        self.DeviceConnecteElements.setStyleSheet(ButtonStyleWhite)
        self.progress_label_IP.setText('Scenning')
        self.ip_search.clicked.connect(self.start_scan)
        self.ip_search.setStyleSheet(ButtonStyleOff2)
        self.reset_lang_elements.pressed.connect(self.resetLangElements)
        self.reset_lang_elements.setStyleSheet(ButtonStyleOff2)
        self.progress_label_IP.setVisible(False)
        self.setLanguageElemets.activated[str].connect(self.setlanguageElements)
        self.setLanguageElemets.setStyleSheet(ButtonStyleWhite)
        self.setLanguageElemets.setEnabled(False)
        self.setLanguageElemets.addItems(state.ALL_LANG_CRAFT)
        self.checkBox_auto_lang_Elements.stateChanged.connect(self.doCheckElements)
        #################lang timer
        self.AutoLanguageElements = QTimer()
        self.AutoLanguageElements.timeout.connect(self.change_lang_elements)  # 
        self.AutoLanguageElements.setInterval(state.MAIN_TIME_REFRESHING)
        ################ set variant ############
        self.setVariantElements.activated[str].connect(self.setVariant)
        self.setVariantElements.setStyleSheet(ButtonStyleWhite)
        self.setVariantElements.setEnabled(False)
        self.setVariantElements.addItems(listVariantElements())
        self.start_scan()
    def start_scan(self):
        ###########
        #self.device_connect_lang_2.setText('CONNECT TO DEVICE:')
        #self.device_connect_lang_2.setStyleSheet("color: green")
        self.progress_label_IP.setVisible(True)
        self.AutoLanguage.stop()
        self.DeviceConnecteElements.setEnabled(True)
        self.setLanguageElemets.setEnabled(False)
        self.setVariantElements.setEnabled(False)
        self.DeviceConnecteElements.setStyleSheet(ButtonStyleOff2)
        self.setLanguageElemets.setStyleSheet(ButtonStyleOff2)
        self.DeviceConnecteElements.clear()
        if self.connectedElements == 1:
            self.connectedElements = 0
            self.dev.disconnect()
        
        # clear combo but keep editable text if typed
        typed = self.DeviceConnecteElements.currentText()
        self.DeviceConnecteElements.clear()
        self.ip_search.setEnabled(False)
        if typed:
            self.DeviceConnecteElements.setEditText(typed)
        self.progress_label_IP.setText("Scanning network...")
        # create worker and thread
        self.scanner = NetworkScanner()
        self.scan_thread = QThread()
        self.scanner.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scanner.run)
        self.scanner.found.connect(self.add_ip)
        self.scanner.progress.connect(self.update_progress)
        self.scanner.finished.connect(self.scan_finished)
        self.scan_thread.start()
    def stop_scan(self):
        if self.scanner:
            self.scanner.stop()

    def add_ip(self, ip):
        # only add once
        if ip not in [self.DeviceConnecteElements.itemText(i) for i in range(self.DeviceConnecteElements.count())]:
            self.DeviceConnecteElements.addItem(ip)

    def update_progress(self, found, scanned):
        self.progress_label_IP.setText(f"Found: {found} — Scanned: {scanned}")

    def scan_finished(self):
        self.progress_label_IP.setText("Scan finished")
        self.ip_search.setEnabled(True)
        # cleanup thread
        if self.scan_thread:
            self.scan_thread.quit()
            self.scan_thread.wait()
            self.scan_thread = None
            self.scanner = None    
    
    def check_relay_state(self):
        """
        color relay state ON/OFF
        """
        for index,state in enumerate(list(self.device.check_relay().values())):
            try:
                if state == 'ON':
                    eval(f'self.RELAY_{index}.setStyleSheet(InputStyleOn)')
                    state.change_input[index] = True

                elif state == '/':
                    eval(f'self.RELAY_{index}.setStyleSheet(InputStyleOff)')
                    state.change_input[index] = False       
            except Exception:
                print('error box')
                continue
    
    def deviceBox(self, CONNECTBOX):
        """
        - connect device BIO24
        - show warning message if device is disconnected
        """
        try:
            if CONNECTBOX[0:3] =='COM':
                self.device = BIO24(CONNECTBOX[0:5].replace(' ',''),baudrate=115200)
                self.device.connect()
                self.connected = 1
                sleep(1)
                self.device_connect.setText('CONNECT:')
                self.device_connect.setStyleSheet("color: green")
                self.DeviceConnect.setStyleSheet(ButtonStyleOn)
                self.DeviceConnect.setEnabled(False)
                self.timer_relay_state.start()
                self.index_refreshing = 1
            else:
                sleep(2)
                self.device_connect.setText('DEVICE DISCONNECTED:')
                self.device_connect.setStyleSheet("color: red")
                self.connected = 0
                self.device.disconnect()
                self.timer_relay_state.stop()
                self.index_refreshing = 0
        except:
            self.device.disconnect()
            self.index_refreshing = 0
            self.timer_relay_state.stop()
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
    
    def deviceBoxLang(self, CONNECTBOX):
        """
        - connect device G800
        - show warning message if device is disconnected
        """
        try:
            if CONNECTBOX[0:3] =='COM':
                self.device = BIO24(CONNECTBOX[0:5].replace(' ',''),baudrate=921600)
                self.device.connect()
                self.connected = 1
                sleep(1)
                self.device_connect_lang.setText('CONNECT:')
                self.device_connect_lang.setStyleSheet("color: green")
                self.DeviceConnectLang.setStyleSheet(ButtonStyleOn)
                self.DeviceConnectLang.setEnabled(False)
                self.setLanguage.setEnabled(True)
            else:
                sleep(2)
                self.device_connect_lang.setText('DEVICE DISCONNECTED:')
                self.device_connect_lang.setStyleSheet("color: red")
                self.connected = 0
                self.device.disconnect()
        except Exception:
            self.device.disconnect()
            self.device_connect_lang.setText('DEVICE DISCONNECTED:')
            self.device_connect_lang.setStyleSheet("color: red")
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
    
    def connectElements(self, CONNECTBOX):
        """
        - connect device G800
        - show warning message if device is disconnected
        """
        try:
            self.dev = DeviceConnection(method="wifi", host=f"{CONNECTBOX}", port=9005)
            self.dev.connect()
            self.progress_label_IP.setVisible(False)
            self.connectedElements = 1
            sleep(1)
            self.device_connect_lang_2.setText('CONNECT:')
            self.device_connect_lang_2.setStyleSheet("color: green")
            self.DeviceConnecteElements.setStyleSheet(ButtonStyleOn)
            self.DeviceConnecteElements.setEnabled(False)
            self.setLanguageElemets.setEnabled(True)
            self.setVariantElements.setEnabled(True)
          
        except:
            self.dev.disconnect()
            self.connectedElements = 0
            self.device_connect_lang_2.setText('DEVICE DISCONNECTED:')
            self.device_connect_lang_2.setStyleSheet("color: red")
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{state.errorNumber}{dateAndTime}{state.errorNumber}\n')
                f.write('Device is not conncected \n')
                f.write('Solution:\n')
                f.write('-- Connenct to the correct ip address !!!\n')
                f.write(f'{state.errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{state.errorNumber*2}\n')
            f.close()
    
    def resetLang(self):
        self.setLanguage.clear()
        self.setLanguage.addItems(listLanguageCraft())
    
    def resetLangElements(self):
        self.setLanguageElemets.clear()
        self.setLanguageElemets.addItems(listLanguageCraft())
    
    def setlanguage(self,lang):
        self.device.change_language_craft(self.setLanguage.currentIndex())
        self.setLanguage.setStyleSheet(ButtonStyleOn)
    
    def setlanguageElements(self):
        #print(self.setLanguageElemets.currentIndex())
        self.dev.setLanguages(self.setLanguageElemets.currentIndex())
        self.setLanguageElemets.setStyleSheet(ButtonStyleOn)
    
    def setVariant(self):
        #print(self.setVariantElements.currentIndex())
        self.dev.setModel(self.setVariantElements.currentIndex())
        self.setVariantElements.setStyleSheet(ButtonStyleOn)
    
    def doCheck(self):
        if self.checkBox_auto_lang.isChecked():
            # Checkbox is checked
            self.lang_max_index = max([index for index,i in enumerate(state.ALL_LANG_CRAFT)])
            self.AutoLanguage.start()
        else:
            self.AutoLanguage.stop()
    
    def doCheckElements(self):
        if self.checkBox_auto_lang_Elements.isChecked():
            # Checkbox is checked
            self.lang_max_index = max([index for index,i in enumerate(state.ALL_LANG_CRAFT)])
            self.AutoLanguageElements.start()
        else:
            self.AutoLanguageElements.stop()
    
    def reset(self):
        self.device.disconnect()
        self.device.connect()
        
    def change_lang(self):
        self.setLanguage.clear()
        if self.lang_index == self.lang_max_index+1:
            self.lang_index = 0
        if self.time_lang_change != self.change_language_time.value():
            self.time_lang_change = self.change_language_time.value()
            self.AutoLanguage.setInterval(int(self.change_language_time.value()*1000))
        self.device.change_language_craft(self.lang_index)
        lang_name =''.join([i for index,i in enumerate(state.ALL_LANG_CRAFT) if index == self.lang_index])
        self.setLanguage.addItem(lang_name)
        self.lang_index += 1
    def change_lang_elements(self):
        self.setLanguageElemets.clear()
        if self.lang_index == self.lang_max_index+1:
            self.lang_index = 0
        if self.time_lang_change != self.change_language_time_Elements.value():
            self.time_lang_change = self.change_language_time_Elements.value()
            self.AutoLanguageElements.setInterval(int(self.change_language_time_Elements.value()*1000))
        self.dev.setLanguages(self.lang_index)
        lang_name =''.join([i for index,i in enumerate(state.ALL_LANG_CRAFT) if index == self.lang_index])
        self.setLanguageElemets.addItem(lang_name)
        self.lang_index += 1
    def setlanguage(self,lang):
        self.device.change_language_craft(self.setLanguage.currentIndex())
        self.setLanguage.setStyleSheet(ButtonStyleOn)
        
    def disconnectAll_lang(self):
        self.AutoLanguage.stop()
        self.setLanguage.clear()
        self.setLanguage.addItems(listLanguageCraft())
        sleep(1)
        self.device_connect_lang.setText('DEVICE CONNECT:')
        self.device_connect_lang.setStyleSheet("color: gray")
        self.DeviceConnectLang.setEnabled(True)
        self.setLanguage.setEnabled(False)
        self.DeviceConnectLang.setStyleSheet(ButtonStyleOff2)
        self.setLanguage.setStyleSheet(ButtonStyleOff2)
        self.DeviceConnectLang.clear()
        self.DeviceConnectLang.addItems(listDeviceConnection())
        if self.connected == 1:
            self.connected = 0
            self.device.disconnect()
       
    def disconnectAll(self):
        """
        -disconnect device with button
        """
        self.device_connect.setText('DEVICE CONNECT:')
        self.device_connect.setStyleSheet("color: gray")
        self.DeviceConnect.setEnabled(True)
        self.DeviceConnect.setStyleSheet(ButtonStyleOff2)
        self.DeviceConnect.clear()
        for index in range(21):
            eval(f'self.RELAY_{index}.setStyleSheet(InputStyleOff)')
        self.DeviceConnect.addItems(listDeviceConnection())
        if self.connected == 1:
            self.connected = 0
            self.device.disconnect()
            self.index_refreshing = 0
            self.timer_relay_state.stop()
    #EXCEL
    def excelFile(self,file_name):
        """
        - save relay name parameters first column
        """
        try:
            self.fileName = file_name
            if self.index_refreshing >= 1:
                if self.repeatSaveData == 0:
                    self.indexButtonSave += 1
                self.indexSaveData = 0
                self.wb = openpyxl.Workbook()     
                self.sheet = self.wb.active
                sheetNames = []
                columnName = self.sheet.cell(row = 1, column = 1) 
                columnName.value = 'date'
                columnName = self.sheet.cell(row = 1, column = 2) 
                columnName.value = 'time'
                sheetNames.extend(list(self.device.check_relay().keys()))
                for index, name in enumerate(sheetNames):
                    columnName = self.sheet.cell(row = 1, column = index+3) 
                    columnName.value = name
                if  self.indexButtonSave == 1:
                    self.ExcelFile.setStyleSheet(ButtonStyleOn)
                    self.startStopSaving.setEnabled(True)
                    self.startStopSaving.setIcon(self.iconSaveData)
                    self.refreshSaveData.start()
                    sleep(2)
                else:
                    self.ExcelFile.setStyleSheet(ButtonStyleWhite)
                    self.refreshSaveData.stop()
                    self.iconSaveData.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOff.png')))
                    self.startStopSaving.setIcon(self.iconSaveData)
            else:
                self.label_errorSaveFile.setVisible(True)
                self.label_saveFile.setVisible(False)
                self.label_errorSaveFile.setText("!!! DEVICE IS NOT CONNECTED !!!")
            
            if self.indexButtonSave >=2:
                self.indexButtonSave =0
        
        except PermissionError:
            self.label_errorSaveFile.setVisible(True)
            self.label_saveFile.setVisible(False)
            self.label_errorSaveFile.setText(f"!!! Excel file {self.fileName} is open. Close and try again !!!")
          
    def savingData(self):
        """
        - save data to excel file
        - if refreshing is 1s create new file every 24ur
        """
        if(self.indexSaveData % 2) == 0:
                self.iconSaveData.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOn.png')))
                self.startStopSaving.setIcon(self.iconSaveData)
                #self.startStopSaving.setStyleSheet(ButtonStyleOn2)
        else:
            self.iconSaveData.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOn1.png')))
            self.startStopSaving.setIcon(self.iconSaveData)
            #self.startStopSaving.setStyleSheet(ButtonStyleOff2)
        self.time=QDateTime.currentDateTime()
        if self.indexSaveData == 86400:  ### saving data to file 24h if refreshing is 1s
            self.refreshSaveData.stop()
            sleep(1)
            self.repeatSaveData += 1
            self.saveDataThread.start(self.saveToCsv)
            self.savingBar.setVisible(True)
            self.backupSave.setVisible(True)
            self.saveBarThread.start()
            self.timeSave =self.indexSaveData * 0.001
            if (self.timeSave) < 1:
                self.worker.setValue(2)
            else:
                self.worker.setValue(self.timeSave)
            sleep(5)
            self.refreshSaveData.start()
          
        if self.indexSaveData > 86480:
            self.saveBarThread.terminate()
            self.indexSaveData = 0
            self.excelFile(self.fileName)
        allParameters = []
        self.label_saveFile.setVisible(True)
        if self.refreshSaving != self.excelRefresh.value():
            self.refreshSaveData.setInterval(int(self.excelRefresh.value()*1000))
            #self.refreshSaveData.setInterval(int(self.excelRefresh.value()*1)) # Test
            self.refreshSaving = self.excelRefresh.value()

        if list(self.device.check_relay().values()) != []: # do not save if list is empty
            allParameters.extend([1 if s == 'ON' else 0 for s in list(self.device.check_relay().values())])
        
            RowName = self.sheet.cell(row = self.indexSaveData+2, column = 1) 
            RowName.value = self.time.toString('dd-MM-yyyy')
            RowName = self.sheet.cell(row = self.indexSaveData+2, column = 2) 
            RowName.value = self.time.toString('hh:mm:ss')
            for index, name in enumerate(allParameters):
                RowName = self.sheet.cell(row = self.indexSaveData+2, column = index+3)
                RowName.value=name

            self.indexSaveData += 1
        #print(self.indexSaveData)
    
    def saveToCsv(self):
        """
        - sava to .csv file
        """
        try: 
            self.startStopSaving.setEnabled(False)
            if self.repeatSaveData == 0 and self.indexBackup == 0: 
                self.wb.save(f"{DATA_SAVE}/{self.fileName}.csv")
            elif self.indexBackup == 1:
                self.wb.save(f"{DATA_SAVE}/{self.fileName}_backup.csv")
                self.indexBackup = 0
            else:
                self.wb.save(f"{DATA_SAVE}/{self.fileName}_{self.repeatSaveData}.csv")
            sleep(self.timeSave/10)
            self.startStopSaving.setEnabled(True)
            self.savingBar.setVisible(False)
            self.backupSave.setVisible(False)
           
        except PermissionError:
            self.indexButtonSave = 0
            self.startStopSaving.setEnabled(True)
            self.label_errorSaveFile.setVisible(True)
            self.label_saveFile.setVisible(False)
            self.savingBar.setVisible(False)
            self.backupSave.setVisible(False)
            self.label_errorSaveFile.setText(f"!!! Excel file {self.fileName} is open. Close and try again !!!")
        
        except AttributeError:
            self.indexButtonSave = 0
            self.startStopSaving.setEnabled(True)
            self.label_errorSaveFile.setVisible(True)
            self.label_saveFile.setVisible(False)
            self.savingBar.setVisible(False)
            self.backupSave.setVisible(False)
            self.label_errorSaveFile.setText("!!! File not saved. Write file name and press enter !!!")
            print(traceback.print_exc())
    
    def startStopSave(self):
        """
        - start or stop saving parameters to excel
        """
        #print("file name",self.fileName)
        if self.index_refreshing >= 1:
            self.label_errorSaveFile.setVisible(False)
            self.indexButtonSave +=1
            if  self.indexButtonSave == 1:
                self.savingBar.setVisible(False)
                self.ExcelFile.setStyleSheet(ButtonStyleOn)
                self.refreshSaveData.start()
                self.saveBarThread.terminate()
            else:
                self.repeatSaveData = 0
                self.ExcelFile.setStyleSheet(ButtonStyleWhite)
                self.refreshSaveData.stop()
                sleep(1)
                self.iconSaveData.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOff.png')))
                self.startStopSaving.setIcon(self.iconSaveData)
                self.saveDataThread.start(self.saveToCsv)
                self.timeSave =self.indexSaveData * 0.001     # calculation saving time
                if self.indexSaveData > 3000:
                    self.savingBar.setVisible(True)
                    self.backupSave.setVisible(True)
                    self.saveBarThread.start()
                    if (self.timeSave) < 1:
                        self.worker.setValue(2)
                    else:
                        self.worker.setValue(self.timeSave)
               
        if self.indexButtonSave >=2:
            self.indexButtonSave =0
    
    def SaveBarShow(self,value):
        """
        - calculate have long saving bar showed
        """
        if self.timeSave < 1:
            self.savingBar.setValue(100)  
        else:
            self.savingBar.setValue(int(value*(100/self.timeSave)))
            if int(value*(100/self.timeSave)) > 100:
                 self.savingBar.setValue(100)

    def closeEvent(self, event):
        """
        - close BIO24
        """
        state.mainWindow.closeScreenBio24()
        self.disconnectAll()
        if hasattr(self, "dev") and self.dev is not None:
            try:
                self.dev.disconnect()
            except Exception as e:
                print("Error disconnecting device:", e)

        # Continue closing the window
        event.accept()
