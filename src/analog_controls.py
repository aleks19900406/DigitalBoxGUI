import datetime
import traceback
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from DigitalBox.lib import *
from . import state
from .styles import InputStyleOn, PotSlicerLabelStyle
from .helpers import listDigitalPotTable, sliderColor


class AnalogControlsMixin:
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
                    f.write(f'{state.errorNumber}{dateAndTime}{state.errorNumber}\n')
                    f.write('!!!Table{x.x}.txt change or in table missing pot value or temperature value !!!\n')
                    f.write('Solution:\n')
                    f.write('-- Dont change name!!! Name must be Table1.1,Table1.2--->Table3.1,Table3.2\n')
                    f.write('-- Table must have temperature and pot value\n')
                    f.write(f'{state.errorNumber*2}\n')
                    f.write(traceback.format_exc())
                    f.write(f'{state.errorNumber*2}\n')
                f.close()

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

    def check_digital_pot(self):
        """
        set digital pot value when value change
        """
        
        self.readDigitalPot0 = self.digital_pot0.value()
        self.readDigitalPot1 = self.digital_pot1.value()
        self.readDigitalPot2 = self.digital_pot2.value()
        self.readDigitalPot3 = self.digital_pot3.value()
        self.readDigitalPot4 = self.digital_pot4.value()
        self.readDigitalPot5 = self.digital_pot5.value()
        ###############################digital potentiometer 1 ######################################################
        if state.beginPotValue[0] != self.readDigitalPot0:
            set_digital_pot(self,self.readDigitalPot0,tableIndex = 1,slider =1,chipSelect = 1)
            state.beginPotValue[0] = self.readDigitalPot0
        elif state.beginPotValue[1] != self.readDigitalPot1:
            set_digital_pot(self,self.readDigitalPot1,tableIndex = 1,slider =2,chipSelect = 1)
            state.beginPotValue[1] = self.readDigitalPot1
        ###############################digital potentiometer 2 ######################################################
        elif state.beginPotValue[2] != self.readDigitalPot2:
            set_digital_pot(self,self.readDigitalPot2,tableIndex = 2,slider =1,chipSelect = 2)
            state.beginPotValue[2] = self.readDigitalPot2
        elif state.beginPotValue[3] != self.readDigitalPot3:
            set_digital_pot(self,self.readDigitalPot3,tableIndex = 2,slider =2,chipSelect = 2)
            state.beginPotValue[3] = self.readDigitalPot3
         ###############################digital potentiometer 3 ######################################################
        elif state.beginPotValue[4] != self.readDigitalPot4:
            set_digital_pot(self,self.readDigitalPot4,tableIndex = 3,slider =1,chipSelect = 3)
            state.beginPotValue[4] = self.readDigitalPot4      
        elif state.beginPotValue[5] != self.readDigitalPot5:
            set_digital_pot(self,self.readDigitalPot5,tableIndex = 3,slider =2,chipSelect = 3)
            state.beginPotValue[5] = self.readDigitalPot5

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
        if state.beginSetVoltage[0] != self.readVoltage[0]:
            self.box.set_voltage = (0,self.readVoltage[0])
            state.beginSetVoltage[0] = self.readVoltage[0]
        if state.beginSetVoltage[1] != self.readVoltage[1]:
            self.box.set_voltage = (1,self.readVoltage[1])
            state.beginSetVoltage[1] = self.readVoltage[1]
        if state.beginSetVoltage[2] != self.readVoltage[2]:
            self.box.set_voltage = (2,self.readVoltage[2])
            state.beginSetVoltage[2] = self.readVoltage[2]
        if state.beginSetVoltage[3] != self.readVoltage[3]:
            self.box.set_voltage = (3,self.readVoltage[3])
            state.beginSetVoltage[3] = self.readVoltage[3]

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
        if state.setPwm1[0] != self.readPwm1[0]:
            self.box.set_pwm1 = (self.readPwm1[0],self.readPwm1[1])
            state.setPwm1[0] = self.readPwm1[0]
        if state.setPwm1[1] != self.readPwm1[1]:
            self.box.set_pwm1 = (self.readPwm1[0],self.readPwm1[1])
            state.setPwm1[1] = self.readPwm1[1]

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
        if state.setPwm2[0] != self.readPwm2[0]:
            self.box.set_pwm2 = (self.readPwm2[0],self.readPwm2[1])
            state.setPwm2[0] = self.readPwm2[0]
        if state.setPwm2[1] != self.readPwm2[1]:
            self.box.set_pwm2 = (self.readPwm2[0],self.readPwm2[1])
            state.setPwm2[1] = self.readPwm2[1]

    def set_frequency_and_duty_old(self):
        """
        set frequency and duty value when value change
        """
        self.readPwmOld =[self.SetFrequencyOld.value(),self.SetDutyOld.value()]
       
        if state.setPwmOld[0] != self.readPwmOld[0]:
            self.box.frequency_out = self.readPwmOld[0]
            state.setPwmOld[0] = self.readPwmOld[0]
        
        if state.setPwmOld[1] != self.readPwmOld[1]:
            self.box.duty_cycle_out = self.readPwmOld[1]
            state.setPwmOld[1] = self.readPwmOld[1]

    def check_DAC_pot(self):
        """
        - if value change send dac value
        """
        
        self.readDac0 = state.SetDacValue.dac_pot0.value()
        self.readDac1 = state.SetDacValue.dac_pot1.value()
        self.readDac2 = state.SetDacValue.dac_pot2.value()
        self.readDac3 = state.SetDacValue.dac_pot3.value()
        self.readDac4 = state.SetDacValue.dac_pot4.value()
        self.readDac5 = state.SetDacValue.dac_pot5.value()
        self.readDac6 = state.SetDacValue.dac_pot6.value()
        self.readDac7 = state.SetDacValue.dac_pot7.value()
        ############################### DAC VALUE 1 ######################################################
        if state.beginDacValue[0] != self.readDac0:
            set_DAC(self,self.readDac0,tableIndex = 0,slider =1)
            state.beginDacValue[0] = self.readDac0
        ############################### DAC VALUE 2 ######################################################
        elif state.beginDacValue[1] != self.readDac1:
            set_DAC(self,self.readDac1,tableIndex = 1,slider =2)
            state.beginDacValue[1] = self.readDac1
        ############################### DAC VALUE 3 ######################################################
        elif state.beginDacValue[2] != self.readDac2:
            set_DAC(self,self.readDac2,tableIndex = 2,slider =3)
            state.beginDacValue[2] = self.readDac2
        ############################### DAC VALUE 4 ######################################################
        elif state.beginDacValue[3] != self.readDac3:
            set_DAC(self,self.readDac3,tableIndex = 3,slider =4)
            state.beginDacValue[3] = self.readDac3
         ############################### DAC VALUE 5 ######################################################
        elif state.beginDacValue[4] != self.readDac4:
            set_DAC(self,self.readDac4,tableIndex = 4,slider =5)
            state.beginDacValue[4] = self.readDac4
        ############################### DAC VALUE 6 ######################################################
        elif state.beginDacValue[5] != self.readDac5:
            set_DAC(self,self.readDac5,tableIndex = 5,slider =6)
            state.beginDacValue[5] = self.readDac5
        elif state.beginDacValue[6] != self.readDac6:
            set_DAC(self,self.readDac6,tableIndex = 6,slider =7)
            state.beginDacValue[6] = self.readDac6
        elif state.beginDacValue[7] != self.readDac7:
            set_DAC(self,self.readDac7,tableIndex = 7,slider =8)
            state.beginDacValue[7] = self.readDac7

    def createPotTable(self):
        """
        - if value change send pot value
        
        """
        
        self.DIGITAL_BOX_MAIN.stop()
        try:
            readPot = state.PotTableSet.Pot_value.value()
            TableFirstMin,TableFirstMax = tablePotMaxMin(self,f"{state.PotTableSet.tableSelection()[0:5]}{state.PotTableSet.tableSelection()[5]}.1")
            #print('readPot',readPot)
            #print('table-->',f"{PotTableSet.tableSelection()[0:5]}{PotTableSet.tableSelection()[5]}.1")
            #print('max=',TableFirstMax)
            if state.beginSetPot != readPot:
                if state.PotTableSet.tableSelection()[7] == '1':
                    state.PotTableSet.closeLableError()
                    if readPot <= 255:
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),0],readPot)
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),1,2,3],0)
                    elif readPot > 255 and readPot <= 255*2:
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),0],255)
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),1],readPot-255)
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),2,3],0)
                    elif readPot > 255*2 and readPot <= 255*3:
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),0,1],255)
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),2],readPot-255*2)
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],0)
                    elif readPot > 255*3:
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),0,1,2],255)
                        self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],readPot-255*3)
                    state.beginSetPot = readPot
                if state.PotTableSet.tableSelection()[7] == '2':
                    self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),4,5],0)
                    if TableFirstMax <= 255:
                        state.PotTableSet.closeLableError()
                        if readPot <= 255:
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),1],readPot)
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),2,3],0)
                        elif readPot > 255 and readPot <= 255*2:
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),1],255)
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),2],readPot-255)
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],0)
                        elif readPot > 255*2 and readPot <= 255*3:
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),0,1,2],255)
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],readPot-255*2)
                    elif TableFirstMax > 255 and TableFirstMax <= 255*2:
                        state.PotTableSet.closeLableError()
                        if readPot <= 255:
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),2],readPot)
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],0)
                        elif readPot > 255 and readPot <= 255*2:
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),2],255)
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],readPot)
                    elif TableFirstMax > 255*2 and TableFirstMax <= 255*3:
                        state.PotTableSet.closeLableError()
                        if readPot <= 255:
                            self.box.set_digital_pot([int(state.PotTableSet.tableSelection()[5]),3],readPot)
                           
                    elif TableFirstMax > 255*3:
                        state.PotTableSet.showLableError(state.PotTableSet.tableSelection()[5])
                    state.beginSetPot = readPot
                #print(self.box.digital_pot[:])
        except ValueError:
            x = datetime.datetime.now()
            dateAndTime = x.strftime("%c")
            with open('check_error.txt', 'a') as f:
                f.write(f'{state.errorNumber}{dateAndTime}{state.errorNumber}\n')
                f.write(f'!!! {state.PotTableSet.tableSelection()[0:5]}{state.PotTableSet.tableSelection()[5]}.1 is empty or not created properly  !!!\n')
                f.write('Solution:\n')
                f.write(f' Check {state.PotTableSet.tableSelection()[0:5]}{state.PotTableSet.tableSelection()[5]}.1 and try again \n')
                f.write(f'{state.errorNumber*2}\n')
                f.write(traceback.format_exc())
                f.write(f'{state.errorNumber*2}\n')
            f.close()

    def createDacTable(self):
        """
        - if value change set dac value
        """
        
        readDac = state.DacTableCreate.Dac_value.value()
        self.DIGITAL_BOX_MAIN.stop()
        if state.beginDacPot != readDac:
            self.box.set_analog_out(int(state.DacTableCreate.tableSelection())-1,readDac)
            state.beginDacPot = readDac
