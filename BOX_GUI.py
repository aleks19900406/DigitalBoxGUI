import sys
import os
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets,QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QMessageBox,QMainWindow,QStyle,QStyleOptionSlider,QApplication
from PyQt5.QtCore import *
from PyQt5 import QtCore
from cv2 import repeat
from os.path import abspath, basename, dirname, join, realpath
from time import sleep,time
from package.tester._clients.das import DAS  # Import DAS class
from DigitalBox.dasConnect import SERIALCONNECT
from DigitalBox.lib import*
import traceback
TEST_DIR_NAME = dirname(abspath(__file__))
TEST_ROOT_NAME = basename(TEST_DIR_NAME)
TEST_ROOT = dirname(TEST_DIR_NAME)
TEST_DATA = dirname(TEST_ROOT)
DATA_ROOT = join(TEST_DATA)
print(TEST_ROOT)
MAIN_TIME_REFRESHING = 1000
SPACE = '\n'
DigitalInput = 24
#DigitalInput = 32
change_input = []
for input in range(DigitalInput):
    change_input.append(False)
QT_DESIGNER_PATH = os.path.join("QT_designer")
BOX_MARKS_PATH = os.path.join("data","boxMarks")
BOX_DIGITAL_POT_PATH = os.path.join("data","digitalPotTable")
IMAGES_PATH = os.path.join("data","images","system")
change_parameters =[0,0,0,0,0,0,0,0,0]
beginPotValue = [30,30,30,30,30,30]
beginDacValue = [30,30,30,30,30,30,30,30]
beginSetVoltage = [0,0,0,0]
setPwm1 = [0,0]
setPwm2 = [0,0]
setPwmOld =[0,0]
errorNumber ='#'*100
ButtonStyleOff  = ("background-color: rgb(210,210,210);"
                                "border-style: outset;"
                                "border-radius: 5px;"
                                "border-color: fusion;"
                                "font: 10px;"
                                "min-width: 2em;")
ButtonStyleOn  = ("background-color: lightgreen;"
                                "border-style: outset;"
                                "border-radius: 5px;"
                                "border-color: beige;"
                                "font: 10px;"
                                "min-width: 2em;")
ButtonStyleWhite = ("background-color: white;"
                                "border-style: outset;"
                                "border-radius: 5px;"
                                "border-color: fusion;"
                                "font: 10px;"
                                "min-width: 2em;")

MainScreenStyle = "background-color: rgb(250,255,250)"


PotSlicerLabelStyle = ("background-color: white;"
                                "border-style: outset;"
                                "border-radius: 5px;"
                                "border-color: fusion;"
                                "font: 12px;")
###

def listBoxMarks():
    boxMarkList =[]
    boxMarkList.clear()
    #boxMarkList =['',]
    for file_name in os.listdir(BOX_MARKS_PATH):
        boxMarkList.append(file_name.replace('.txt',''))
    return boxMarkList

def listDigitalPotTable():
    DigitalPotList =[]
    DigitalPotList.clear()
    for file_name in os.listdir(BOX_DIGITAL_POT_PATH):
        DigitalPotList.append(file_name.replace('.txt',''))
    return DigitalPotList

def deliteListDigitalPotTable():
    DigitalPotList =[]
    DigitalPotList.clear()
    for file_name in os.listdir(BOX_DIGITAL_POT_PATH):
        print(os.path.basename(file_name.replace('.txt','')))
        DigitalPotList.append(file_name.replace('.txt',''))
    return DigitalPotList

def sliderColor(self,sliderIndex):
    colorSlider = eval(f'self.digital_pot{sliderIndex}.value()')
    if (colorSlider/2)>=255:
        G=B=0
        R=255
    elif (colorSlider/2) <= 10:
        B=255
        R=G = 240 - abs(colorSlider-20)
    else:
        G=B= 255-(colorSlider/2)
        R =255
       
    return int(R),int(G),int(B)

def sliderColorDac(self,sliderIndex):
    colorSlider = eval(f'self.dac_pot{sliderIndex}.value()')
    if (colorSlider/2)>=255:
        G=B=0
        R=255
    elif (colorSlider/2) <= 10:
        B=255
        R=G = 240 - abs(colorSlider-20)
    else:
        G=B= 255-(colorSlider/2)
        R =255
       
    return int(R),int(G),int(B)

def listConnection():
    import serial.tools.list_ports
    LIST_CONNECT =[]
    LIST_CONNECT.clear()
    for USB_PORT in serial.tools.list_ports.comports():
        if 'Arduino Mega' in str(USB_PORT):
            LIST_CONNECT.append(f'{str(USB_PORT)[0:5]} - Arduino Mega 2560') 
        elif'CP210x' in str(USB_PORT) :
            LIST_CONNECT.append(f'{str(USB_PORT)[0:5]} - NodeMCU ESP32')
    for ip_address in range(10,100,10):
        LIST_CONNECT.append(f'RPI - 192.168.1.{ip_address}')
    
    return LIST_CONNECT

def activate_output(self,number,value):
    self.box.set_digital_out(number,value)

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        Window1 = os.path.abspath(f"{QT_DESIGNER_PATH}/Main_screen.ui")
        loadUi(str(Window1),self)
        self.index_on_off = 0
        self.index_out = [0,0,0,0,0,0,0,0]
        self.index_extras = [0,0,0,0,0]
        self.connectParameters = 0
        self.box_is_connected = 0
        self.index_refreshing = 0
        self.digitalPotChange = 0
        self.digitalPotIndex = 0
        self.SetWidget = QtWidgets.QMainWindow()
        self.SetWidget.setWindowTitle('DIGITAL BOX MAIN')
        self.SetWidget.setFixedSize(1920, 1080)
    
        self.setStyleSheet(MainScreenStyle)
        self.on_off.clicked.connect(self.button_OnOff)
        self.RefreshingConnection.clicked.connect(self.BoxRefreshing)
        self.SetPwmBar1.valueChanged.connect(self.SetFrequencyBar1)
        self.SetPwmBar2.valueChanged.connect(self.SetFrequencyBar2)
        self.BOX_VERSION.setText('')
        self.BOX_VERSION.setFont(QFont('Arial', 14))
        self.BOX_VERSION.setStyleSheet("color: red");
        ################## digital output #####################################
        self.OUT0.setCheckable(True)
        self.OUT0.clicked.connect(self.output0)
        self.OUT1.clicked.connect(self.output1)
        self.OUT2.clicked.connect(self.output2)
        self.OUT3.clicked.connect(self.output3)
        self.OUT4.clicked.connect(self.output4)
        self.OUT5.clicked.connect(self.output5)
        self.OUT6.clicked.connect(self.output6)
        self.OUT7.clicked.connect(self.output7)
        ###################### open additional screen ##########################
        self.ButtonHusaModel.clicked.connect(self.buttonHusaModel)
        self.ButtonPyroSystem.clicked.connect(self.buttonPyroSystem)
        self.ButtonDacSet.clicked.connect(self.buttonDacSet)
       
        ###########################box connection##################################
        #self.pushButton.clicked.connect(self.testButton)
        #self.digital_pot0.setMinimum(0)
        #self.digital_pot0.setMaximum(500)
        self.BoxConnect.activated[str].connect(self.connectBox)
        self.BoxConnect.setEditable(True)
        self.BoxConnect.setStyleSheet(ButtonStyleWhite)
        self.BoxMarks.activated[str].connect(self.boxMarks)
        self.BoxMarks.setEditable(True)
        self.BoxMarks.setStyleSheet(ButtonStyleWhite)
        self.SelectPotTable.activated[str].connect(self.digitalPotTable)
        self.SelectPotTable.setEditable(True)
        self.SelectPotTable.setStyleSheet(ButtonStyleWhite)
        ###################TIMER ######################################################
        self.DIGITAL_BOX_MAIN = QTimer()
        self.DIGITAL_BOX_MAIN.timeout.connect(self.timerDigitalBox)  # 
        self.DIGITAL_BOX_MAIN.setInterval(MAIN_TIME_REFRESHING)
        self.thread_check_input = QThreadPool()
        ##############################################################################
   
       #################################################################################
    def timerDigitalBox(self):
        global MAIN_TIME_REFRESHING
        if self.digitalPotIndex == 0:
            tbegin = time()
            try:
                self.check_output()
                self.set_voltage()
                self.set_pwm1()
                self.set_pwm2()
                self.set_frequency_and_duty_old()
                self.input_state_indicate()
                self.thread_check_input.start(self.check_all_input)
                tend = time()
                print('time main box',int((tend-tbegin)*1000),'interval:',MAIN_TIME_REFRESHING)
                if  (tend-tbegin)*1000 >= MAIN_TIME_REFRESHING:
                    self.digitalPotChange = 1
                    MAIN_TIME_REFRESHING += 500
                    self.DIGITAL_BOX_MAIN.setInterval(MAIN_TIME_REFRESHING)
                else:
                    if (tend-tbegin)*1000 < MAIN_TIME_REFRESHING-200:
                        self.DIGITAL_BOX_MAIN.setInterval(MAIN_TIME_REFRESHING)
                        MAIN_TIME_REFRESHING -= 100
                        self.digitalPotChange = 0
            except ValueError:
                with open('check_error.txt', 'w') as f:
                    f.write(f'{errorNumber}\n')
                    f.write('!!! Can not set any parameters(set_voltage,set_pwm1,2...)!!!\n')
                    f.write('Solution:\n')
                    f.write('-- Check digital box version(>= V3.10) and\n')
                    f.write(f'{errorNumber}\n')
                    f.write(traceback.format_exc())
                    f.write(f'{errorNumber}\n')
                f.close()  
        
     
    def check_all_input(self):
        tbegin = time()
        self.digitalPotIndex = 1
        sleep(0.2)
        try:
            self.read_adc()
        except Exception:
            with open('check_error.txt', 'w') as f:
                f.write(f'{errorNumber}\n')
                f.write('!!!Dont get anything from ADC read !!!\n')
                f.write('Solution:\n')
                f.write('-- Check digital box version or hardware problems with ADC read\n')
                f.write(f'{errorNumber}\n')
                f.write(traceback.format_exc())
                f.write(f'{errorNumber}\n')
            f.close()  
        try:   
            self.read_pwm()
        except Exception:
            with open('check_error.txt', 'w') as f:
                f.write(f'{errorNumber}\n')
                f.write('!!!Dont get anything from PWM read !!!\n')
                f.write('Solution:\n')
                f.write('-- Check digital box version or hardware problems with ADC read\n')
                f.write(f'{errorNumber}\n')
                f.write(traceback.format_exc())
                f.write(f'{errorNumber}\n')
            f.close()  
        self.check_digital_pot()
        self.check_DAC_pot()
        
        self.digitalPotIndex = 0
        tend = time()
        print('read in data time:',tend-tbegin)
        
           
    def boxMarks(self,BOXMARKS):
        #self.BoxMarks.setStyleSheet(ButtonStyleOn)
        
        BOX_MARKS = open(f"{BOX_MARKS_PATH}/{BOXMARKS}.txt", "r")
        print('boxMarks refreshing')
        read_all_lines=BOX_MARKS.readlines()
        # husa model_LB
        #for index in range(1,7):
        #   eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        # HUSA MODEL_PB
        #for index in range(1,10):
        #   eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff)')
        #INPUT style
        for index in range(24):
            eval(f'self.INPUT_{index}.setStyleSheet(ButtonStyleOff)')
        #OUT button style
        for index in range(8):
            eval(f'self.OUT{index}.setStyleSheet(ButtonStyleOff)')
        
        # button connect style
        #self.RefreshingConnection.setStyleSheet(ButtonStyleOff)
        # button on/off style
        self.on_off.setStyleSheet(ButtonStyleOff)
        #################################
        for name in read_all_lines:
            if name == f'INPUT{SPACE}':
                try:
                    for index in range(24):
                        input_text = eval(f'self.INPUT_{index}')
                        input_text.setText(read_all_lines[1].replace('\n','').split(',')[index])
                except IndexError:
                    continue
            if name == f'OUTPUT{SPACE}':
                try:
                    for index in range(8):
                        output_text = eval(f'self.OUT{index}')
                        output_text.setText(read_all_lines[3].replace('\n','').split(',')[index])
                except IndexError:
                    continue
            if name == f'DIGITAL_POT{SPACE}':
                try:
                    for index in range(6):
                        digital_pot_text = eval(f'self.labelDigitalPot{index}')
                        digital_pot_text.setText(read_all_lines[5].replace('\n','').split(',')[index])
                        digital_pot_text.setFont(QFont('Arial', 10))
                except IndexError:
                    continue
                except AttributeError:
                    print('!!! POT not enough slider !!!')
            
            
            if name == f'DAC_POT{SPACE}':
                try:
    
                    for index in range(6):
                        digital_pot_text = eval(f'SetDacValue.labelDac{index}')
                        digital_pot_text.setText(read_all_lines[7].replace('\n','').split(',')[index])
                        digital_pot_text.setFont(QFont('Arial', 10))
                except IndexError:
                    continue
                except AttributeError:
                    print('!!! DAC not enough slider !!!')
            
            
            if name == f'READ_ADC{SPACE}':
            
                for index in range(4):
                    digital_pot_text = eval(f'self.labelADC{index}')
                    digital_pot_text.setText(read_all_lines[9].replace('\n','').split(',')[index])
                    digital_pot_text.setFont(QFont('Arial', 10))
            
            
            if name == f'SET_VOLTAGE{SPACE}':
            
                for index in range(4):
                    digital_pot_text = eval(f'self.labelSetVoltage{index}')
                    digital_pot_text.setText(read_all_lines[11].replace('\n','').split(',')[index])
                    digital_pot_text.setFont(QFont('Arial', 10))
        
            
            if name == f'READ_PWM1{SPACE}':
                for index in range(2):
                    digital_pot_text = eval(f'self.labelPwm1_{index}')
                    digital_pot_text.setText(read_all_lines[13].replace('\n','').split(',')[index])
                    digital_pot_text.setFont(QFont('Arial', 10))
            
            if name == f'READ_PWM2{SPACE}':
                for index in range(2):
                    digital_pot_text = eval(f'self.labelPwm2_{index}')
                    digital_pot_text.setText(read_all_lines[15].replace('\n','').split(',')[index])
                    digital_pot_text.setFont(QFont('Arial', 10)) 
        
            if name == f'SET_PWM1{SPACE}':
                for index in range(2):
                    digital_pot_text = eval(f'self.labelSetPwm1_{index}')
                    digital_pot_text.setText(read_all_lines[17].replace('\n','').split(',')[index])
                    digital_pot_text.setFont(QFont('Arial', 10))  
            
            if name == f'SET_PWM2{SPACE}':
                for index in range(2):
                    digital_pot_text = eval(f'self.labelSetPwm2_{index}')
                    digital_pot_text.setText(read_all_lines[19].replace('\n','').split(',')[index])
                    digital_pot_text.setFont(QFont('Arial', 10))
           

    def connectBox(self,CONNECTBOX):
        print('#######',self.box_is_connected)
        self.Connection = CONNECTBOX
        if self.box_is_connected == 1:
            sleep(2)
            self.box.disconnect()
            sleep(2)
        try:
            if CONNECTBOX[0:3] =='COM':
                self.box = SERIALCONNECT(CONNECTBOX[0:5].replace(' ',''))
                VERSION = self.box.connect()
                if VERSION >= "3.10":
                    print('version is corrected')
                    self.index_refreshing +=1
                    self.DIGITAL_BOX_MAIN.start()
                    self.BOX_VERSION.setText('')
                    self.BoxConnect.setStyleSheet(ButtonStyleOn)
                else:
                    print('version is < 3.10 upgrade version')
                    sleep(2)
                    self.box.disconnect()
                    self.index_refreshing = 0
                    self.BoxConnect.setStyleSheet(ButtonStyleWhite) 
                    self.BOX_VERSION.setText(f"Current version digital box is {VERSION}.Version must be >= 3.10. Update box to the latest version if you want to use this application") 
            else:
                self.box = DAS(CONNECTBOX[6:].replace(' ',''))  #
                self.box.connect()
                VERSION =  self.box.box_version[0].strip()
                if VERSION >= "3.10":
                    print('version is corrected')
                    self.index_refreshing +=1
                    self.DIGITAL_BOX_MAIN.start()
                    self.BOX_VERSION.setText('')
                    self.BoxConnect.setStyleSheet(ButtonStyleOn)
                else:
                    print('version is < 3.10 upgrade version')
                    sleep(2)
                    self.box.disconnect()
                    self.index_refreshing = 0
                    self.BOX_VERSION.setText(f"Current version digital box is {VERSION}.Version must be >= 3.10. Update box to the latest version if you want to use this application") 
                        
        except:
            with open('check_error.txt', 'w') as f:
                f.write(f'{errorNumber}\n')
                f.write(f'Das service is not connected to this ip {CONNECTBOX[6:]} \n')
                f.write('Solution:\n')
                f.write(f'-- Open supervisor {CONNECTBOX[6:]}:9001 (copy ip to this ip to browser) and check das service \n')
                f.write(f'-- Reset das service.Das service must bi in running state \n')
                f.write('-- Computer and RPI must be in the same domain \n')
                f.write(f'{errorNumber}\n')
                f.write(traceback.format_exc())
                f.write(f'{errorNumber}\n')
            f.close()

        self.connectParameters = 1
        self.box_is_connected +=1
        if self.box_is_connected >=2:
            self.box_is_connected =0     
    
    
    def digitalPotTable(self,potTable):
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
                    eval(f'self.digital_pot{index}.setTickInterval(int((max +(abs(min)))/10))')
                    eval(f'self.PotMax{index}.setText(str(max+10))')
                    eval(f'self.PotMin{index}.setText(str(min-10))')
                    eval(f'self.PotMin{index}.setStyleSheet(PotSlicerLabelStyle)')
                    eval(f'self.PotMax{index}.setStyleSheet(PotSlicerLabelStyle)')
                    R,G,B = sliderColor(self,index)
                    eval(f'self.digital_pot{index}.valueChanged.connect(self.SetDigitalPot{index})')
                    eval(f'self.labelDigitalPot{index}.setStyleSheet(ButtonStyleOn)')
                    eval(f'self.lcdNumber_digital_pot{index}.display(self.digital_pot{index}.value())')
                    eval(f'self.digital_pot{index}.setValue(min+20)')
                    eval(f'self.digital_pot{index}.setStyleSheet(f"background-color: rgb({R},{G},{B})")')
            except Exception:
                with open('check_error.txt', 'w') as f:
                    f.write(f'{errorNumber}\n')
                    f.write('!!!Table{x.x}.txt change or in table missing pot value or temperature value !!!\n')
                    f.write('Solution:\n')
                    f.write('-- Dont change name!!! Name must be Table1.1,Table1.2--->Table3.1,Table3.2\n')
                    f.write('-- Table must have temperature and pot value\n')
                    f.write(f'{errorNumber}\n')
                    f.write(traceback.format_exc())
                    f.write(f'{errorNumber}\n')
                f.close()  
                  
    def BoxRefreshing(self):
        print('box_connect',self.index_refreshing)
        self.BoxConnect.setStyleSheet(ButtonStyleWhite)   
        self.BoxMarks.setStyleSheet(ButtonStyleWhite)
        self.SelectPotTable.setStyleSheet(ButtonStyleWhite)
        if  self.index_refreshing == 0:
            #self.label_connect.setText('')
            #self.label_marks.setText('')
            self.BoxConnect.clear()
            self.BoxMarks.clear()
            self.SelectPotTable.clear()
            self.BoxConnect.addItems(listConnection())
            self.BoxMarks.addItems(listBoxMarks())
            self.SelectPotTable.addItems(listDigitalPotTable())
            self.AllTable = listDigitalPotTable()
            print('DIGITAL POT TABLE',listConnection())
            self.BOX_VERSION.setText('')

        else:
            sleep(2)
            self.index_refreshing +=1
            self.DIGITAL_BOX_MAIN.stop()
            self.DIGITAL_BOX_MAIN.setInterval(1000)
            self.BoxConnect.clear()
            self.BoxMarks.clear()
            self.SelectPotTable.clear()
            self.label_connect.setText('BOX CONNECT')
            self.label_marks.setText('SELECT MARKS')
            print(listConnection())
            self.BoxConnect.addItems(listConnection())
            self.BoxMarks.addItems(listBoxMarks())
            self.SelectPotTable.addItems(listDigitalPotTable())
            for index,TablePot in enumerate(listDigitalPotTable()):
                eval(f'self.labelDigitalPot{index}.setStyleSheet(MainScreenStyle)')
                eval(f'self.digital_pot{index}.setStyleSheet(MainScreenStyle)')
            self.AllTable = listDigitalPotTable()
            self.on_off.setStyleSheet(ButtonStyleOff)
            for index in range(8):
                eval(f'self.OUT{index}.setStyleSheet(ButtonStyleOff)')
            for index in range(6):
                eval(f'self.digital_pot{index}.setStyleSheet(ButtonStyleWhite)')
                eval(f'self.digital_pot{index}.value()')
                #eval(f'self.digital_pot{index}.setEnabled(False)')
                eval(f'self.lcdNumber_digital_pot{index}.display(0)')
            
            sleep(1)
            self.box.disconnect()
            print('disconnected')
    
        
        if self.index_refreshing >=2:
            self.index_refreshing =0
       
    def button_OnOff(self):

        self.index_on_off +=1
        if self.index_on_off >=2:
            self.index_on_off =0
    
    def output0(self):
        self.index_out[0] +=1
        if self.index_out[0] >=2:
            self.index_out[0] =0 
    
    def output1(self):
        self.index_out[1] +=1
        if self.index_out[1] >=2:
            self.index_out[1] =0 
         
    def output2(self):
        self.index_out[2] +=1
        if self.index_out[2] >=2:
            self.index_out[2] =0  
    
    def output3(self):
     
        self.index_out[3] +=1
        if self.index_out[3] >=2:
            self.index_out[3] =0  
    
    def output4(self):
      
        self.index_out[4] +=1
        if self.index_out[4] >=2:
            self.index_out[4] =0  
    
    def output5(self):
        self.index_out[5] +=1
        if self.index_out[5] >=2:
            self.index_out[5] =0  
    
    def output6(self):
        self.index_out[6] +=1
        if self.index_out[6] >=2:
            self.index_out[6] =0  
    
    def output7(self):
        self.index_out[7] +=1
        if self.index_out[7] >=2:
            self.index_out[7] =0
    
    def SetDigitalPot0(self):
        if self.index_refreshing == 1:
            R,G,B = sliderColor(self,0)
            self.digital_pot0.setStyleSheet(f"background-color: rgb({R},{G},{B})")
            self.lcdNumber_digital_pot0.display(self.digital_pot0.value())
        return self.digital_pot0.value()
                 
    def SetDigitalPot1(self):
        #print('slider1--------------------------------------------------------')
        if self.index_refreshing == 1:
            R,G,B = sliderColor(self,1)
            self.digital_pot1.setStyleSheet(f"background-color: rgb({R},{G},{B})")
            self.lcdNumber_digital_pot1.display(self.digital_pot1.value())
        return self.digital_pot1.value()
    
    def SetDigitalPot2(self):
        #print('slider2--------------------------------------------------------')
        if self.index_refreshing == 1:
            R,G,B = sliderColor(self,2)
            self.digital_pot2.setStyleSheet(f"background-color: rgb({R},{G},{B})")
            self.lcdNumber_digital_pot2.display(self.digital_pot2.value())
        return self.digital_pot2.value()
    
    def SetDigitalPot3(self):
        if self.index_refreshing == 1:
            R,G,B = sliderColor(self,3)
            self.digital_pot3.setStyleSheet(f"background-color: rgb({R},{G},{B})")
            self.lcdNumber_digital_pot3.display(self.digital_pot3.value())
        return self.digital_pot3.value()
    
    def SetDigitalPot4(self):
        if self.index_refreshing == 1:
            R,G,B = sliderColor(self,4)
            self.digital_pot4.setStyleSheet(f"background-color: rgb({R},{G},{B})")
            self.lcdNumber_digital_pot4.display(self.digital_pot4.value())
        return self.digital_pot4.value()
    
    def SetDigitalPot5(self):
        if self.index_refreshing == 1:
            R,G,B = sliderColor(self,5)
            self.digital_pot5.setStyleSheet(f"background-color: rgb({R},{G},{B})")
            self.lcdNumber_digital_pot5.display(self.digital_pot5.value())
        return self.digital_pot5.value()
    ################################################################
    def check_input(self):
        global input
        input = self.box.digital_in[:]
        #print('#######################check_input')
        return input
    
    def check_output(self):
        begin_parameter = [self.index_on_off,self.index_out[0],self.index_out[1],self.index_out[2],self.index_out[3],self.index_out[4],self.index_out[5],self.index_out[6],self.index_out[7]]
        print(begin_parameter)
        if begin_parameter != change_parameters or self.connectParameters == 1:
            print(begin_parameter,change_parameters)
            t0 = time()
            if (self.index_on_off % 2) == 0:
                self.box.main = 0
                self.on_off.setStyleSheet(ButtonStyleOff)
                change_parameters[0]= 0
            elif (self.index_on_off % 2) == 1:
                self.box.main = 1
                self.on_off.setStyleSheet(ButtonStyleOn)
                change_parameters[0]= 1
            
            parameter_true = tuple([i for i, val in enumerate(begin_parameter[1:]) if  val])
            if parameter_true:
                activate_output(self,parameter_true,True)
            
            parameter_false = tuple([i for i, val in enumerate(begin_parameter[1:]) if not val])
            if parameter_false:
                activate_output(self,parameter_false,False) 
   
            if (self.index_out[0] % 2) == 0:
                change_parameters[1]= 0 
                self.OUT0.setStyleSheet(ButtonStyleOff) 
            else:
                change_parameters[1]= 1
                self.OUT0.setStyleSheet(ButtonStyleOn) 
                
            if (self.index_out[1] % 2) == 0:
                change_parameters[2]= 0
                self.OUT1.setStyleSheet(ButtonStyleOff) 
            else:
                change_parameters[2]= 1
                self.OUT1.setStyleSheet(ButtonStyleOn) 
                
            if (self.index_out[2] % 2) == 0:
                change_parameters[3]= 0    
                self.OUT2.setStyleSheet(ButtonStyleOff) 
            else:
                change_parameters[3]= 1
                self.OUT2.setStyleSheet(ButtonStyleOn) 
                
            if (self.index_out[3] % 2) == 0:
                change_parameters[4]= 0
                self.OUT3.setStyleSheet(ButtonStyleOff) 
            else:
                change_parameters[4]= 1
                self.OUT3.setStyleSheet(ButtonStyleOn) 
                
            if (self.index_out[4] % 2) == 0:
                change_parameters[5]= 0 
                self.OUT4.setStyleSheet(ButtonStyleOff) 
            else:
                change_parameters[5]= 1
                self.OUT4.setStyleSheet(ButtonStyleOn) 
                
            if (self.index_out[5] % 2) == 0:
                change_parameters[6]= 0
                self.OUT5.setStyleSheet(ButtonStyleOff) 
            else:
                change_parameters[6]= 1
                self.OUT5.setStyleSheet(ButtonStyleOn) 
                  
            if (self.index_out[6] % 2) == 0:
                change_parameters[7]= 0
                self.OUT6.setStyleSheet(ButtonStyleOff) 
            else: 
                change_parameters[7]= 1
                self.OUT6.setStyleSheet(ButtonStyleOn) 
            
            if (self.index_out[7] % 2) == 0:
                change_parameters[8]= 0
                self.OUT7.setStyleSheet(ButtonStyleOff)  
            else:
                change_parameters[8]= 1
                self.OUT7.setStyleSheet(ButtonStyleOn) 
            self.connectParameters = 0
   
    def check_digital_pot(self):
        global beginPotValue
        #print('####################check_digital pot')
        readDigitalPot0 = self.digital_pot0.value()
        readDigitalPot1 = self.digital_pot1.value()
        readDigitalPot2 = self.digital_pot2.value()
        readDigitalPot3 = self.digital_pot3.value()
        readDigitalPot4 = self.digital_pot4.value()
        readDigitalPot5 = self.digital_pot5.value()
        #print('###',readDigitalPot0, readDigitalPot1,readDigitalPot2,readDigitalPot3,readDigitalPot4,readDigitalPot5)
        ###############################digital potentiometer 1 ######################################################
        if beginPotValue[0] != readDigitalPot0:
            #sleep(0.5)
            set_digital_pot(self,readDigitalPot0,tableIndex = 1,slider =1,chipSelect = 1)
            beginPotValue[0] = readDigitalPot0
        elif beginPotValue[1] != readDigitalPot1:
            #sleep(0.5)
            set_digital_pot(self,readDigitalPot1,tableIndex = 1,slider =2,chipSelect = 1)
            beginPotValue[1] = readDigitalPot1
        ###############################digital potentiometer 2 ######################################################
        elif beginPotValue[2] != readDigitalPot2:
            #sleep(0.5)
            set_digital_pot(self,readDigitalPot2,tableIndex = 2,slider =1,chipSelect = 2)
            beginPotValue[2] = readDigitalPot2
        elif beginPotValue[3] != readDigitalPot3:
            #sleep(0.5)
            set_digital_pot(self,readDigitalPot3,tableIndex = 2,slider =2,chipSelect = 2)
            beginPotValue[3] = readDigitalPot3
         ###############################digital potentiometer 3 ######################################################
        elif beginPotValue[4] != readDigitalPot4:
            #sleep(0.5)
            set_digital_pot(self,readDigitalPot4,tableIndex = 3,slider =1,chipSelect = 3)
            beginPotValue[4] = readDigitalPot4
        
        elif beginPotValue[5] != readDigitalPot5:
            #sleep(0.5)
            set_digital_pot(self,readDigitalPot5,tableIndex = 3,slider =2,chipSelect = 3)
            beginPotValue[5] = readDigitalPot5
            
    def read_adc(self):
        read_adc_all = self.box.read_adc
        self.readADC0.display(read_adc_all[0])
        self.readADC1.display(read_adc_all[1])
        self.readADC2.display(read_adc_all[2])
        self.readADC3.display(read_adc_all[3])
    
    def read_pwm(self):
        read_pwm_all = self.box.read_pwm
        self.ReadPwm1.display(read_pwm_all[0]['f'])
        self.ReadDuty1.display(read_pwm_all[0]['d'])
        self.ReadPwm2.display(read_pwm_all[1]['f'])
        self.ReadDuty2.display(read_pwm_all[1]['d'])
        #print('read_pwm',read_pwm_all)
    
    def set_voltage(self):
        readVoltage =[self.SetVoltage0.value(),self.SetVoltage1.value(),self.SetVoltage2.value(),self.SetVoltage3.value()]
        if beginSetVoltage[0] != readVoltage[0]:
            self.box.set_voltage = (0,readVoltage[0])
            beginSetVoltage[0] = readVoltage[0]
            #print('dif0')
        if beginSetVoltage[1] != readVoltage[1]:
            self.box.set_voltage = (1,readVoltage[1])
            beginSetVoltage[1] = readVoltage[1]
            #print('dif1')
        if beginSetVoltage[2] != readVoltage[2]:
            self.box.set_voltage = (2,readVoltage[2])
            beginSetVoltage[2] = readVoltage[2]
            #print('dif2')
        if beginSetVoltage[3] != readVoltage[3]:
            self.box.set_voltage = (3,readVoltage[3])
            beginSetVoltage[3] = readVoltage[3]
    
    def SetFrequencyBar1(self):
        self.SetFrequency1.setValue(self.SetPwmBar1.value())
        self.SetPwmBar1.setStyleSheet(f"background-color: rgb({250-int((self.SetPwmBar1.value()/100))},{250-int((self.SetPwmBar1.value()/100))},255)")
       
    def SetFrequencyBar2(self):
        self.SetFrequency2.setValue(self.SetPwmBar2.value())
        self.SetPwmBar2.setStyleSheet(f"background-color: rgb({250-int((self.SetPwmBar2.value()/100))},{250-int((self.SetPwmBar2.value()/100))},255)")
      
    def set_pwm1(self):
        readPwm1 =[self.SetFrequency1.value(),self.SetDuty1.value()]
        self.SetPwmBar1.setValue(self.SetFrequency1.value())
        print('pwm value:',self.SetFrequency1.value())
        readPwm1 =[self.SetFrequency1.value(),self.SetDuty1.value()]
        if setPwm1[0] != readPwm1[0]:
            self.box.set_pwm1 = (readPwm1[0],readPwm1[1])
            setPwm1[0] = readPwm1[0]
        if setPwm1[1] != readPwm1[1]:
            self.box.set_pwm1 = (readPwm1[0],readPwm1[1])
            setPwm1[1] = readPwm1[1]
            
    def set_pwm2(self):
        readPwm2 =[self.SetFrequency2.value(),self.SetDuty2.value()]
        self.SetPwmBar2.setValue(self.SetFrequency2.value())
        if setPwm2[0] != readPwm2[0]:
            self.box.set_pwm2 = (readPwm2[0],readPwm2[1])
            setPwm2[0] = readPwm2[0]
            #print('dif0')
        if setPwm2[1] != readPwm2[1]:
            self.box.set_pwm2 = (readPwm2[0],readPwm2[1])
            setPwm2[1] = readPwm2[1]
     
    def set_frequency_and_duty_old(self):
        readPwmOld =[self.SetFrequencyold.value(),self.SetDutyold.value()]
       
        print(readPwmOld)
        if setPwmOld[0] != readPwmOld[0]:
            self.box.frequency_out = readPwmOld[0]
            setPwmOld[0] = readPwmOld[0]
        
        if setPwmOld[1] != readPwmOld[1]:
            self.box.duty_cycle_out = readPwmOld[1]
            setPwmOld[1] = readPwmOld[1]
            
            
    def input_state_indicate(self):
        begin_input = self.check_input()
        #print(begin_input)
        for index in range(DigitalInput):
            #eval(f'self.INPUT_{index}.setEnabled(False)')
            if begin_input[index]== True:
                #print('on',input[index],'####',index)
                eval(f'self.INPUT_{index}.setStyleSheet(ButtonStyleOn)')
                #sleep(DISPLAY_SLEEP)
                change_input[index] = True

            elif begin_input[index]== False:
                #print('off',input[index],'####',index)
                eval(f'self.INPUT_{index}.setStyleSheet(ButtonStyleOff)')
                #sleep(DISPLAY_SLEEP)
                change_input[index] = False       

    def buttonHusaModel(self):
        if (self.index_extras[0] % 2) == 0:
            self.ButtonHusaModel.setStyleSheet(ButtonStyleOn)
            HusaModelWindow.show()
        else: 
            self.ButtonHusaModel.setStyleSheet(ButtonStyleOff)
            HusaModelWindow.close()
            
        self.index_extras[0] +=1
        if self.index_extras[0] >=2:
            self.index_extras[0] =0 
    
    def closeHusaScreen(self):
        self.index_extras[0] +=1
        self.ButtonHusaModel.setStyleSheet(ButtonStyleOff)
    
    def buttonPyroSystem(self):
        if (self.index_extras[1] % 2) == 0:
            self.ButtonPyroSystem.setStyleSheet(ButtonStyleOn)
            PyroSetSystem.show()
        else: 
            self.ButtonPyroSystem.setStyleSheet(ButtonStyleOff)
            PyroSetSystem.close()
            
        self.index_extras[1] +=1
        if self.index_extras[1] >=2:
            self.index_extras[1] =0 
        
    def closePyroScreen(self):
        self.index_extras[1] +=1
        self.ButtonPyroSystem.setStyleSheet(ButtonStyleOff)
    
    def buttonDacSet(self):
        if (self.index_extras[2] % 2) == 0:
            self.ButtonDacSet.setStyleSheet(ButtonStyleOn)
            SetDacValue.show()
        else: 
            self.ButtonDacSet.setStyleSheet(ButtonStyleOff)
            SetDacValue.close()
            
        self.index_extras[2] +=1
        if self.index_extras[2] >=2:
            self.index_extras[2] =0 
    
    def closeDacScreen(self):
        self.index_extras[2] +=1
        self.ButtonDacSet.setStyleSheet(ButtonStyleOff)
    
    def husaAutoSetModule(self,model_set):
        self.digitalPotIndex = 1
        sleep(0.5)
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
        self.digitalPotIndex = 1
        sleep(0.5)
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
        self.digitalPotIndex = 1
        sleep(1)
        select_system(self,system)
        sleep(1)
        self.digitalPotIndex = 0

    def check_DAC_pot(self):
        global beginDacValue
        print('####################check_dac')
        readDac0 = SetDacValue.dac_pot0.value()
        readDac1 = SetDacValue.dac_pot1.value()
        readDac2 = SetDacValue.dac_pot2.value()
        readDac3 = SetDacValue.dac_pot3.value()
        readDac4 = SetDacValue.dac_pot4.value()
        readDac5 = SetDacValue.dac_pot5.value()
        readDac6 = SetDacValue.dac_pot6.value()
        readDac7 = SetDacValue.dac_pot7.value()
        print('###',readDac0, readDac1,readDac2,readDac3,readDac4,readDac5)
        ############################### DAC VALUE 1 ######################################################
        if beginDacValue[0] != readDac0:
            #sleep(0.5)
            set_DAC(self,readDac0,tableIndex = 0,slider =1)
            beginDacValue[0] = readDac0
        ############################### DAC VALUE 2 ######################################################
        elif beginDacValue[1] != readDac1:
            #sleep(0.5)
            set_DAC(self,readDac1,tableIndex = 1,slider =2)
            beginDacValue[1] = readDac1
        ############################### DAC VALUE 3 ######################################################
        elif beginDacValue[2] != readDac2:
            #sleep(0.5)
            set_DAC(self,readDac2,tableIndex = 2,slider =3)
            beginDacValue[2] = readDac2
        ############################### DAC VALUE 4 ######################################################
        elif beginDacValue[3] != readDac3:
            #sleep(0.5)
            set_DAC(self,readDac3,tableIndex = 3,slider =4)
            beginDacValue[3] = readDac3
         ############################### DAC VALUE 5 ######################################################
        elif beginDacValue[4] != readDac4:
            #sleep(0.5)
            set_DAC(self,readDac4,tableIndex = 4,slider =5)
            beginDacValue[4] = readDac4
        ############################### DAC VALUE 6 ######################################################
        elif beginDacValue[5] != readDac5:
            #sleep(0.5)
            set_DAC(self,readDac5,tableIndex = 5,slider =6)
            beginDacValue[5] = readDac5
        elif beginDacValue[6] != readDac6:
            #sleep(0.5)
            set_DAC(self,readDac6,tableIndex = 6,slider =7)
            beginDacValue[6] = readDac6

        elif beginDacValue[7] != readDac7:
            #sleep(0.5)
            set_DAC(self,readDac7,tableIndex = 7,slider =8)
            beginDacValue[7] = readDac7
        
class SetDacPot(QMainWindow):
    def __init__(self):
        
        #super(Screen1,self).__init__()
        super().__init__()
        DacScreen = os.path.abspath(f"{QT_DESIGNER_PATH}/DacTable.ui")
        loadUi(str(DacScreen),self)
        SetWidget = QtWidgets.QMainWindow()
        SetWidget.setWindowTitle('SET DAC')
        SetWidget.setFixedSize(480, 620)
        self.setStyleSheet(MainScreenStyle)
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
                R,G,B = sliderColorDac(self,index)
                eval(f'self.dac_pot{index}.valueChanged.connect(self.SetDacPot{index})')
                eval(f'self.labelDac{index}.setStyleSheet(ButtonStyleOn)')
        except Exception:
            with open('check_error.txt', 'w') as f:
                f.write(f'{errorNumber}\n')
                f.write('!!!Table{x}.txt change or in table missing DAC value or temperature value !!!\n')
                f.write('Solution:\n')
                f.write('-- Dont change name!!! Name must be Table1-->Table8\n')
                f.write('-- Table must have temperature and DAC value\n')
                f.write(f'{errorNumber}\n')
                f.write(traceback.format_exc())
                f.write(f'{errorNumber}\n')
            f.close()  
    def closeEvent(self, event):
        #close = QMessageBox()
        #close.setText("You sure?")
        #close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        #close = close.exec()
        #if close == QMessageBox.Yes:
        #    event.accept()
        mainWindow.closeDacScreen()    
        #else:
         #   event.ignore()        
    def SetDacPot0(self):
        R,G,B = sliderColorDac(self,0)
        self.dac_pot0.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot0.display(self.dac_pot0.value())
        return self.dac_pot0.value()
                 
    def SetDacPot1(self):
        #print('slider1--------------------------------------------------------')
    
        R,G,B = sliderColorDac(self,1)
        self.dac_pot1.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot1.display(self.dac_pot1.value())
        return self.dac_pot1.value()
    
    def SetDacPot2(self):
        #print('slider2--------------------------------------------------------')
        R,G,B = sliderColorDac(self,2)
        self.dac_pot2.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot2.display(self.dac_pot2.value())
        return self.dac_pot2.value()
    
    def SetDacPot3(self):
        R,G,B = sliderColorDac(self,3)
        self.dac_pot3.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot3.display(self.dac_pot3.value())
        return self.dac_pot3.value()

    def SetDacPot4(self):
        R,G,B = sliderColorDac(self,4)
        self.dac_pot4.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot4.display(self.dac_pot4.value())
        return self.dac_pot4.value()

    def SetDacPot5(self):
        R,G,B = sliderColorDac(self,5)
        self.dac_pot5.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot5.display(self.dac_pot5.value())
        return self.dac_pot5.value()

    def SetDacPot6(self):
        R,G,B = sliderColorDac(self,6)
        self.dac_pot6.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot6.display(self.dac_pot6.value())
        return self.dac_pot6.value()
    
    def SetDacPot7(self):
        R,G,B = sliderColorDac(self,7)
        self.dac_pot7.setStyleSheet(f"background-color: rgb({R},{G},{B})")
        self.lcdNumber_dac_pot7.display(self.dac_pot7.value())
        return self.dac_pot7.value()
        
class HusaSetModule(QMainWindow):
    
    def __init__(self):
        
        #super(Screen1,self).__init__()
        super().__init__()
        HusaScreen = os.path.abspath(f"{QT_DESIGNER_PATH}/HusaSetModel.ui")
        loadUi(str(HusaScreen),self)
        SetWidget = QtWidgets.QMainWindow()
        SetWidget.setWindowTitle('HUSA SET PB/LB MODULE')
        SetWidget.setFixedSize(370, 400)
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
        self.M1_LB.clicked.connect(self.set_LB_model_1)
        self.M2_LB.clicked.connect(self.set_LB_model_2)
        self.M3_LB.clicked.connect(self.set_LB_model_3)
        self.M4_LB.clicked.connect(self.set_LB_model_4)
        self.M5_LB.clicked.connect(self.set_LB_model_5)
        self.M6_LB.clicked.connect(self.set_LB_model_6)
        
    #def createWindow(self):    
     #   screen1Widget.setWindowTitle('screen1')
      #  screen1Widget.setFixedSize(500, 500)
        

    def closeEvent(self, event):
        #close = QMessageBox()
        #close.setText("You sure?")
        #close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        #close = close.exec()
        #if close == QMessageBox.Yes:
        #    event.accept()
        mainWindow.closeHusaScreen()    
        #else:
         #   event.ignore()
    
      ### change husa models ###############
    def set_model_1(self):
        for index in range(1,10):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.MODEL_1.setStyleSheet(ButtonStyleOn)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M1')
        LB_MODEL = getLBModel(self,'M1')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn)')
     
    def set_model_2(self):
        for index in range(1,10):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.MODEL_2.setStyleSheet(ButtonStyleOn)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M2')
        LB_MODEL = getLBModel(self,'M2')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn)')
        
    def set_model_3(self):
        for index in range(1,10):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.MODEL_3.setStyleSheet(ButtonStyleOn)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M3')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn)')
    
    def set_model_4(self):
        for index in range(1,10):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.MODEL_4.setStyleSheet(ButtonStyleOn)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M4')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn)')
 
    def set_model_5(self):
        for index in range(1,10):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.MODEL_5.setStyleSheet(ButtonStyleOn)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M5')    
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn)')
        
    def set_model_6(self):
        for index in range(1,10):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.MODEL_6.setStyleSheet(ButtonStyleOn)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M6')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn)')
       
    def set_model_7(self):
        for index in range(1,10):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.MODEL_7.setStyleSheet(ButtonStyleOn)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M7')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn)')
       
    def set_model_8(self):
        for index in range(1,10):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.MODEL_8.setStyleSheet(ButtonStyleOn)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M8')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn)')
      
    def set_model_9(self):
        for index in range(1,10):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.MODEL_9.setStyleSheet(ButtonStyleOn)
        PB_MODEL,LB_MODEL=mainWindow.husaAutoSetModule('M9')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn)')
    ###### LB_model #################    
    def set_LB_model_1(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.M1_LB.setStyleSheet(ButtonStyleOn)
        mainWindow.husaSetLBModule('M1')
    
    def set_LB_model_2(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.M2_LB.setStyleSheet(ButtonStyleOn)
        mainWindow.husaSetLBModule('M2')
    
    def set_LB_model_3(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.M3_LB.setStyleSheet(ButtonStyleOn)
        mainWindow.husaSetLBModule('M3')
    
    def set_LB_model_4(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.M4_LB.setStyleSheet(ButtonStyleOn)
        mainWindow.husaSetLBModule('M4')      
    
    def set_LB_model_5(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.M5_LB.setStyleSheet(ButtonStyleOn)
        mainWindow.husaSetLBModule('M5')
    
    def set_LB_model_6(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff)')
        self.M6_LB.setStyleSheet(ButtonStyleOn)
        mainWindow.husaSetLBModule('M6')
class Bio21PyroSetSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        PyroScreen = os.path.abspath(f"{QT_DESIGNER_PATH}/Bio21PyroSetSystem.ui")
        loadUi(str(PyroScreen),self)
        SetWidget = QtWidgets.QMainWindow()
        SetWidget.setWindowTitle('Pyro set system')
        SetWidget.setFixedSize(370, 400)
        self.setStyleSheet(MainScreenStyle)
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
        icon = QtGui.QIcon()
        #icon.addPixmap(QtGui.QPixmap("./data/images/system/Steam.png"))
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
        self.SIGNALIZATION_REFRESH = QTimer()
        self.SIGNALIZATION_REFRESH.timeout.connect(self.refreshSignalization)   
        self.SIGNALIZATION_REFRESH.setInterval(200)
    
    
    def closeEvent(self, event):
        #close = QMessageBox()
        #close.setText("You sure?")
        #close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        #close = close.exec()
        #if close == QMessageBox.Yes:
        #    event.accept()
        mainWindow.closePyroScreen()    
        #else:
         #   event.ignore()
    def refreshSignalization(self):
        ...
       
    def set_system0(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff)')
        self.SYSTEM0.setStyleSheet(ButtonStyleOn)
        mainWindow.pyroSetSystem('STANDBY')
    def set_system1(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff)')
        self.SYSTEM1.setStyleSheet(ButtonStyleOn)
        mainWindow.pyroSetSystem('PREHEAT')
      
    def set_system2(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff)')
        self.SYSTEM2.setStyleSheet(ButtonStyleOn)
        mainWindow.pyroSetSystem('SYSTEM1')
    def set_system3(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff)')
        self.SYSTEM3.setStyleSheet(ButtonStyleOn)
        mainWindow.pyroSetSystem('SYSTEM2')
    def set_system4(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff)')
        self.SYSTEM4.setStyleSheet(ButtonStyleOn)
        mainWindow.pyroSetSystem('SYSTEM3')
    def set_system5(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff)')
        self.SYSTEM5.setStyleSheet(ButtonStyleOn)
        mainWindow.pyroSetSystem('SYSTEM4')
    def set_system6(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff)')
        self.SYSTEM6.setStyleSheet(ButtonStyleOn)
        mainWindow.pyroSetSystem('SYSTEM5')
    def set_system7(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff)')
        self.SYSTEM7.setStyleSheet(ButtonStyleOn)
        mainWindow.pyroSetSystem('SYSTEM6')
    def set_system8(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff)')
        self.SYSTEM8.setStyleSheet(ButtonStyleOn)
        mainWindow.pyroSetSystem('SYSTEM7')
    def set_system9(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff)')
        self.SYSTEM9.setStyleSheet(ButtonStyleOn)
        mainWindow.pyroSetSystem('SYSTEM8')
    def set_system10(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff)')
        self.SYSTEM10.setStyleSheet(ButtonStyleOn)
        mainWindow.pyroSetSystem('SYSTEM9')
    def set_system11(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff)')
        self.SYSTEM11.setStyleSheet(ButtonStyleOn)
        mainWindow.pyroSetSystem('SYSTEM10')
    def set_system12(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff)')
        self.SYSTEM12.setStyleSheet(ButtonStyleOn)
        mainWindow.pyroSetSystem('PYRO')

    def setSystemPyro(self):
        systemPyro = self.set_system0()
        mainWindow.pyroSetSystem(systemPyro)


 

if __name__ == "__main__":
    import sys
   
    app = QApplication(sys.argv)
    #mainWidget = QtWidgets.QMainWindow()
    #screen1Widget = QtWidgets.QMainWindow()
    mainWindow = MainWindow()
    HusaModelWindow = HusaSetModule()
    PyroSetSystem = Bio21PyroSetSystem()
    SetDacValue = SetDacPot()
    mainWindow.show()
    sys.exit(app.exec_())





