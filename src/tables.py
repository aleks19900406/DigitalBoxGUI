import datetime
import os
import traceback
from pathlib import Path
from PyQt6 import QtGui
from PyQt6.QtWidgets import QMainWindow
from PyQt6.uic import loadUi
from PyQt6.QtGui import QFont
from DigitalBox.lib import dacValueMaxMin
from . import state
from .paths import BOX_DIGITAL_DAC_PATH, BOX_DIGITAL_POT_PATH, IMAGE_PATH_OTHER, QT_DESIGNER
from .scaling import make_scalable
from .styles import ButtonStyleOff2, ButtonStyleOn, ButtonStyleWhite, MainScreenStyle, PotSlicerLabelStyle
from .helpers import listDigitalDacTable, listDigitalPotTable, sliderColorDac


class SetDacPot(QMainWindow):
    def __init__(self):
        super().__init__()
        ########################## SCREEN PATH CONVERT #############################
        DacScreen = QT_DESIGNER / 'DacTable.ui'
        loadUi(str(DacScreen),self)
        self.setWindowTitle('SET DAC')
        make_scalable(self, 960, 705)
        self.setStyleSheet(MainScreenStyle)
        ##########################SET SLIDER STYLE #############################
        try:
            for index in range(8):
                min,max = dacValueMaxMin(self,f'Table{index+1}')
                getattr(self, f'dac_pot{index}').setMinimum(min-10)
                getattr(self, f'dac_pot{index}').setMaximum(max+10)
                getattr(self, f'dac_pot{index}').setTickInterval(int((max +(abs(min)))/10))
                getattr(self, f'DacMax{index}').setText(str(max+10))
                getattr(self, f'DacMin{index}').setText(str(min-10))
                getattr(self, f'DacMin{index}').setStyleSheet(PotSlicerLabelStyle)
                getattr(self, f'DacMax{index}').setStyleSheet(PotSlicerLabelStyle)
                R,G,B = sliderColorDac(self,index,min,max)
                getattr(self, f'dac_pot{index}').valueChanged.connect(getattr(self, f'SetDacPot{index}'))
                getattr(self, f'labelDac{index}').setStyleSheet(ButtonStyleOn)
        except Exception:
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{state.errorNumber}{dateAndTime}{state.errorNumber}\n')
                f.write('!!!Table{x}.txt change or in table missing DAC value or temperature value !!!\n')
                f.write('Solution:\n')
                f.write('-- Dont change name!!! Name must be Table1-->Table8\n')
                f.write('-- Table must have temperature and DAC value\n')
                f.write(f'{state.errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{state.errorNumber*2}\n')
            f.close()  
        #######################################################################
    def closeEvent(self, event):
        """
        - close Dac screen
        """
        state.mainWindow.closeDacScreen()    
        
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

class CreatePotTable(QMainWindow):
    def __init__(self):
        super().__init__()
        ########################## SCREEN PATH CONVERT #############################
        PotTable = QT_DESIGNER / 'CreatePotTable.ui'
        loadUi(str(PotTable),self)
        self.setWindowTitle('Create lookup Pot table')
        make_scalable(self, 470, 210)
        #############################################################################
        self.save_index = 0
        self.SelectTable = "Table1.1"
        #self.SelectDacTable.setStyleSheet(ButtonStyleWhite)    
        self.Pot_value.valueChanged.connect(self.ChangeValuePot)
        self.Pot_box_value.valueChanged.connect(self.ReadValuePot)
        self.save_value.clicked.connect(self.savePotValue)
        self.SelectPotTable.textActivated.connect(self.digitalPotTable)
        self.SelectPotTable.addItems(listDigitalPotTable())
        self.SelectPotTable.setStyleSheet(ButtonStyleWhite)
        self.save_value.setStyleSheet(ButtonStyleOff2)
        self.lableErrorPot.setVisible(False)
        self.lableErrorPot.setFont(QFont('Arial', 11))
        self.lableErrorPot.setStyleSheet("color: red")
        self.lableErrorPot.setText("Pot value in Table x.1 is > 765. Table x.2 can not be set")
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
        #self.f = open(f'{BOX_DIGITAL_POT_PATH}/{self.SelectTable}.txt', 'w')
        self.SelectPotTable.setStyleSheet(ButtonStyleOn)
    
    def savePotValue(self):
        """
        - save value to selected txt file
        """
        if self.save_index == 0:
            self.f = open(f'{BOX_DIGITAL_POT_PATH}/{self.SelectTable}.txt', 'w')
        self.f = open(f'{BOX_DIGITAL_POT_PATH}/{self.SelectTable}.txt', 'a')
        #print('save value',self.save_index,self.SelectTable,self.Pot_box_value.value(),self.Pot_value.value())
        self.f.writelines(f'{self.Pot_box_value.value()} {self.Pot_value.value()}\n')
        self.save_index += 1
        self.f.close()
        self.save_value.setEnabled(False)
        
    def closeEvent(self, event):
        """
        - close pot table screen
        """
        state.mainWindow.closePotTable()

class CreateDacTable(QMainWindow):
    def __init__(self):
        super().__init__()
        ########################## SCREEN PATH CONVERT #############################
        DacTable = QT_DESIGNER / 'CreateDacTable.ui'
        loadUi(str(DacTable),self)
        self.setWindowTitle('Create lookup Dac table ')
        make_scalable(self, 470, 210)
        self.save_index = 0
        self.SelectTable = "Table1"
        self.Dac_value.valueChanged.connect(self.ChangeValueDac)
        self.Dac_box_value.valueChanged.connect(self.ReadValueDac)
        self.save_value.clicked.connect(self.savePotValue)
        self.SelectDacTable.textActivated.connect(self.digitalDacTable)
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
        self.f = open(f'{BOX_DIGITAL_DAC_PATH}/{self.SelectTable}.txt', 'w')
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
        self.f = open(f'{BOX_DIGITAL_DAC_PATH}/{self.SelectTable}.txt', 'a')
        #print('save value',self.save_index,self.SelectTable,self.Dac_box_value.value(),self.Dac_value.value())
        self.f.writelines(f'{self.Dac_box_value.value()} {self.Dac_value.value()}\n')
        self.save_index += 1
        self.f.close()
        self.save_value.setEnabled(False)
        
    def closeEvent(self, event):
        """
        - close dac table
        """
        state.mainWindow.closeDacTable()
