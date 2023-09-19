###################### IMPORTS #########################################
import sys
import os
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets,QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QMessageBox,QMainWindow,QApplication,QTreeWidgetItemIterator,QTreeWidgetItem,QTreeWidget,QPushButton,QPlainTextEdit
from PyQt5.QtCore import *
from time import sleep,time
from package.tester._clients.das import DAS  # Import DAS class
from DigitalBox.dasConnect import SERIALCONNECT,WifiEsp32Connect
from DigitalBox.lib import*
import serial.tools.list_ports
import traceback
import openpyxl
import subprocess
import datetime

################## PATH TO DATA FILE ####################################
QT_DESIGNER_PATH = os.path.join("QT_designer")
BOX_MARKS_PATH = os.path.join("data","boxMarks")
BOX_DIGITAL_POT_PATH = os.path.join("data","digitalPotTable")
BOX_DIGITAL_DAC_PATH = os.path.join("data","dacTable")
IMAGES_PATH = os.path.join("data","images","system")
IMAGE_PATH_OTHER =os.path.join("data","images","other")
DATA_SAVE = os.path.join("data","saveData")
AUTO_TEST_PATH = os.path.join("data","autoTest")
#print(os.path.basename(AUTO_TEST_PATH))
###################### BEGIN PARAMETERS #################################
VERZIJA_ESP = "3.17"
VERZIJA_RPI = "3.10"
MAIN_TIME_REFRESHING = 1000
SPACE = '\n'
DigitalInput = 32
change_input = []
for input in range(DigitalInput):
    change_input.append(False)
change_parameters =[0,0,0,0,0,0,0,0,0]
beginPotValue = [0,0,0,0,0,0]
beginDacValue = [0,0,0,0,0,0,0,0]
beginSetVoltage = [0,0,0,0]
beginSetPot = 0
beginDacPot = 0

setPwm1 = [0,0]
setPwm2 = [0,0]
setPwmOld =[0,0]
errorNumber ='#'*50
######################### BUTTON SET STYLE ##############################
ButtonStyleOnOff = ("background-color:white ;""font: 10px;" )
ButtonStyleOff2  = ("background-color: rgb(210,210,210);""font: 10px;" )
ButtonStyleOn2  = ("background-color: rgb(159,255,159);""font: 10px;")
ButtonStyleOff  = ("background-color: rgb(210,210,210);"
                                "border-radius: 5px;""font: 10px;")
ButtonStyleOn  = ("background-color:  rgb(159,255,159);"
                                "border-radius: 5px;"
                                "font: 12px;")                                 
ButtonStyleWhite = ("background-color: white;"
                                "border-style: outset;"
                                "border-radius: 5px;"
                                "font: 12px;")
MainScreenStyle = "background-color: rgb(250,255,250)"
PotSlicerLabelStyle = ("background-color: white;"
                                "border-style: outset;"
                                "border-radius: 5px;"
                                "border-color: fusion;"
                                "font: 12px;")

InputStyleOn  = ("background-color:  rgb(159,255,159);"
                                "border-radius: 5px;"
                                "font: 10px;")                                 
InputStyleOff =  ("background-color: rgb(210,210,210);"
                                "border-radius: 5px;""font: 10px;")
##########################################################################

class Worker(QObject):
    finished = pyqtSignal()
    stepIncreased = pyqtSignal(int)
    def __init__(self):
            super(Worker, self).__init__()
            self._step = 0
            self._isRunning = True
            self._maxSteps = 100
    
    def setValue(self,value):
        self.value = value
        self.stepIncreased.emit(self._step)
    
    def task(self):
        if not self._isRunning:
            self._isRunning = True
            self._step = 0
        
        while self._step  < self.value  and self._isRunning == True:
            self._step += 1
            self.stepIncreased.emit(self._step)
            sleep(1)
        self._step = 0
        self.finished.emit()
    def stop(self):
        self._isRunning = False

def listDigitalDacTable():
    """
    Convert all DacTable file name to list except readMe.txt
    """
    DigitalDacList =[]
    DigitalDacList.clear()
    for file_name in os.listdir(BOX_DIGITAL_DAC_PATH):
        if file_name == "readMe.txt":
            continue
        if file_name.endswith('.txt'):
            DigitalDacList.append(file_name.replace('.txt',''))
    return DigitalDacList

def dataFile():
    """
    Convert all saveData file name to list but only file with the extension .xlsx
    """
    dataSave =[]
    dataSave.clear()
    #dataSave.append('')
    for file_name in os.listdir(DATA_SAVE):
        if file_name.endswith('.csv'):
            dataSave.append(file_name.replace('.csv',''))
    return dataSave

def listBoxMarks():
    """
    Convert all boxMaks file name to list except readMe.txt
    """
    boxMarkList =[]
    boxMarkList.clear()
    for file_name in os.listdir(BOX_MARKS_PATH):
        #print(file_name)
        if file_name == "readMe.txt":
            continue
        if file_name.endswith('.txt'):
            boxMarkList.append(file_name.replace('.txt',''))
    return boxMarkList

def listDigitalPotTable():
    """
        Convert all digitalPotTable file name to list except readMe.txt
    """
    DigitalPotList =[]
    DigitalPotList.clear()
    for file_name in os.listdir(BOX_DIGITAL_POT_PATH):
        if file_name == "readMe.txt":
            continue
        if file_name.endswith('.txt'):
            DigitalPotList.append(file_name.replace('.txt',''))
    return DigitalPotList

def deliteListDigitalPotTable():
    """
    - refresh file and reload
    """
    DigitalPotList =[]
    DigitalPotList.clear()
    for file_name in os.listdir(BOX_DIGITAL_POT_PATH):
        if file_name.endswith('.txt'):
            DigitalPotList.append(file_name.replace('.txt',''))
    return DigitalPotList

def sliderColor(self,sliderIndex,minValue,maxValue):
    """_summary_

    Args:
        sliderIndex (_type_): _description_
        minValue (_type_): _description_
        maxValue (_type_): _description_

    Returns:
        _type_: _description_
        

    Color digital pot slider depends value set
    
    """
    sliderValue = eval(f'self.digital_pot{sliderIndex}.value()')
    setColorMax = maxValue/255
    if (sliderValue/setColorMax)>=255:
        G=B=0
        R=255
    elif (sliderValue/setColorMax) <= 10:
        B=255
        R=G = 240 - abs(sliderValue/setColorMax-20)
    else:
        G=B= 255-(sliderValue/setColorMax)
        R =255
       
    return int(R),int(G),int(B)

def sliderColorDac(self,sliderIndex,minValue,maxValue):
    """_summary_

    Args:
        sliderIndex (_type_): _description_
        minValue (_type_): _description_
        maxValue (_type_): _description_

    Returns:
        _type_: _description_
        
    Color Dac slider depends value set   
    """
    colorSlider = eval(f'self.dac_pot{sliderIndex}.value()')
    setColorMax = maxValue/255
    if (colorSlider/setColorMax)>=255:
        G=B=0
        R=255
    elif (colorSlider/setColorMax) <= 10:
        B=255
        R=G = 240 - abs(colorSlider/setColorMax-20)
    else:
        G=B= 255-(colorSlider/setColorMax)
        R =255
       
    return int(R),int(G),int(B)

def listConnection():
    """
    Find all serial connection only Arduino Mega(old box) and ESP32(new box) and convert to list
    Convert to list all rpi 192.168.1.10'--->192.168.1.90    
    """
    LIST_CONNECT =[]
    LIST_CONNECT.clear()
    for USB_PORT in serial.tools.list_ports.comports():
        if 'Arduino Mega' in str(USB_PORT):
            LIST_CONNECT.append(f'{str(USB_PORT)[0:5]} - Arduino Mega 2560') 
        elif'CP210x' in str(USB_PORT) :
            LIST_CONNECT.append(f'{str(USB_PORT)[0:5]} - NodeMCU ESP32')
    #LIST_CONNECT.append("")
    for ip_address in range(15,100,10):
        LIST_CONNECT.append(f'ESP32 - 192.168.1.{ip_address}')
    for ip_address in range(10,100,10):
        LIST_CONNECT.append(f'RPI - 192.168.1.{ip_address}')
    
    return LIST_CONNECT
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        Window1 = os.path.abspath(f"{QT_DESIGNER_PATH}/Main_screen.ui")
        loadUi(str(Window1),self)
        f = open("check_error.txt", "w")
        f.write("")
        f.close()
        self.refreshSaving = 1000
        self.index_on_off = 0
        self.index_out = [0,0,0,0,0,0,0,0]
        self.index_extras = [0,0,0,0,0,0,0,0]
        self.connectParameters = 0
        self.box_is_connected = 0
        self.index_refreshing = 0
        self.digitalPotChange = 0
        self.digitalPotIndex = 0
        self.indexSaveData = 0
        self.indexButtonSave = 0
        self.repeatSaveData = 0
        self.indexBackup = 0
        self.setWindowTitle('DIGITAL BOX MAIN')
        #self.setFixedSize(1920, 1080)
        self.setGeometry(150, 40, 1520, 990)
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
        ###################### BUTTON OPEN ADDITIONAL SCREEN ######################
        self.ButtonHusaModel.clicked.connect(self.buttonHusaModel)
        self.ButtonPyroSystem.clicked.connect(self.buttonPyroSystem)
        self.ButtonDacSet.clicked.connect(self.buttonDacSet)
        self.ButtonSetPot.clicked.connect(self.buttonSetPot)
        self.ButtonSetDac.clicked.connect(self.buttonSetDac)
        self.ButtonAutomation.clicked.connect(self.buttonAutomation)
        #self.ButtonCreateAutoTest.clicked.connect(self.buttonCreateAutoTest)
        self.ButtonCreateAutoTest.setVisible(False)
        self.barOpenAutoTest.setVisible(False)
        self.SetEnvirement.setVisible(False)
        self.setEnvironmentText.setVisible(False)
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
        self.BoxConnect.addItems(listConnection())
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
        self.DIGITAL_BOX_MAIN.setInterval(MAIN_TIME_REFRESHING)
        self.ReadSetPotDac = QTimer()
        self.ReadSetPotDac.timeout.connect(self.timerCreatePotDacTable)  # 
        self.ReadSetPotDac.setInterval(MAIN_TIME_REFRESHING)
        self.refreshSaveData = QTimer()
        self.refreshSaveData.timeout.connect(self.savingData)  # 
        self.refreshSaveData.setInterval(MAIN_TIME_REFRESHING)
        self.dateTimeTimer = QTimer()
        self.dateTimeTimer.timeout.connect(self.showTime)  # 
        self.dateTimeTimer.setInterval(MAIN_TIME_REFRESHING)
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
        
        self.iconOn = QtGui.QIcon()
        self.iconOn.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/OnButton.png')))
        
        self.on_off.setIcon(self.iconOff)
        self.iconRefresh = QtGui.QIcon()
        self.iconRefresh.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/ButtonRefresh.png')))
        self.RefreshingConnection.setIcon(self.iconRefresh)
        self.iconSaveData = QtGui.QIcon()
        self.iconSaveData.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOn.png')))
        self.startStopSaving.setIcon(self.iconSaveData)
    
    
    def resetExcelParameters(self):
        """
        - reset parameters when box connection change or button refresh pressed 
        """
        self.repeatSaveData = 0
        self.indexButtonSave =0
        self.refreshSaveData.stop()
        self.ExcelFile.setStyleSheet(ButtonStyleWhite)
        self.refreshSaveData.stop()
     
    def backup_save(self):
        """
        - if user change box connection or click refresh button create a backup file
        """
        if self.indexButtonSave == 1: #backup
            self.indexBackup += 1
            self.indexButtonSave = 0
            self.backupSave.setVisible(True)
            self.ExcelFile.setStyleSheet(ButtonStyleWhite)
            self.refreshSaveData.stop()
            sleep(1)
            self.saveDataThread.start(self.saveToCsv)
            self.savingBar.setVisible(True)
            self.backupSave.setVisible(True)
            self.saveBarThread.start()
           
            self.timeSave =self.indexSaveData * 0.001     # calculation saving time
            if (self.timeSave) < 1:
                self.worker.setValue(2)
                
            else:
                self.worker.setValue(self.timeSave)
            self.repeatSaveData = 0
            self.indexSaveData = 0
            self.saveBarThread.terminate()
     
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
            self.label_errorSaveFile.setText(f"!!! File not saved. Write file name and press enter !!!")
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
             
    def savingData(self):
        """
        - save data to excel file
        """
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

        digitalPot = [self.readDigitalPot0,self.readDigitalPot1,self.readDigitalPot2,self.readDigitalPot3,self.readDigitalPot4,self.readDigitalPot5]
        digitalOut = [bool(self.index_on_off),bool(self.index_out[0]),bool(self.index_out[1]),bool(self.index_out[2]),bool(self.index_out[3]),bool(self.index_out[4]),bool(self.index_out[5]),bool(self.index_out[6]),bool(self.index_out[7])]
        
        readPwm1= [self.read_pwm_all[0]['f'],self.read_pwm_all[0]['d']]
        readPwm2= [self.read_pwm_all[1]['f'],self.read_pwm_all[1]['d']]
        dacSet = [self.readDac0,self.readDac1,self.readDac2,self.readDac3,self.readDac4,self.readDac5,self.readDac6,self.readDac7]
        allParameters.extend(digitalPot)
        allParameters.extend(digitalOut)
        allParameters.extend(self.read_adc_all)
        allParameters.extend(self.readVoltage)
        allParameters.extend(readPwm1)
        allParameters.extend(self.readPwm1)
        allParameters.extend(readPwm2)
        allParameters.extend(self.readPwm2)
        allParameters.extend(self.read_input)
        allParameters.extend(dacSet)
        allParameters.extend(self.readPwmOld)
        RowName = self.sheet.cell(row = self.indexSaveData+2, column = 1) 
        RowName.value = self.time.toString('dd-MM-yyyy hh:mm:ss')
        for index, name in enumerate(allParameters):
            RowName = self.sheet.cell(row = self.indexSaveData+2, column = index+2)
            RowName.value=name

        self.indexSaveData += 1
        #print(self.indexSaveData)
        
    def excelFile(self,file_name):
        """
        - in first column create name for all parameters
        - if Marks is selected get names from boxMark file and copy to first column row
        """
        try:
            self.fileName = file_name
            if self.index_refreshing >= 1:
                if self.repeatSaveData == 0:
                    self.indexButtonSave += 1
                self.indexSaveData = 0
                self.wb = openpyxl.Workbook()     
                self.sheet = self.wb.active
                freqOldBox = []
                dutyOldBox = []
                dacSet =[]
                digitalInput = []
                readAdc =[]
                setVoltage = []
                readPwm1 = []
                readPwm2 = []
                setPwm1 = []
                setPwm2 = []
                digitalOut = []
                digitalPot =[]
                sheetNames =[]
                for index in range(6):
                    try:
                        if self.read_all_lines[5].replace('\n','').split(',')[index] == '':
                            digitalPot.append(f'setPot{index}')
                        else:
                            digitalPot.append(self.read_all_lines[5].replace('\n','').split(',')[index])
                    except IndexError:
                        digitalPot.append(f'setPot{index}')
                    except AttributeError:
                        digitalPot.append(f'setPot{index}')
                digitalOut.append(f'On/Off')
                for index in range(8):
                    try:
                        if self.read_all_lines[3].replace('\n','').split(',')[index] == '':
                            digitalOut.append(f'switch{index}')
                        else:
                            digitalOut.append(self.read_all_lines[3].replace('\n','').split(',')[index])
                    except IndexError:
                        digitalOut.append(f'switch{index}')
                    except AttributeError:
                        digitalOut.append(f'switch{index}')
                    
                for index in range(4):
                    try:
                        if self.read_all_lines[9].replace('\n','').split(',')[index] == '':
                            readAdc.append(f'readADC{index}')
                        else:
                            readAdc.append(self.read_all_lines[9].replace('\n','').split(',')[index])
                    except IndexError:
                        readAdc.append(f'readADC{index}')
                    except AttributeError: 
                        readAdc.append(f'readADC{index}')
                for index in range(4):
                    try:
                        if self.read_all_lines[11].replace('\n','').split(',')[index] == '':
                            setVoltage.append(f'setVoltage{index}')
                        else:
                            setVoltage.append(self.read_all_lines[11].replace('\n','').split(',')[index])
                            
                    except IndexError:
                        setVoltage.append(f'setVoltage{index}')
                    except AttributeError:         
                        setVoltage.append(f'setVoltage{index}')
                readPwm1.append(f'readPwm1')
                readPwm1.append(f'readDuty1')
                setPwm1.append(f'setPwm1')
                setPwm1.append(f'setDuty1')
                readPwm2.append(f'readPwm2')
                readPwm2.append(f'readDuty2')
                setPwm2.append(f'setPwm2')
                setPwm2.append(f'setDuty2')
                for index in range(32):
                    try:
                        if self.read_all_lines[1].replace('\n','').split(',')[index] == '':
                            digitalInput.append(f'IN{index}')
                        else:
                            digitalInput.append(self.read_all_lines[1].replace('\n','').split(',')[index])
                    except IndexError:
                        digitalInput.append(f'IN{index}')
                    except AttributeError:         
                        digitalInput.append(f'IN{index}')    
                for index in range(8):
                    try:
                        if self.read_all_lines[7].replace('\n','').split(',')[index] == '':
                            dacSet.append(f'setDac{index}')
                        else:
                            dacSet.append(self.read_all_lines[7].replace('\n','').split(',')[index])
                    except IndexError:
                        dacSet.append(f'setDac{index}')
                    except AttributeError:         
                        dacSet.append(f'setDac{index}') 
                freqOldBox.append(f'setFreq(duty50%)')
                dutyOldBox.append(f'setDuty(2kHz)')
                sheetNames.extend(digitalPot)
                sheetNames.extend(digitalOut)
                sheetNames.extend(readAdc)
                sheetNames.extend(setVoltage)
                sheetNames.extend(readPwm1)
                sheetNames.extend(setPwm1)
                sheetNames.extend(readPwm2)
                sheetNames.extend(setPwm2)
                sheetNames.extend(digitalInput)
                sheetNames.extend(dacSet)
                sheetNames.extend(freqOldBox)
                sheetNames.extend(dutyOldBox)
                columnName = self.sheet.cell(row = 1, column = 1) 
                columnName.value = 'date and time'
                for index, name in enumerate(sheetNames):
                    columnName = self.sheet.cell(row = 1, column = index+2) 
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
                self.label_errorSaveFile.setText(f"!!! CONNECT DIGITAL BOX !!!")
            
            if self.indexButtonSave >=2:
                self.indexButtonSave =0
        
        except PermissionError:
            self.label_errorSaveFile.setVisible(True)
            self.label_saveFile.setVisible(False)
            self.label_errorSaveFile.setText(f"!!! Excel file {self.fileName} is open. Close and try again !!!")
        
    def closeEvent(self, event):
        """
        show the message when you close the application
        """
        self.DIGITAL_BOX_MAIN.stop()
        close = QMessageBox()
        close.setText("Are you sure you want to close digital box ?")
        close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        close = close.exec()
        if close == QMessageBox.Yes:
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
            mainWindow.close()
            HusaModelWindow.close()
            PyroSetSystem.close()
            SetDacValue.close()
            PotTableSet.close()
            DacTableCreate.close()
            RunAutoTest.close()
            
             
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
        global MAIN_TIME_REFRESHING
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
                print('time main box',int((tend-tbegin)*1000),'ms','interval:',MAIN_TIME_REFRESHING)
                
                # increase main time refreshing if function executing to long
                if  (tend-tbegin)*1000 >= MAIN_TIME_REFRESHING:
                    self.digitalPotChange = 1
                    MAIN_TIME_REFRESHING += 500
                    self.DIGITAL_BOX_MAIN.setInterval(MAIN_TIME_REFRESHING)
                # decrease main time refreshing if execute function is short
                else:
                    if (tend-tbegin)*1000 < MAIN_TIME_REFRESHING-200:
                        self.DIGITAL_BOX_MAIN.setInterval(MAIN_TIME_REFRESHING)
                        MAIN_TIME_REFRESHING -= 100
                        self.digitalPotChange = 0
                
            # save value error to check_error.txt file
            except ValueError:
                x = datetime.datetime.now()
                dateAndTime = x.strftime("%c")
                with open('check_error.txt', 'a') as f:
                    f.write(f'{errorNumber}{dateAndTime}{errorNumber}\n')
                    f.write('!!! Can not set any parameters(set_voltage,set_pwm1,2...)!!!\n')
                    f.write('Solution:\n')
                    f.write(f'-- Check digital box version(RPI - {VERZIJA_RPI} ESP - {VERZIJA_ESP}) and\n')
                    f.write(f'{errorNumber*2}\n')
                    f.write(traceback.format_exc())
                    f.write(f'{errorNumber*2}\n')
                    f.close()
            except:
                with open('check_error.txt', 'a') as f:
                    f.write(traceback.format_exc())
                f.close()
        
    def check_all_input(self):
        """
        check all input(read_adc,read_pwm,check_digital_pot, check_DAC_pot)
        extra timer for long executing function 
        """
        self.digitalPotIndex = 1
        sleep(0.2)
        try:
            self.read_adc()
        except Exception:
            self.read_adc_all = [0,0,0,0]
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{errorNumber}{dateAndTime}{errorNumber}\n')
                f.write('!!!Dont get anything from ADC read !!!\n')
                f.write('Solution:\n')
                f.write(f'-- Check digital box version(RPI - {VERZIJA_RPI} ESP - {VERZIJA_ESP}) or hardware problems with ADC read\n')
                f.write(f'{errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{errorNumber*2}\n')
            f.close()
        
        try:   
            self.read_pwm()
            
        except Exception:
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{errorNumber}{dateAndTime}{errorNumber}\n')
                f.write('!!!Dont get anything from PWM read !!!\n')
                f.write('Solution:\n')
                f.write(f'-- Check digital box version(RPI - {VERZIJA_RPI} ESP - {VERZIJA_ESP}) or hardware problems with ADC read\n')
                f.write(f'{errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{errorNumber*2}\n')
            f.close()
        
        self.check_digital_pot()
        self.check_DAC_pot()
        
        self.digitalPotIndex = 0
                
    def boxMarks(self,BOXMARKS):
        """
        open folder in data/boxMarks and get all marks name
        """
        try:
            BOX_MARKS = open(f"{BOX_MARKS_PATH}/{BOXMARKS}.txt", "r")
            self.BoxMarks.setStyleSheet(ButtonStyleOn)
            self.read_all_lines=BOX_MARKS.readlines()
            for name in self.read_all_lines:
                if name == f'INPUT{SPACE}':
                    try:
                        for index in range(DigitalInput):
                            input_text = eval(f'self.INPUT_{index}')
                            if self.read_all_lines[1].replace('\n','').split(',')[index] == '':
                                input_text.setText(f'IN{index}')
                            else:
                                input_text.setText(self.read_all_lines[1].replace('\n','').split(',')[index])
                    except IndexError:
                        input_text.setText(f'IN{index}')
                        
                if name == f'OUTPUT{SPACE}':
                    try:
                        for index in range(8):
                            output_text = eval(f'self.OUT{index}')
                            if self.read_all_lines[3].replace('\n','').split(',')[index] == '':
                                output_text.setText(f'out{index}')
                            else:
                                output_text.setText(self.read_all_lines[3].replace('\n','').split(',')[index])
                    except IndexError:
                        output_text.setText(f'out{index}')
                if name == f'DIGITAL_POT{SPACE}':
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
                
                
                if name == f'DAC_POT{SPACE}':
                    try:
                        for index in range(8):
                            digital_pot_text = eval(f'SetDacValue.labelDac{index}')
                            if self.read_all_lines[7].replace('\n','').split(',')[index] == '':
                                digital_pot_text.setText(f'Table{index}')
                            else:
                                digital_pot_text.setText(self.read_all_lines[7].replace('\n','').split(',')[index])
                            digital_pot_text.setFont(QFont('Arial', 10))
                    except IndexError:
                        digital_pot_text.setText(f'Table{index}')
                    except AttributeError:
                        print('!!! DAC not enough slider !!!')
                
                
                if name == f'READ_ADC{SPACE}':
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
                
                
                if name == f'SET_VOLTAGE{SPACE}':
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
            
                if name == f'READ_PWM1{SPACE}':
                    for index in range(2):
                        digital_pot_text = eval(f'self.labelPwm1_{index}')
                        digital_pot_text.setText(self.read_all_lines[13].replace('\n','').split(',')[index])
                        digital_pot_text.setFont(QFont('Arial', 10))
                
                if name == f'READ_PWM2{SPACE}':
                    for index in range(2):
                        digital_pot_text = eval(f'self.labelPwm2_{index}')
                        digital_pot_text.setText(self.read_all_lines[15].replace('\n','').split(',')[index])
                        digital_pot_text.setFont(QFont('Arial', 10)) 
            
                if name == f'SET_PWM1{SPACE}':
                    for index in range(2):
                        digital_pot_text = eval(f'self.labelSetPwm1_{index}')
                        digital_pot_text.setText(self.read_all_lines[17].replace('\n','').split(',')[index])
                        digital_pot_text.setFont(QFont('Arial', 10))  
                
                if name == f'SET_PWM2{SPACE}':
                    for index in range(2):
                        digital_pot_text = eval(f'self.labelSetPwm2_{index}')
                        digital_pot_text.setText(self.read_all_lines[19].replace('\n','').split(',')[index])
                        digital_pot_text.setFont(QFont('Arial', 10))
                if name == f'SET_FREQ{SPACE}':
                        digital_pot_text = eval(f'self.labelSetPwm3_0')
                        digital_pot_text.setText(self.read_all_lines[21].replace('\n',''))
                        digital_pot_text.setFont(QFont('Arial', 10))
                if name == f'SET_DUTY{SPACE}':
                        digital_pot_text = eval(f'self.labelSetPwm3_1')
                        digital_pot_text.setText(self.read_all_lines[23].replace('\n',''))
                        digital_pot_text.setFont(QFont('Arial', 10))
        except IndexError:
            
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{errorNumber}{dateAndTime}{errorNumber}\n')
                f.write('!!!Some name(INPUT,OUTPUT,DIGITAL_POT,...) do not have arguments!!!\n')
                f.write('Solution:\n')
                f.write(f'-- Check data/{BOXMARKS}.txt file and do as instructed(check readMe.txt file) \n')
                f.write(f'{errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{errorNumber*2}\n')
            f.close()
        
        except:
                with open('check_error.txt', 'a') as f:
                    f.write(traceback.format_exc())
                f.close()
    
    def animationConnect(self):
        self.connectBar.setVisible(True)
        for value in range(0,110,10):
            self.connectBar.setValue(value)
            sleep(0.2)
        self.connectBar.setVisible(False)
        self.connectBar.setValue(0)
    def connectBox(self,CONNECTBOX):
        """
        - connect digital box with RPI or direct with digital box(serial connection)
        - check if version is correct
        - show warning message if version is not correct  
        """
        self.backup_save()
        self.Connection = CONNECTBOX
        self.startStopSaving.setEnabled(False)
        self.resetExcelParameters()
        self.connectAnimation.start(self.animationConnect)
        try:
            print('connect')
            if self.index_refreshing >= 1:
                sleep(2)
                self.box.disconnect()
            
            if CONNECTBOX[0:3] =='COM':
                self.box = SERIALCONNECT(CONNECTBOX[0:5].replace(' ',''))
                VERSION = self.box.connect()
                self.label_errorSaveFile.setVisible(False)
                self.label_saveFile.setVisible(True)
                if VERSION >= VERZIJA_RPI:
                    self.index_refreshing +=1
                    self.DIGITAL_BOX_MAIN.start()
                    self.BOX_VERSION.setVisible(False)
                    self.warningMessagePot.setVisible(False)
                    self.warningMessageDac.setVisible(False)
                    self.BoxConnect.setStyleSheet(ButtonStyleOn)
                else:
                    sleep(2)
                    self.box.disconnect()
                    self.index_refreshing = 0
                    self.BoxConnect.setStyleSheet(ButtonStyleWhite)
                    self.BOX_VERSION.setVisible(True)
                    self.BOX_VERSION.setText(f"Current version digital box is {VERSION}.Version must be >= {VERZIJA_RPI}. Update box to the latest version if you want to use this application") 
            
            elif CONNECTBOX[0:3] =='ESP':
                self.box = WifiEsp32Connect(CONNECTBOX.replace('ESP32 - ',''))
                VERSION = self.box.connect()
                self.label_errorSaveFile.setVisible(False)
                self.label_saveFile.setVisible(True)
                if VERSION >= VERZIJA_ESP:
                    self.index_refreshing +=1
                    self.DIGITAL_BOX_MAIN.start()
                    self.dateTimeTimer.start()
                    self.BOX_VERSION.setVisible(False)
                    self.warningMessagePot.setVisible(False)
                    self.warningMessageDac.setVisible(False)
                    self.BoxConnect.setStyleSheet(ButtonStyleOn)
                else:
                    sleep(2)
                    self.box.disconnect()
                    self.index_refreshing = 0
                    self.BoxConnect.setStyleSheet(ButtonStyleWhite)
                    self.BOX_VERSION.setVisible(True)
                    self.BOX_VERSION.setText(f"Current version digital box is {VERSION}.Version must be >= {VERZIJA_ESP}. Update box to the latest version if you want to use this application") 
            
            elif CONNECTBOX[0:3] =='RPI':
                #print('connect to rpi')
                self.box = DAS(CONNECTBOX.replace('RPI - ',''))  #
                self.box.connect()
                sleep(2)
                VERSION =  self.box.box_version[0].strip()
                if VERSION >= VERZIJA_RPI:
                    self.index_refreshing +=1
                    self.DIGITAL_BOX_MAIN.start()
                    self.dateTimeTimer.start()
                    self.BOX_VERSION.setVisible(False)
                    self.warningMessagePot.setVisible(False)
                    self.warningMessageDac.setVisible(False)
                    self.BoxConnect.setStyleSheet(ButtonStyleOn)
                else:
                    sleep(2)
                    self.box.disconnect()
                    self.index_refreshing = 0
                    self.BOX_VERSION.setVisible(True)
                    self.BOX_VERSION.setText(f"Current version digital box is {VERSION}.Version must be >= {VERZIJA_RPI}. Update box to the latest version if you want to use this application") 
            
            self.ButtonHusaModel.setStyleSheet(ButtonStyleOff2)
            self.ButtonPyroSystem.setStyleSheet(ButtonStyleOff2)
            self.ButtonDacSet.setStyleSheet(ButtonStyleOff2)
            self.ButtonSetPot.setStyleSheet(ButtonStyleOff2)
            self.ButtonSetDac.setStyleSheet(ButtonStyleOff2)
            self.ButtonAutomation.setStyleSheet(ButtonStyleOff2)
            self.warningMessageAddFunction.setStyleSheet("color: black")
            self.warningMessageAddFunction.setText(f"ADDITIONAL FUNCTIONS")     
        except:
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{errorNumber}{dateAndTime}{errorNumber}\n')
                f.write(f'Das service is not connected to this ip {CONNECTBOX[6:]} \n')
                f.write('Solution:\n')
                f.write(f'-- Open supervisor {CONNECTBOX[6:]}:9001 (copy ip to this ip to browser) and check das service \n')
                f.write(f'-- Reset das service.Das service must be in running state \n')
                f.write('-- Computer and RPI must be in the same domain \n')
                f.write(f'-- RPI(das {VERZIJA_RPI}), digital box(third generation) and tester({VERZIJA_RPI}) must be updated \n')
                f.write(f'{errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{errorNumber*2}\n')
            f.close()

        self.connectParameters = 1
        self.box_is_connected +=1
        if self.box_is_connected >=2:
            self.box_is_connected =0     
    
    def digitalPotTable(self,potTable):
        """
        - activate selected digital pot slider
        - set min,max and interval for selected slider
        """
        #print(self.AllTable)
        for index,allPotTable in enumerate(self.AllTable):
            if allPotTable == potTable:
                self.AllTable.pop(index)
                self.SelectPotTable.clear()
                self.SelectPotTable.addItems(self.AllTable)
            
        for index,TablePot in enumerate(listDigitalPotTable()):
            try:
                if TablePot == potTable:
                    min,max = tableValueMaxMin(self,TablePot)
                    eval(f'self.digital_pot{index}.setMinimum(min-10)')
                    eval(f'self.digital_pot{index}.setMaximum(max+10)')
                    eval(f'self.digital_pot{index}.setTickInterval(int((max +(abs(min)))/20))')
                    eval(f'self.PotMax{index}.setText(str(max+10))')
                    eval(f'self.PotMin{index}.setText(str(min-10))')
                    eval(f'self.PotMin{index}.setStyleSheet(PotSlicerLabelStyle)')
                    eval(f'self.PotMax{index}.setStyleSheet(PotSlicerLabelStyle)')
                    R,G,B = sliderColor(self,index,min,max)
                    eval(f'self.digital_pot{index}.valueChanged.connect(self.SetDigitalPot{index})')
                    eval(f'self.labelDigitalPot{index}.setStyleSheet(InputStyleOn)')
                    eval(f'self.lcdNumber_digital_pot{index}.display(self.digital_pot{index}.value())')
                    eval(f'self.digital_pot{index}.setValue(min+20)')
                    eval(f'self.digital_pot{index}.setStyleSheet(f"background-color: rgb({R},{G},{B})")')
            except Exception:
                x = datetime.datetime.now()
                dateAndTime = x.strftime("%c")
                with open('check_error.txt', 'a') as f:
                    f.write(f'{errorNumber}{dateAndTime}{errorNumber}\n')
                    f.write('!!!Table{x.x}.txt change or in table missing pot value or temperature value !!!\n')
                    f.write('Solution:\n')
                    f.write('-- Dont change name!!! Name must be Table1.1,Table1.2--->Table3.1,Table3.2\n')
                    f.write('-- Table must have temperature and pot value\n')
                    f.write(f'{errorNumber*2}\n')
                    f.write(traceback.format_exc())
                    f.write(f'{errorNumber*2}\n')
                f.close()  
                  
    def BoxRefreshing(self):
        """
        - refresh box connection,digital pot table and select marks
        """
        self.backup_save()
        self.BoxConnect.setStyleSheet(ButtonStyleWhite)   
        self.BoxMarks.setStyleSheet(ButtonStyleWhite)
        self.SelectPotTable.setStyleSheet(ButtonStyleWhite)
        self.resetExcelParameters()
        self.indexButtonSave = 0
        self.repeatSaveData = 0
        if  self.index_refreshing == 0:
            self.BoxConnect.clear()
            self.ExcelFile.clear()
            self.BoxMarks.clear()
            self.SelectPotTable.clear()
            self.BoxConnect.addItems(listConnection())
            self.BoxMarks.addItems(listBoxMarks())
            self.SelectPotTable.addItems(listDigitalPotTable())
            self.ExcelFile.addItems(dataFile())
            self.BOX_VERSION.setVisible(False)
        else:
            sleep(2)
            self.index_refreshing +=1
            self.refreshSaveData.stop()
            #self.iconSaveData.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOff.png')))
            #self.startStopSaving.setIcon(self.iconSaveData)
            self.startStopSaving.setEnabled(False)
            self.DIGITAL_BOX_MAIN.stop()
            self.dateTimeTimer.stop()
            self.DIGITAL_BOX_MAIN.setInterval(1000)
            self.BoxConnect.clear()
            self.BoxMarks.clear()
            self.ExcelFile.clear()
            self.SelectPotTable.clear()
            self.label_connect.setText('BOX CONNECT')
            self.label_marks.setText('SELECT MARKS')
            self.BoxConnect.addItems(listConnection())
            self.BoxMarks.addItems(listBoxMarks())
            self.BoxMarks.setStyleSheet(ButtonStyleWhite)
            self.ExcelFile.setStyleSheet(ButtonStyleWhite)
            self.ExcelFile.addItems(dataFile())
            self.SelectPotTable.addItems(listDigitalPotTable())
            for index,TablePot in enumerate(listDigitalPotTable()):
                eval(f'self.labelDigitalPot{index}.setStyleSheet(MainScreenStyle)')
                eval(f'self.digital_pot{index}.setStyleSheet(MainScreenStyle)')
            self.AllTable = listDigitalPotTable()
            self.on_off.setIcon(self.iconOff)
            for index in range(8):
                eval(f'self.OUT{index}.setStyleSheet(ButtonStyleOff2)')
                eval(f'self.OUT{index}.setIcon(self.iconSwitchOff)')
                
            for index in range(6):
                eval(f'self.digital_pot{index}.setStyleSheet(ButtonStyleWhite)')
                eval(f'self.digital_pot{index}.value()')
                #eval(f'self.digital_pot{index}.setEnabled(False)')
                eval(f'self.lcdNumber_digital_pot{index}.display(0)')
            
            sleep(1)
            self.box.disconnect()
            #print('disconnected')
    
        if self.index_refreshing >=2:
            self.index_refreshing =0
 ################################## ON/OFF AND OUTPUT BUTTONS #################################      
    def button_OnOff(self):
        self.index_on_off +=1
        if self.index_on_off >=2:
            self.index_on_off = 0
            self.on_off.setIcon(self.iconOff)
        else:
             self.on_off.setIcon(self.iconOn)
    
    def output0(self):
        self.index_out[0] +=1
        if self.index_out[0] >= 2:
            self.index_out[0] = 0
            self.OUT0.setStyleSheet(ButtonStyleOff2) 
            self.OUT0.setIcon(self.iconSwitchOff)
        else:
            self.OUT0.setStyleSheet(ButtonStyleOn2)
            self.OUT0.setIcon(self.iconSwitchOn)
    
    def output1(self):
        self.index_out[1] +=1
        if self.index_out[1] >=2:
            self.index_out[1] =0 
            self.OUT1.setStyleSheet(ButtonStyleOff2) 
            self.OUT1.setIcon(self.iconSwitchOff)
        else:
            self.OUT1.setStyleSheet(ButtonStyleOn2)
            self.OUT1.setIcon(self.iconSwitchOn)
    
    def output2(self):
        self.index_out[2] +=1
        if self.index_out[2] >=2:
            self.index_out[2] =0  
            self.OUT2.setStyleSheet(ButtonStyleOff2)
            self.OUT2.setIcon(self.iconSwitchOff) 
        else:
            self.OUT2.setStyleSheet(ButtonStyleOn2)
            self.OUT2.setIcon(self.iconSwitchOn)
    
    def output3(self):
        self.index_out[3] +=1
        if self.index_out[3] >=2:
            self.index_out[3] =0  
            self.OUT3.setStyleSheet(ButtonStyleOff2)
            self.OUT3.setIcon(self.iconSwitchOff) 
        else:
            self.OUT3.setStyleSheet(ButtonStyleOn2)
            self.OUT3.setIcon(self.iconSwitchOn)
    
    def output4(self):
        self.index_out[4] +=1
        if self.index_out[4] >=2:
            self.index_out[4] =0
            self.OUT4.setStyleSheet(ButtonStyleOff2)
            self.OUT4.setIcon(self.iconSwitchOff)
        else:
            self.OUT4.setStyleSheet(ButtonStyleOn2)
            self.OUT4.setIcon(self.iconSwitchOn)   
    
    def output5(self):
        self.index_out[5] +=1
        if self.index_out[5] >=2:
            self.index_out[5] =0  
            self.OUT5.setStyleSheet(ButtonStyleOff2)
            self.OUT5.setIcon(self.iconSwitchOff)
        else:
            self.OUT5.setStyleSheet(ButtonStyleOn2)
            self.OUT5.setIcon(self.iconSwitchOn)
    
    def output6(self):
        self.index_out[6] +=1
        if self.index_out[6] >=2:
            self.index_out[6] =0
            self.OUT6.setStyleSheet(ButtonStyleOff2)
            self.OUT6.setIcon(self.iconSwitchOff)
        else:
            self.OUT6.setStyleSheet(ButtonStyleOn2)
            self.OUT6.setIcon(self.iconSwitchOn) 
    
    def output7(self):
        self.index_out[7] +=1
        if self.index_out[7] >=2:
            self.index_out[7] =0
            self.OUT7.setStyleSheet(ButtonStyleOff2)
            self.OUT7.setIcon(self.iconSwitchOff)
        else:
            self.OUT7.setStyleSheet(ButtonStyleOn2)
            self.OUT7.setIcon(self.iconSwitchOn)
 ##################################### SLIDERS #################################################   
    def SetDigitalPot0(self):
        """
        - if box is connected then slider is activated
        - show value on the slider and ldc display
        """
        if self.index_refreshing >= 1:
            min,max = tableValueMaxMin(self,'Table1.1')
            R,G,B = sliderColor(self,0,min,max)
            self.digital_pot0.setStyleSheet(f"background-color: rgb({R},{G},{B})")
            self.lcdNumber_digital_pot0.display(self.digital_pot0.value())
        return self.digital_pot0.value()
                 
    def SetDigitalPot1(self):
        """
        - if box is connected then slider is activated
        - show value on the slider and ldc display
        """
        if self.index_refreshing >= 1:
            min,max = tableValueMaxMin(self,'Table1.2')
            R,G,B = sliderColor(self,1,min,max)
            self.digital_pot1.setStyleSheet(f"background-color: rgb({R},{G},{B})")
            self.lcdNumber_digital_pot1.display(self.digital_pot1.value())
        return self.digital_pot1.value()
    
    def SetDigitalPot2(self):
        """
        - if box is connected then slider is activated
        - show value on the slider and ldc display
        """
        if self.index_refreshing >= 1:
            min,max = tableValueMaxMin(self,'Table2.1')
            R,G,B = sliderColor(self,2,min,max)
            self.digital_pot2.setStyleSheet(f"background-color: rgb({R},{G},{B})")
            self.lcdNumber_digital_pot2.display(self.digital_pot2.value())
        return self.digital_pot2.value()
    
    def SetDigitalPot3(self):
        """
        - if box is connected then slider is activated
        - show value on the slider and ldc display
        """
        if self.index_refreshing >= 1:
            min,max = tableValueMaxMin(self,'Table2.2')
            R,G,B = sliderColor(self,3,min,max)
            self.digital_pot3.setStyleSheet(f"background-color: rgb({R},{G},{B})")
            self.lcdNumber_digital_pot3.display(self.digital_pot3.value())
        return self.digital_pot3.value()
    
    def SetDigitalPot4(self):
        """
        - if box is connected then slider is activated
        - show value on the slider and ldc display
        """
        if self.index_refreshing >= 1:
            min,max = tableValueMaxMin(self,'Table3.1')
            R,G,B = sliderColor(self,4,min,max)
            self.digital_pot4.setStyleSheet(f"background-color: rgb({R},{G},{B})")
            self.lcdNumber_digital_pot4.display(self.digital_pot4.value())
        return self.digital_pot4.value()
    
    def SetDigitalPot5(self):
        """
        - if box is connected then slider is activated
        - show value on the slider and ldc display
        """
        if self.index_refreshing >= 1:
            min,max = tableValueMaxMin(self,'Table3.2')
            R,G,B = sliderColor(self,5,min,max)
            self.digital_pot5.setStyleSheet(f"background-color: rgb({R},{G},{B})")
            self.lcdNumber_digital_pot5.display(self.digital_pot5.value())
        return self.digital_pot5.value()
  ##############################################################################################  
    def check_input(self):
        """
        read digital input from digital box
        """
        global input
        input = self.box.digital_in[:]
        return input
    
    def check_output(self):
        """
        set all output parameters and on/off button when state change
        """
        begin_parameter = [self.index_on_off,self.index_out[0],self.index_out[1],self.index_out[2],self.index_out[3],self.index_out[4],self.index_out[5],self.index_out[6],self.index_out[7]]
        if begin_parameter != change_parameters or self.connectParameters == 1:
            #print(begin_parameter,change_parameters)
            if (self.index_on_off % 2) == 0:
                #self.on_off.setIcon(self.iconOff)
                self.box.main = 0
                change_parameters[0]= 0
            else:
                #self.on_off.setIcon(self.iconOn)
                self.box.main = 1
                change_parameters[0]= 1
            
            parameter_true = tuple([i for i, val in enumerate(begin_parameter[1:]) if  val])
            if parameter_true:
                activate_output(self,parameter_true,True)
            
            parameter_false = tuple([i for i, val in enumerate(begin_parameter[1:]) if not val])
            if parameter_false:
                activate_output(self,parameter_false,False) 
   
            if (self.index_out[0] % 2) == 0:
                change_parameters[1]= 0
                self.OUT0.setStyleSheet(ButtonStyleOff2)
                self.OUT0.setIcon(self.iconSwitchOff) 
            else:
                change_parameters[1]= 1
                self.OUT0.setStyleSheet(ButtonStyleOn2)
                self.OUT0.setIcon(self.iconSwitchOn) 
                
            if (self.index_out[1] % 2) == 0:
                change_parameters[2]= 0
                self.OUT1.setStyleSheet(ButtonStyleOff2)
                self.OUT1.setIcon(self.iconSwitchOff)
            else:
                change_parameters[2]= 1
                self.OUT1.setStyleSheet(ButtonStyleOn2)
                self.OUT1.setIcon(self.iconSwitchOn) 
                
            if (self.index_out[2] % 2) == 0:
                change_parameters[3]= 0    
                self.OUT2.setStyleSheet(ButtonStyleOff2)
                self.OUT2.setIcon(self.iconSwitchOff)
            else:
                change_parameters[3]= 1
                self.OUT2.setStyleSheet(ButtonStyleOn2)
                self.OUT2.setIcon(self.iconSwitchOn) 
                
            if (self.index_out[3] % 2) == 0:
                change_parameters[4]= 0
                self.OUT3.setStyleSheet(ButtonStyleOff2)
                self.OUT3.setIcon(self.iconSwitchOff)
            else:
                change_parameters[4]= 1
                self.OUT3.setStyleSheet(ButtonStyleOn2)
                self.OUT3.setIcon(self.iconSwitchOn)
                
            if (self.index_out[4] % 2) == 0:
                change_parameters[5]= 0 
                self.OUT4.setStyleSheet(ButtonStyleOff2)
                self.OUT4.setIcon(self.iconSwitchOff)
            else:
                change_parameters[5]= 1
                self.OUT4.setStyleSheet(ButtonStyleOn2)
                self.OUT4.setIcon(self.iconSwitchOn)
                
            if (self.index_out[5] % 2) == 0:
                change_parameters[6]= 0
                self.OUT5.setStyleSheet(ButtonStyleOff2)
                self.OUT5.setIcon(self.iconSwitchOff)
            else:
                change_parameters[6]= 1
                self.OUT5.setStyleSheet(ButtonStyleOn2) 
                self.OUT5.setIcon(self.iconSwitchOn)
                  
            if (self.index_out[6] % 2) == 0:
                change_parameters[7]= 0
                self.OUT6.setStyleSheet(ButtonStyleOff2)
                self.OUT6.setIcon(self.iconSwitchOff)
            else: 
                change_parameters[7]= 1
                self.OUT6.setStyleSheet(ButtonStyleOn2)
                self.OUT6.setIcon(self.iconSwitchOn)
            
            if (self.index_out[7] % 2) == 0:
                change_parameters[8]= 0
                self.OUT7.setStyleSheet(ButtonStyleOff2)
                self.OUT7.setIcon(self.iconSwitchOff) 
            else:
                change_parameters[8]= 1
                self.OUT7.setStyleSheet(ButtonStyleOn2)
                self.OUT7.setIcon(self.iconSwitchOn) 
            self.connectParameters = 0
   
    def check_digital_pot(self):
        """
        set digital pot value when value change
        """
        global beginPotValue
        self.readDigitalPot0 = self.digital_pot0.value()
        self.readDigitalPot1 = self.digital_pot1.value()
        self.readDigitalPot2 = self.digital_pot2.value()
        self.readDigitalPot3 = self.digital_pot3.value()
        self.readDigitalPot4 = self.digital_pot4.value()
        self.readDigitalPot5 = self.digital_pot5.value()
        ###############################digital potentiometer 1 ######################################################
        if beginPotValue[0] != self.readDigitalPot0:
            set_digital_pot(self,self.readDigitalPot0,tableIndex = 1,slider =1,chipSelect = 1)
            beginPotValue[0] = self.readDigitalPot0
        elif beginPotValue[1] != self.readDigitalPot1:
            set_digital_pot(self,self.readDigitalPot1,tableIndex = 1,slider =2,chipSelect = 1)
            beginPotValue[1] = self.readDigitalPot1
        ###############################digital potentiometer 2 ######################################################
        elif beginPotValue[2] != self.readDigitalPot2:
            set_digital_pot(self,self.readDigitalPot2,tableIndex = 2,slider =1,chipSelect = 2)
            beginPotValue[2] = self.readDigitalPot2
        elif beginPotValue[3] != self.readDigitalPot3:
            set_digital_pot(self,self.readDigitalPot3,tableIndex = 2,slider =2,chipSelect = 2)
            beginPotValue[3] = self.readDigitalPot3
         ###############################digital potentiometer 3 ######################################################
        elif beginPotValue[4] != self.readDigitalPot4:
            set_digital_pot(self,self.readDigitalPot4,tableIndex = 3,slider =1,chipSelect = 3)
            beginPotValue[4] = self.readDigitalPot4      
        elif beginPotValue[5] != self.readDigitalPot5:
            set_digital_pot(self,self.readDigitalPot5,tableIndex = 3,slider =2,chipSelect = 3)
            beginPotValue[5] = self.readDigitalPot5
            
    def read_adc(self):
        """
        read adc value and show on display
        """
        self.read_adc_all = self.box.read_adc[0:4]
        #print(self.read_adc_all)
        self.readADC0.display(float(self.read_adc_all[0]))
        self.readADC1.display(float(self.read_adc_all[1]))
        self.readADC2.display(float(self.read_adc_all[2]))
        self.readADC3.display(float(self.read_adc_all[3]))
    
    def read_pwm(self):
        """
        read pwm1 and pwm2 and show on the display
        """
        self.read_pwm_all = self.box.read_pwm[:]
        self.ReadPwm1.display(self.read_pwm_all[0]['f'])
        self.ReadDuty1.display(self.read_pwm_all[0]['d'])
        self.ReadPwm2.display(self.read_pwm_all[1]['f'])
        self.ReadDuty2.display(self.read_pwm_all[1]['d'])
        
    def set_voltage(self):
        """
        set voltage when value change
        """
        self.readVoltage =[self.SetVoltage0.value(),self.SetVoltage1.value(),self.SetVoltage2.value(),self.SetVoltage3.value()]
        if beginSetVoltage[0] != self.readVoltage[0]:
            self.box.set_voltage = (0,self.readVoltage[0])
            beginSetVoltage[0] = self.readVoltage[0]
        if beginSetVoltage[1] != self.readVoltage[1]:
            self.box.set_voltage = (1,self.readVoltage[1])
            beginSetVoltage[1] = self.readVoltage[1]
        if beginSetVoltage[2] != self.readVoltage[2]:
            self.box.set_voltage = (2,self.readVoltage[2])
            beginSetVoltage[2] = self.readVoltage[2]
        if beginSetVoltage[3] != self.readVoltage[3]:
            self.box.set_voltage = (3,self.readVoltage[3])
            beginSetVoltage[3] = self.readVoltage[3]
    
    def SetFrequencyBar1(self):
        """
        - set frequency with slider
        - color the slider when value change
        """
       
        self.SetFrequency1.setValue(self.SetPwmBar1.value())
        self.SetPwmBar1.setStyleSheet(f"background-color: rgb({250-int((self.SetPwmBar1.value()/100))},{250-int((self.SetPwmBar1.value()/100))},255)")
    def SetFrequencyBar2(self):
        """
        - set frequency with slider
        - color the slider when value change
        """
        self.SetFrequency2.setValue(self.SetPwmBar2.value())
        self.SetPwmBar2.setStyleSheet(f"background-color: rgb({250-int((self.SetPwmBar2.value()/100))},{250-int((self.SetPwmBar2.value()/100))},255)")
    def set_pwm1(self):
        """
        set PWM1 when value change
        """
        self.BeginValuePwm1=self.setPwmBegin1.value()
        self.EndValuePwm1=self.setPwmEnd1.value()
        self.SetPwmBar1.setMinimum(self.BeginValuePwm1)
        self.SetPwmBar1.setMaximum(self.EndValuePwm1)
        self.readPwm1 =[self.SetFrequency1.value(),self.SetDuty1.value()]
        self.SetPwmBar1.setValue(self.SetFrequency1.value())
        if setPwm1[0] != self.readPwm1[0]:
            self.box.set_pwm1 = (self.readPwm1[0],self.readPwm1[1])
            setPwm1[0] = self.readPwm1[0]
        if setPwm1[1] != self.readPwm1[1]:
            self.box.set_pwm1 = (self.readPwm1[0],self.readPwm1[1])
            setPwm1[1] = self.readPwm1[1]
            
    def set_pwm2(self):
        """
        set PWM2 when value change
        """
        self.BeginValuePwm2=self.setPwmBegin2.value()
        self.EndValuePwm2=self.setPwmEnd2.value()
        self.SetPwmBar2.setMinimum(self.BeginValuePwm2)
        self.SetPwmBar2.setMaximum(self.EndValuePwm2)
        self.readPwm2 =[self.SetFrequency2.value(),self.SetDuty2.value()]
        self.SetPwmBar2.setValue(self.SetFrequency2.value())
        if setPwm2[0] != self.readPwm2[0]:
            self.box.set_pwm2 = (self.readPwm2[0],self.readPwm2[1])
            setPwm2[0] = self.readPwm2[0]
        if setPwm2[1] != self.readPwm2[1]:
            self.box.set_pwm2 = (self.readPwm2[0],self.readPwm2[1])
            setPwm2[1] = self.readPwm2[1]
     
    def set_frequency_and_duty_old(self):
        """
        set frequency and duty value when value change
        """
        self.readPwmOld =[self.SetFrequencyOld.value(),self.SetDutyOld.value()]
       
        if setPwmOld[0] != self.readPwmOld[0]:
            self.box.frequency_out = self.readPwmOld[0]
            setPwmOld[0] = self.readPwmOld[0]
        
        if setPwmOld[1] != self.readPwmOld[1]:
            self.box.duty_cycle_out = self.readPwmOld[1]
            setPwmOld[1] = self.readPwmOld[1]
                   
    def input_state_indicate(self):
        """
        color digital input state
        """
        self.read_input = self.check_input()
        for index in range(DigitalInput):
            if self.read_input[index]== True:
                eval(f'self.INPUT_{index}.setStyleSheet(InputStyleOn)')
                change_input[index] = True

            elif self.read_input[index]== False:
                eval(f'self.INPUT_{index}.setStyleSheet(InputStyleOff)')
                change_input[index] = False       
########################## OPEN SCREEN ###########################################################
    def buttonHusaModel(self):
        """
        - show screen husa if box is connected
        - if box is not connected show massage error
        """
        if self.index_refreshing >= 1:
            if (self.index_extras[0] % 2) == 0:
                self.ButtonHusaModel.setStyleSheet(ButtonStyleOn2)
                HusaModelWindow.show()
            else: 
                self.ButtonHusaModel.setStyleSheet(ButtonStyleOff2)
                HusaModelWindow.close()
        else:
            self.warningMessageAddFunction.setStyleSheet("color: red")
            self.warningMessageAddFunction.setText(f"!!! CONNECT DIGITAL BOX !!!") 
            self.ButtonHusaModel.setStyleSheet(ButtonStyleOff2)
        self.index_extras[0] +=1
        if self.index_extras[0] >=2:
            self.index_extras[0] =0 
    
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
                PyroSetSystem.show()
            else: 
                self.ButtonPyroSystem.setStyleSheet(ButtonStyleOff2)
                PyroSetSystem.close()
        else:
            self.warningMessageAddFunction.setStyleSheet("color: red")
            self.warningMessageAddFunction.setText(f"!!! CONNECT DIGITAL BOX !!!") 
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
            SetDacValue.show()
        else:
            self.ButtonDacSet.setStyleSheet(ButtonStyleOff2)
            SetDacValue.close()
            
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
                self.labelTableOpenError.setText(f"!!! CREATE POT TABLE IS OPEN. GUI STOPPED!!!")
                self.labelTableOpenError.setVisible(True)
                self.ButtonSetPot.setStyleSheet(ButtonStyleOn2)
                PotTableSet.show()
                self.DIGITAL_BOX_MAIN.stop()
                self.DIGITAL_BOX_MAIN.setInterval(1000)
                self.ReadSetPotDac.start()
                
            else: 
                self.labelTableOpenError.setVisible(False)
                self.ButtonSetPot.setStyleSheet(ButtonStyleOff2)
                PotTableSet.close()
                self.ReadSetPotDac.stop()
                self.DIGITAL_BOX_MAIN.start()
        else:
            self.warningMessagePot.setVisible(True)
            self.warningMessagePot.setText(f"!!! CONNECT DIGITAL BOX !!!") 
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
                self.labelTableOpenError.setText(f"!!! CREATE DAC TABLE IS OPEN. GUI STOPPED!!!")
                self.labelTableOpenError.setVisible(True)
                self.ButtonSetDac.setStyleSheet(ButtonStyleOn2)
                DacTableCreate.show()
                self.DIGITAL_BOX_MAIN.stop()
                self.DIGITAL_BOX_MAIN.setInterval(1000)
                self.ReadSetPotDac.start()
                
            else:
                self.labelTableOpenError.setVisible(False)
                self.ButtonSetDac.setStyleSheet(ButtonStyleOff2)
                DacTableCreate.close()
                self.ReadSetPotDac.stop()
                self.DIGITAL_BOX_MAIN.start()
        else:
            self.warningMessageDac.setVisible(True)
            self.warningMessageDac.setText(f"!!! CONNECT DIGITAL BOX !!!") 
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
            RunAutoTest.show()
        else:
            self.ButtonCreateAutoTest.setStyleSheet(ButtonStyleOff2)
            RunAutoTest.close()
        self.index_extras[7] +=1
        if self.index_extras[7] >=2:
            self.index_extras[7] =0   
    
    def closeRunAutoTest(self):
        """
        - close screen closeRunAutoTest
        """
        self.index_extras[6] +=1
        self.ButtonCreateAutoTest.setStyleSheet(ButtonStyleOff2)
    
    def check_DAC_pot(self):
        """
        - if value change send dac value
        """
        global beginDacValue
        self.readDac0 = SetDacValue.dac_pot0.value()
        self.readDac1 = SetDacValue.dac_pot1.value()
        self.readDac2 = SetDacValue.dac_pot2.value()
        self.readDac3 = SetDacValue.dac_pot3.value()
        self.readDac4 = SetDacValue.dac_pot4.value()
        self.readDac5 = SetDacValue.dac_pot5.value()
        self.readDac6 = SetDacValue.dac_pot6.value()
        self.readDac7 = SetDacValue.dac_pot7.value()
        ############################### DAC VALUE 1 ######################################################
        if beginDacValue[0] != self.readDac0:
            set_DAC(self,self.readDac0,tableIndex = 0,slider =1)
            beginDacValue[0] = self.readDac0
        ############################### DAC VALUE 2 ######################################################
        elif beginDacValue[1] != self.readDac1:
            set_DAC(self,self.readDac1,tableIndex = 1,slider =2)
            beginDacValue[1] = self.readDac1
        ############################### DAC VALUE 3 ######################################################
        elif beginDacValue[2] != self.readDac2:
            set_DAC(self,self.readDac2,tableIndex = 2,slider =3)
            beginDacValue[2] = self.readDac2
        ############################### DAC VALUE 4 ######################################################
        elif beginDacValue[3] != self.readDac3:
            set_DAC(self,self.readDac3,tableIndex = 3,slider =4)
            beginDacValue[3] = self.readDac3
         ############################### DAC VALUE 5 ######################################################
        elif beginDacValue[4] != self.readDac4:
            set_DAC(self,self.readDac4,tableIndex = 4,slider =5)
            beginDacValue[4] = self.readDac4
        ############################### DAC VALUE 6 ######################################################
        elif beginDacValue[5] != self.readDac5:
            set_DAC(self,self.readDac5,tableIndex = 5,slider =6)
            beginDacValue[5] = self.readDac5
        elif beginDacValue[6] != self.readDac6:
            set_DAC(self,self.readDac6,tableIndex = 6,slider =7)
            beginDacValue[6] = self.readDac6
        elif beginDacValue[7] != self.readDac7:
            set_DAC(self,self.readDac7,tableIndex = 7,slider =8)
            beginDacValue[7] = self.readDac7    

    def createPotTable(self):
        """
        - if value change send pot value
        
        """
        global beginSetPot
        self.DIGITAL_BOX_MAIN.stop()
        try:
            readPot = PotTableSet.Pot_value.value()
            TableFirstMin,TableFirstMax = tablePotMaxMin(self,f"{PotTableSet.tableSelection()[0:5]}{PotTableSet.tableSelection()[5]}.1")
            #print('table-->',f"{PotTableSet.tableSelection()[0:5]}{PotTableSet.tableSelection()[5]}.1")
            #print('max=',TableFirstMax)
            if beginSetPot != readPot:
                if PotTableSet.tableSelection()[7] == '1':
                    PotTableSet.closeLableError()
                    if readPot <= 255:
                        self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),0],readPot)
                        self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),1,2,3],0)
                    elif readPot > 255 and readPot <= 255*2:
                        self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),0],255)
                        self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),1],readPot-255)
                        self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),2,3],0)
                    elif readPot > 255*2 and readPot <= 255*3:
                        self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),0,1],255)
                        self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),2],readPot-255*2)
                        self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),3],0)
                    elif readPot > 255*3:
                        self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),0,1,2],255)
                        self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),3],readPot-255*3)
                    beginSetPot = readPot
                if PotTableSet.tableSelection()[7] == '2':
                    self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),4,5],0)
                    if TableFirstMax <= 255:
                        PotTableSet.closeLableError()
                        if readPot <= 255:
                            self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),1],readPot)
                            self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),2,3],0)
                        elif readPot > 255 and readPot <= 255*2:
                            self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),1],255)
                            self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),2],readPot-255)
                            self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),3],0)
                        elif readPot > 255*2 and readPot <= 255*3:
                            self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),0,1,2],255)
                            self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),3],readPot-255*2)
                    elif TableFirstMax > 255 and TableFirstMax <= 255*2:
                        PotTableSet.closeLableError()
                        if readPot <= 255:
                            self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),2],readPot)
                            self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),3],0)
                        elif readPot > 255 and readPot <= 255*2:
                            self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),2],255)
                            self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),3],readPot)
                    elif TableFirstMax > 255*2 and TableFirstMax <= 255*3:
                        PotTableSet.closeLableError()
                        if readPot <= 255:
                            self.box.set_digital_pot([int(PotTableSet.tableSelection()[5]),3],readPot)
                           
                    elif TableFirstMax > 255*3:
                        PotTableSet.showLableError(PotTableSet.tableSelection()[5])
                    beginSetPot = readPot
                #print(self.box.digital_pot[:])
        except ValueError:
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{errorNumber}{dateAndTime}{errorNumber}\n')
                f.write(f'!!! {PotTableSet.tableSelection()[0:5]}{PotTableSet.tableSelection()[5]}.1 is empty or not created properly  !!!\n')
                f.write('Solution:\n')
                f.write(f' Check {PotTableSet.tableSelection()[0:5]}{PotTableSet.tableSelection()[5]}.1 and try again \n')
                f.write(f'{errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{errorNumber*2}\n')
            f.close()
    
    def createDacTable(self):
        """
        - if value change set dac value
        """
        global beginDacPot
        readDac = DacTableCreate.Dac_value.value()
        self.DIGITAL_BOX_MAIN.stop()
        if beginDacPot != readDac:
            self.box.set_analog_out(int(DacTableCreate.tableSelection())-1,readDac)
            beginDacPot = readDac               

class SetDacPot(QMainWindow):
    def __init__(self):
        super().__init__()
        ########################## SCREEN PATH CONVERT #############################
        DacScreen = os.path.abspath(f"{QT_DESIGNER_PATH}/DacTable.ui")
        loadUi(str(DacScreen),self)
        self.setWindowTitle('SET DAC')
        self.setFixedSize(960, 705)
        self.setStyleSheet(MainScreenStyle)
        ##########################SET SLIDER STYLE #############################
        try:
            for index in range(8):
                min,max = dacValueMaxMin(self,f'Table{index+1}')
                eval(f'self.dac_pot{index}.setMinimum(min-10)')
                eval(f'self.dac_pot{index}.setMaximum(max+10)')
                eval(f'self.dac_pot{index}.setTickInterval(int((max +(abs(min)))/10))')
                eval(f'self.DacMax{index}.setText(str(max+10))')
                eval(f'self.DacMin{index}.setText(str(min-10))')
                eval(f'self.DacMin{index}.setStyleSheet(PotSlicerLabelStyle)')
                eval(f'self.DacMax{index}.setStyleSheet(PotSlicerLabelStyle)')
                R,G,B = sliderColorDac(self,index,min,max)
                eval(f'self.dac_pot{index}.valueChanged.connect(self.SetDacPot{index})')
                eval(f'self.labelDac{index}.setStyleSheet(ButtonStyleOn)')
        except Exception:
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{errorNumber}{dateAndTime}{errorNumber}\n')
                f.write('!!!Table{x}.txt change or in table missing DAC value or temperature value !!!\n')
                f.write('Solution:\n')
                f.write('-- Dont change name!!! Name must be Table1-->Table8\n')
                f.write('-- Table must have temperature and DAC value\n')
                f.write(f'{errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{errorNumber*2}\n')
            f.close()  
        #######################################################################
    def closeEvent(self, event):
        """
        - close Dac screen
        """
        mainWindow.closeDacScreen()    
        
    def SetDacPot0(self):
        """
        - return dac value
        - set background slider color
        """
        min,max = dacValueMaxMin(self,'Table1')
        R,G,B = sliderColorDac(self,0,min,max)
        self.dac_pot0.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot0.display(self.dac_pot0.value())
        return self.dac_pot0.value()
                 
    def SetDacPot1(self):
        """
        - return dac value
        - set background slider color
        """
        min,max = dacValueMaxMin(self,'Table2')
        R,G,B = sliderColorDac(self,1,min,max)
        self.dac_pot1.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot1.display(self.dac_pot1.value())
        return self.dac_pot1.value()
    
    def SetDacPot2(self):
        """
        - return dac value
        - set background slider color
        """
        min,max = dacValueMaxMin(self,'Table3')
        R,G,B = sliderColorDac(self,2,min,max)
        self.dac_pot2.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot2.display(self.dac_pot2.value())
        return self.dac_pot2.value()
    
    def SetDacPot3(self):
        """
        - return dac value
        - set background slider color
        """ 
        min,max = dacValueMaxMin(self,'Table4')
        R,G,B = sliderColorDac(self,3,min,max)
        self.dac_pot3.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot3.display(self.dac_pot3.value())
        return self.dac_pot3.value()

    def SetDacPot4(self):
        """
        - return dac value
        - set background slider color
        """
        min,max = dacValueMaxMin(self,'Table5')
        R,G,B = sliderColorDac(self,4,min,max)
        self.dac_pot4.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot4.display(self.dac_pot4.value())
        return self.dac_pot4.value()

    def SetDacPot5(self):
        """
        - return dac value
        - set background slider color
        """
        min,max = dacValueMaxMin(self,'Table6')
        R,G,B = sliderColorDac(self,5,min,max)
        self.dac_pot5.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot5.display(self.dac_pot5.value())
        return self.dac_pot5.value()

    def SetDacPot6(self):
        """
        - return dac value
        - set background slider color
        """
        min,max = dacValueMaxMin(self,'Table7')
        R,G,B = sliderColorDac(self,6,min,max)
        self.dac_pot6.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot6.display(self.dac_pot6.value())
        return self.dac_pot6.value()
    
    def SetDacPot7(self):
        """
        - return dac value
        - set background slider color
        """
        min,max = dacValueMaxMin(self,'Table8')
        R,G,B = sliderColorDac(self,7,min,max)
        self.dac_pot7.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot7.display(self.dac_pot7.value())
        return self.dac_pot7.value()    
class HusaSetModule(QMainWindow):
    def __init__(self):
        super().__init__()
        ########################## SCREEN PATH CONVERT #############################
        HusaScreen = os.path.abspath(f"{QT_DESIGNER_PATH}/HusaSetModel.ui")
        loadUi(str(HusaScreen),self)
        self.setWindowTitle('HUSA SET PB/LB MODULE')
        self.setFixedSize(380, 450)
        ################## ALL LB PB MODEL BUTTON ###################################
        self.setStyleSheet(MainScreenStyle)
        self.MODEL_1.clicked.connect(self.set_model_1)
        self.MODEL_2.clicked.connect(self.set_model_2)
        self.MODEL_3.clicked.connect(self.set_model_3)
        self.MODEL_4.clicked.connect(self.set_model_4)
        self.MODEL_5.clicked.connect(self.set_model_5)
        self.MODEL_6.clicked.connect(self.set_model_6)
        self.MODEL_7.clicked.connect(self.set_model_7)
        self.MODEL_8.clicked.connect(self.set_model_8)
        self.MODEL_9.clicked.connect(self.set_model_9)
        self.MODEL_10.clicked.connect(self.set_model_10)
        self.MODEL_11.clicked.connect(self.set_model_11)
        self.M1_LB.clicked.connect(self.set_LB_model_1)
        self.M2_LB.clicked.connect(self.set_LB_model_2)
        self.M3_LB.clicked.connect(self.set_LB_model_3)
        self.M4_LB.clicked.connect(self.set_LB_model_4)
        self.M5_LB.clicked.connect(self.set_LB_model_5)
        self.M6_LB.clicked.connect(self.set_LB_model_6)
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')

    def closeEvent(self, event):
        """
        - close husa screen
        """
        mainWindow.closeHusaScreen()    
      ########## AUTO SET HUSA MODEL PB AND LB MODEL ############################
    def set_model_1(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_1.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M1')
        LB_MODEL = getLBModel(self,'M1')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
     
    def set_model_2(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_2.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M2')
        LB_MODEL = getLBModel(self,'M2')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
        
    def set_model_3(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_3.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M3')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
    
    def set_model_4(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_4.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M4')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
 
    def set_model_5(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_5.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M5')    
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
        
    def set_model_6(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_6.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M6')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
       
    def set_model_7(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_7.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M7')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
       
    def set_model_8(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_8.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M8')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
      
    def set_model_9(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_9.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M9')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
    
    def set_model_10(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_10.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M10')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
    
    def set_model_11(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_11.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M11')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
    ########## SET ONLY LB MODEL ##################################################    
    def set_LB_model_1(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.M1_LB.setStyleSheet(ButtonStyleOn2)
        mainWindow.husaSetLBModule('M1')
    
    def set_LB_model_2(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.M2_LB.setStyleSheet(ButtonStyleOn2)
        mainWindow.husaSetLBModule('M2')
    
    def set_LB_model_3(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.M3_LB.setStyleSheet(ButtonStyleOn2)
        mainWindow.husaSetLBModule('M3')
    
    def set_LB_model_4(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.M4_LB.setStyleSheet(ButtonStyleOn2)
        mainWindow.husaSetLBModule('M4')      
    
    def set_LB_model_5(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.M5_LB.setStyleSheet(ButtonStyleOn2)
        mainWindow.husaSetLBModule('M5')
    
    def set_LB_model_6(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.M6_LB.setStyleSheet(ButtonStyleOn2)
        mainWindow.husaSetLBModule('M6')
class Bio21PyroSetSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        ########################## SCREEN PATH CONVERT #############################
        PyroScreen = os.path.abspath(f"{QT_DESIGNER_PATH}/Bio21PyroSetSystem.ui")
        loadUi(str(PyroScreen),self)
        self.setWindowTitle('Pyro set system')
        self.setFixedSize(425, 360)
        self.setStyleSheet(MainScreenStyle)
        ########################## ALL SYSTEM BUTTON CONNECTION #############################
        self.SYSTEM0.clicked.connect(self.setSystemPyro)
        self.SYSTEM1.clicked.connect(self.set_system1)
        self.SYSTEM2.clicked.connect(self.set_system2)
        self.SYSTEM3.clicked.connect(self.set_system3)
        self.SYSTEM4.clicked.connect(self.set_system4)
        self.SYSTEM5.clicked.connect(self.set_system5)
        self.SYSTEM6.clicked.connect(self.set_system6)
        self.SYSTEM7.clicked.connect(self.set_system7)
        self.SYSTEM8.clicked.connect(self.set_system8)
        self.SYSTEM9.clicked.connect(self.set_system9)
        self.SYSTEM10.clicked.connect(self.set_system10)
        self.SYSTEM11.clicked.connect(self.set_system11)
        self.SYSTEM12.clicked.connect(self.set_system12)
        ############################ ADD IMAGE TO ALL BUTTON ################################
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGES_PATH}/Standby.png')))
        self.SYSTEM0.setIcon(icon)
        icon.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGES_PATH}/fastpreheat.png')))
        self.SYSTEM1.setIcon(icon)
        icon.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGES_PATH}/TopBottomFan.png')))
        self.SYSTEM2.setIcon(icon)
        icon.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGES_PATH}/LargeGrillFan.png')))
        self.SYSTEM3.setIcon(icon)
        icon.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGES_PATH}/HotAirTop.png')))
        self.SYSTEM4.setIcon(icon)
        icon.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGES_PATH}/HotAir.png')))
        self.SYSTEM5.setIcon(icon)
        icon.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGES_PATH}/TopBottom.png')))
        self.SYSTEM6.setIcon(icon)
        icon.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGES_PATH}/LargeGrill.png')))
        self.SYSTEM7.setIcon(icon)
        icon.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGES_PATH}/HotAir.png')))
        self.SYSTEM8.setIcon(icon)
        icon.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGES_PATH}/HotAirBottom.png')))
        self.SYSTEM9.setIcon(icon)
        icon.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGES_PATH}/HotAirBottom.png')))
        self.SYSTEM10.setIcon(icon)
        icon.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGES_PATH}/defrost.png')))
        self.SYSTEM11.setIcon(icon)
        icon.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGES_PATH}/pyro.png')))
        self.SYSTEM12.setIcon(icon)
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
    
    def closeEvent(self, event):
        """
        - close pyro screen
        """
        mainWindow.closePyroScreen()    
    ################# ACTIVATE SELECTED SYSTEM ######################################
    def set_system0(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM0.setStyleSheet(ButtonStyleOn2)
        mainWindow.pyroSetSystem('STANDBY')
    
    def set_system1(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM1.setStyleSheet(ButtonStyleOn2)
        mainWindow.pyroSetSystem('PREHEAT')
      
    def set_system2(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM2.setStyleSheet(ButtonStyleOn2)
        mainWindow.pyroSetSystem('SYSTEM1')
    
    def set_system3(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM3.setStyleSheet(ButtonStyleOn2)
        mainWindow.pyroSetSystem('SYSTEM2')
    
    def set_system4(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM4.setStyleSheet(ButtonStyleOn2)
        mainWindow.pyroSetSystem('SYSTEM3')
    
    def set_system5(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM5.setStyleSheet(ButtonStyleOn2)
        mainWindow.pyroSetSystem('SYSTEM4')
    
    def set_system6(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM6.setStyleSheet(ButtonStyleOn2)
        mainWindow.pyroSetSystem('SYSTEM5')
    
    def set_system7(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM7.setStyleSheet(ButtonStyleOn2)
        mainWindow.pyroSetSystem('SYSTEM6')
    
    def set_system8(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM8.setStyleSheet(ButtonStyleOn2)
        mainWindow.pyroSetSystem('SYSTEM7')
    
    def set_system9(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM9.setStyleSheet(ButtonStyleOn2)
        mainWindow.pyroSetSystem('SYSTEM8')
    
    def set_system10(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM10.setStyleSheet(ButtonStyleOn2)
        mainWindow.pyroSetSystem('SYSTEM9')
    
    def set_system11(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM11.setStyleSheet(ButtonStyleOn2)
        mainWindow.pyroSetSystem('SYSTEM10')
    
    def set_system12(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM12.setStyleSheet(ButtonStyleOn2)
        mainWindow.pyroSetSystem('PYRO')
    
    def setSystemPyro(self):
        systemPyro = self.set_system0()
        mainWindow.pyroSetSystem(systemPyro)
class CreatePotTable(QMainWindow):
    def __init__(self):
        super().__init__()
        ########################## SCREEN PATH CONVERT #############################
        PotTable = os.path.abspath(f"{QT_DESIGNER_PATH}/CreatePotTable.ui")
        loadUi(str(PotTable),self)
        self.setWindowTitle('Create lookup Pot table')
        self.setFixedSize(470, 210)
        #############################################################################
        self.save_index = 0
        self.SelectTable = "Table1.1"
        #self.SelectDacTable.setStyleSheet(ButtonStyleWhite)    
        self.Pot_value.valueChanged.connect(self.ChangeValuePot)
        self.Pot_box_value.valueChanged.connect(self.ReadValuePot)
        self.save_value.clicked.connect(self.savePotValue)
        self.SelectPotTable.activated[str].connect(self.digitalPotTable)
        self.SelectPotTable.addItems(listDigitalPotTable())
        self.SelectPotTable.setStyleSheet(ButtonStyleWhite)
        self.save_value.setStyleSheet(ButtonStyleOff2)
        self.lableErrorPot.setVisible(False)
        self.lableErrorPot.setFont(QFont('Arial', 11))
        self.lableErrorPot.setStyleSheet("color: red")
        self.lableErrorPot.setText(f"Pot value in Table x.1 is > 765. Table x.2 can not be set")
        ############################## BUTTON STYLE ##################################
        self.iconSaveOn = QtGui.QIcon()
        self.iconSaveOn.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOn.png')))
        self.save_value.setIcon(self.iconSaveOn)
        
    def showLableError(self,number):
        self.lableErrorPot.setVisible(True)
        self.lableErrorPot.setText(f"Pot value in Table {number}.1 is > 765. Table {number}.2 can not be set")
    def closeLableError(self):
        self.lableErrorPot.setVisible(False)
     
    def ChangeValuePot(self):
        """
        - return pot value
        - activate button(save) when value change
        """
        self.save_value.setIcon(self.iconSaveOn)
        self.save_value.setEnabled(True)
        return self.Pot_value.value()

    def ReadValuePot(self):
        """
        - return pot value
        - activate button(save) when value change
        """
        self.save_value.setIcon(self.iconSaveOn)
        self.save_value.setEnabled(True)
        return self.Pot_box_value.value()
    
    def tableSelection(self):
        """
        - return table number
        """
        return self.SelectTable
    
    def digitalPotTable(self,potTable):
        """
        - select table you want to change
        -  open and clear txt file
        """
        self.SelectTable = potTable
        if self.save_index >= 1:
            self.f.close()
        self.save_index = 0
        #self.f = open(f'{BOX_DIGITAL_POT_PATH}\\{self.SelectTable}.txt', 'w')
        self.SelectPotTable.setStyleSheet(ButtonStyleOn)
    
    def savePotValue(self):
        """
        - save value to selected txt file
        """
        if self.save_index == 0:
            self.f = open(f'{BOX_DIGITAL_POT_PATH}\\{self.SelectTable}.txt', 'w')
        self.f = open(f'{BOX_DIGITAL_POT_PATH}\\{self.SelectTable}.txt', 'a')
        #print('save value',self.save_index,self.SelectTable,self.Pot_box_value.value(),self.Pot_value.value())
        self.f.writelines(f'{self.Pot_box_value.value()} {self.Pot_value.value()}\n')
        self.save_index += 1
        self.f.close()
        self.save_value.setEnabled(False)
        
    def closeEvent(self, event):
        """
        - close pot table screen
        """
        mainWindow.closePotTable()    
class CreateDacTable(QMainWindow):
    def __init__(self):
        super().__init__()
        ########################## SCREEN PATH CONVERT #############################
        DacTable = os.path.abspath(f"{QT_DESIGNER_PATH}/CreateDacTable.ui")
        loadUi(str(DacTable),self)
        self.setWindowTitle('Create lookup Dac table ')
        self.setFixedSize(470, 210)
        self.save_index = 0
        self.SelectTable = "Table1"
        self.Dac_value.valueChanged.connect(self.ChangeValueDac)
        self.Dac_box_value.valueChanged.connect(self.ReadValueDac)
        self.save_value.clicked.connect(self.savePotValue)
        self.SelectDacTable.activated[str].connect(self.digitalDacTable)
        self.SelectDacTable.addItems(listDigitalDacTable())
        self.SelectDacTable.setStyleSheet(ButtonStyleWhite)
        self.save_value.setStyleSheet(ButtonStyleOff2)
        ############################## BUTTON STYLE ####################################
        self.iconSaveOn = QtGui.QIcon()
        self.iconSaveOn.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOn.png')))
        self.save_value.setIcon(self.iconSaveOn)
        
    def ChangeValueDac(self):
        """
        - return dac value
        - activate button(save) when value change
        """
        self.save_value.setIcon(self.iconSaveOn)
        self.save_value.setEnabled(True)
        return self.Dac_value.value()

    def ReadValueDac(self):
        """
        - return dac value
        - activate button(save) when value change
        """
        self.save_value.setIcon(self.iconSaveOn)
        self.save_value.setEnabled(True)
        return self.Dac_box_value.value()
    
    def digitalDacTable(self,potTable):
        """
        - select table you want to change
        -  open and clear txt file
        """
        self.SelectTable = potTable
        if self.save_index >= 1:
            self.f.close()
        self.save_index = 0
        self.f = open(f'{BOX_DIGITAL_DAC_PATH}\\{self.SelectTable}.txt', 'w')
        self.SelectDacTable.setStyleSheet(ButtonStyleOn)
    
    def tableSelection(self):
        """
        - return table number
        """
        return self.SelectTable[5]
    
    def savePotValue(self):
        """
        - save value to selected txt file
        """
        self.f = open(f'{BOX_DIGITAL_DAC_PATH}\\{self.SelectTable}.txt', 'a')
        #print('save value',self.save_index,self.SelectTable,self.Dac_box_value.value(),self.Dac_value.value())
        self.f.writelines(f'{self.Dac_box_value.value()} {self.Dac_value.value()}\n')
        self.save_index += 1
        self.f.close()
        self.save_value.setEnabled(False)
        
    def closeEvent(self, event):
        """
        - close dac table
        """
        mainWindow.closeDacTable()    

class CreateAutoTest(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Dict = {}
        self.DictRunTest ={}
        # to store files in a list
        self.listDirectory = []
        self.dir_list = os.listdir(AUTO_TEST_PATH)
        self.dir_list.insert(0,'')
        print('dirList',self.dir_list)
        self.fileType = ".py"
        self.index = 0
        self.pQ = None
        self.setWindowTitle('AUTO TEST')
        self.setGeometry(100, 100, 900, 900)
        self.setStyleSheet(MainScreenStyle)
        # tree
        self.tree = QTreeWidget(self)
        self.tree.setGeometry(10, 50, 300, 300)
        self.tree.setStyleSheet(MainScreenStyle)
        self.tree.setHidden(False)
        self.tree.setHeaderLabels(['click refresh to expand test'])
        
        self.refreshButton = QPushButton('refresh', self)
        self.refreshButton.move(0,10)
        self.refreshButton.setStyleSheet(ButtonStyleOff)
           # connect button to function on_click
        self.refreshButton.clicked.connect(self.test_refresh)
        
        self.runButton = QPushButton('run tests', self)
        self.runButton.move(110,10)
        self.runButton.setStyleSheet(ButtonStyleOff)
           # connect button to function on_click
        self.runButton.clicked.connect(self.runTest)
        
        self.Button = QPushButton('test', self)
        self.Button.move(250,10)
        self.Button.setStyleSheet(ButtonStyleOff)
           # connect button to function on_click
        self.Button.clicked.connect(self.testButton)
        
        self.text = QPlainTextEdit(self)
        self.text.move(10,350)
        self.text.resize(300,100)
        #self.text.setReadOnly(True)
        
        self.thread_run_test = QThreadPool()
     
        #self.progress = QProgressBar(self)
        #self.progress.move(10,450)
        #self.progress.setRange(0, 100)
    def closeEvent(self, event):
        """
        - close dac table
        """
        mainWindow.closeRunAutoTest()    
    def testButton(self):
        # Kill all child processes
        for child in self.all_processes:
            child.kill()
            #self.pQ.kill()
        print('end proccess')
    
    def test_refresh(self):
        self.Dict.clear()
        self.DictRunTest.clear()
        self.listDirectory.clear()
        #self.testButton()
        self.tree.clear()
        self.tree.setHidden(False)
        self.tree.setHeaderLabels(["automation test"])
        for index,(root, dirs, file) in enumerate(os.walk(AUTO_TEST_PATH)):
            testFile= file.copy()
            testFile.sort(reverse=True)
            for f in file:
                if self.fileType in f:
                    if index == 0:
                        continue
                    if (self.dir_list[index].find(".") == -1):
                        self.Dict[self.dir_list[index]] = file
                        self.DictRunTest[self.dir_list[index]] = testFile
                    
        for department in self.dir_list[1:]:
            self.parent = QTreeWidgetItem(self.tree)
            if (department.find(".") == -1):
                self.parent.setExpanded(False)
                self.parent.setText(0,department)
                self.parent.setFlags(self.parent.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                self.listDirectory.append(department)
                self.listDirectory.sort()
                try:
                    for self.index_child ,employee in enumerate(self.Dict[department]):
                        self.child = QTreeWidgetItem(self.parent)
                        self.child.setFlags(self.child.flags() | Qt.ItemIsUserCheckable)
                        self.child.setText(0, employee)
                        self.child.setCheckState(0, Qt.Unchecked)
                except KeyError:
                    continue
        # place the tree on the main window
        #self.setCentralWidget(self.tree)
      
        self.show()
    
    
    def runTest(self):
        self.text.clear()
        self.tree.setEnabled(False)
        self.refreshButton.setEnabled(False)
        print('go')
        self.runAllTest()
        #self.thread_run_test.start(self.runAllTest)
        print('ok')

    
    def runAllTest(self):
        self.listScript =[]
        self.all_processes = []
        for index in range(len(self.listDirectory)):
            iterator = QTreeWidgetItemIterator(self.tree,QTreeWidgetItemIterator.Checked)
            while iterator.value():
                print('ok123')
                self.item = iterator.value()
                res = any(self.item.text(0) in ele for ele in self.DictRunTest[self.listDirectory[index]])
                if self.fileType in self.item.text(0): 
                    if res is True:
                        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!',self.item.text(0)) 
                        #self.pQ = QProcess(self)
                        #self.pQ.readyReadStandardOutput.connect(self.handle_stdout)
                        #self.pQ.readyReadStandardError.connect(self.handle_stderr)
                        #self.pQ.stateChanged.connect(self.handle_state)
                        #self.pQ.start("python",[f'allTest/{listDirectory[index]}/{self.item.text(0)}'])
                        #self.pQ.waitForFinished()
                        pathTest = f'{os.path.dirname(AUTO_TEST_PATH)}/{os.path.basename(AUTO_TEST_PATH)}/{self.listDirectory[index]}/{self.item.text(0)}'
                        self.listScript.append(pathTest)
                        #self.all_processes.append(self.pQ)
                        #self.all_processes.sort(reverse=True)
                iterator += 1
        for script in self.listScript:
            self.pQ = QProcess(self)
            self.pQ.readyReadStandardOutput.connect(self.handle_stdout)
            self.pQ.readyReadStandardError.connect(self.handle_stderr)
            self.pQ.stateChanged.connect(self.handle_state)
            self.all_processes.append(self.pQ)
            print('script',script)
            self.pQ.start("python",[script])
        
        print(self.listScript)
        print (20*'#')
        self.refreshButton.setEnabled(True)
        self.tree.setEnabled(True)     
    
    def handle_stderr(self):
        data = self.pQ.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        #progress = simple_percent_parser(stderr)
        #if progress:
            #self.progress.setValue(progress)
        self.message(stderr)
       
    def handle_stdout(self):
        data = self.pQ.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.message(stdout)

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: 'Finish',
            QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]
        self.message(f"State changed: {state_name}")

    def message(self, s):
        self.text.appendPlainText(s)
       
class AutoRunScript(QMainWindow):
    def __init__(self):
        super().__init__()
        ########################## SCREEN PATH CONVERT #############################
        DacScreen = os.path.abspath(f"{QT_DESIGNER_PATH}/AutoTest.ui")
        loadUi(str(DacScreen),self)
        self.Dict = {}
        self.DictRunTest ={}
        # to store files in a list
        self.listDirectory = []
        self.dir_list = os.listdir(AUTO_TEST_PATH)
        self.dir_list.insert(0,'')
        print('dirList',self.dir_list)
        self.fileType = ".py"
        self.index = 0
        self.pQ = None
        self.setWindowTitle('AUTOMATION TEST')
        self.setFixedSize(500, 725)
        self.setStyleSheet(MainScreenStyle)
        self.tree.setStyleSheet(MainScreenStyle)
        self.tree.setHidden(False)
        self.tree.setHeaderLabels(["automation test"])
        self.tree.setHeaderLabels(['click refresh to expand test'])
        #######################################################################
    
        self.refreshButton.setStyleSheet(ButtonStyleOff2)
           # connect button to function on_click
        self.refreshButton.clicked.connect(self.test_refresh)
        
        self.runButton.setStyleSheet(ButtonStyleOff2)
           # connect button to function on_click
        self.runButton.clicked.connect(self.runTest)
        
        self.Button.setStyleSheet(ButtonStyleOff2)
           # connect button to function on_click
        self.Button.clicked.connect(self.testButton)
        
        #self.text.setReadOnly(True)
        
        self.thread_run_test = QThreadPool()
     
        #self.progress = QProgressBar(self)
        #self.progress.move(10,450)
        #self.progress.setRange(0, 100)
    def closeEvent(self, event):
        """
        - close dac table
        """
        mainWindow.closeRunAutoTest()    
    def testButton(self):
        # Kill all child processes
        for child in self.all_processes:
            child.kill()
            #self.pQ.kill()
        print('end proccess')
    
    def test_refresh(self):
        self.Dict.clear()
        self.DictRunTest.clear()
        self.listDirectory.clear()
        #self.testButton()
        self.tree.clear()
        self.tree.setHidden(False)
        self.tree.setHeaderLabels(["automation test"])
        for index,(root, dirs, file) in enumerate(os.walk(AUTO_TEST_PATH)):
            testFile= file.copy()
            testFile.sort(reverse=True)
            for f in file:
                if self.fileType in f:
                    if index == 0:
                        continue
                    if (self.dir_list[index].find(".") == -1):
                        self.Dict[self.dir_list[index]] = file
                        self.DictRunTest[self.dir_list[index]] = testFile
                    
        for department in self.dir_list[1:]:
            self.parent = QTreeWidgetItem(self.tree)
            if (department.find(".") == -1):
                self.parent.setExpanded(False)
                self.parent.setText(0,department)
                self.parent.setFlags(self.parent.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                self.listDirectory.append(department)
                self.listDirectory.sort()
                try:
                    for self.index_child ,employee in enumerate(self.Dict[department]):
                        self.child = QTreeWidgetItem(self.parent)
                        self.child.setFlags(self.child.flags() | Qt.ItemIsUserCheckable)
                        self.child.setText(0, employee)
                        self.child.setCheckState(0, Qt.Unchecked)
                except KeyError:
                    continue
        # place the tree on the main window
        #self.setCentralWidget(self.tree)
      
        self.show()
    
    
    def runTest(self):
        self.text.clear()
        self.tree.setEnabled(False)
        self.refreshButton.setEnabled(False)
        print('go')
        self.runAllTest()
        #self.thread_run_test.start(self.runAllTest)
        print('ok')

    
    def runAllTest(self):
        self.listScript =[]
        self.all_processes = []
        for index in range(len(self.listDirectory)):
            iterator = QTreeWidgetItemIterator(self.tree,QTreeWidgetItemIterator.Checked)
            while iterator.value():
                print('ok123')
                self.item = iterator.value()
                res = any(self.item.text(0) in ele for ele in self.DictRunTest[self.listDirectory[index]])
                if self.fileType in self.item.text(0): 
                    if res is True:
                        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!',self.item.text(0)) 
                        #self.pQ = QProcess(self)
                        #self.pQ.readyReadStandardOutput.connect(self.handle_stdout)
                        #self.pQ.readyReadStandardError.connect(self.handle_stderr)
                        #self.pQ.stateChanged.connect(self.handle_state)
                        #self.pQ.start("python",[f'allTest/{listDirectory[index]}/{self.item.text(0)}'])
                        #self.pQ.waitForFinished()
                        pathTest = f'{os.path.dirname(AUTO_TEST_PATH)}/{os.path.basename(AUTO_TEST_PATH)}/{self.listDirectory[index]}/{self.item.text(0)}'
                        self.listScript.append(pathTest)
                        #self.all_processes.append(self.pQ)
                        #self.all_processes.sort(reverse=True)
                iterator += 1
        for script in self.listScript:
            self.pQ = QProcess(self)
            self.pQ.readyReadStandardOutput.connect(self.handle_stdout)
            self.pQ.readyReadStandardError.connect(self.handle_stderr)
            self.pQ.stateChanged.connect(self.handle_state)
            self.all_processes.append(self.pQ)
            print('script',script)
            self.pQ.start("python",[script])
        
        print(self.listScript)
        print (20*'#')
        self.refreshButton.setEnabled(True)
        self.tree.setEnabled(True)     
    
    def handle_stderr(self):
        data = self.pQ.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        #progress = simple_percent_parser(stderr)
        #if progress:
            #self.progress.setValue(progress)
        self.message(stderr)
       
    def handle_stdout(self):
        data = self.pQ.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.message(stdout)

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: 'Finish',
            QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]
        self.message(f"State changed: {state_name}")

    def message(self, s):
        self.text.appendPlainText(s)
      
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ### CREATE AN OBJECT NAMES ###
    mainWindow = MainWindow()
    mainWindow.show()
    #autoTest = AutoRunScript()
    #utoTest.show()
    HusaModelWindow = HusaSetModule()
    PyroSetSystem = Bio21PyroSetSystem()
    SetDacValue = SetDacPot()
    PotTableSet = CreatePotTable()
    DacTableCreate = CreateDacTable()
    RunAutoTest = CreateAutoTest()
    ##############################
    sys.exit(app.exec_())





