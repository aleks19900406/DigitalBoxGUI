import os
import traceback
from time import sleep
import openpyxl
from PyQt6 import QtGui
from .paths import DATA_SAVE, IMAGE_PATH_OTHER
from .box_marks import box_mark_name
from .styles import ButtonStyleOn, ButtonStyleWhite


class SavingMixin:
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
            self.startSaveThread()
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

    def startSaveThread(self):
        """
        - disable the save button (GUI thread) and write the file in the thread pool
        """
        self.startStopSaving.setEnabled(False)
        self.saveDataThread.start(self.saveToCsv)

    def saveToCsv(self):
        """
        - sava to .csv file
        - runs in a pool thread: must not touch any widget, result goes through saveFinished
        """
        error = ""
        try:
            if self.repeatSaveData == 0 and self.indexBackup == 0: 
                self.wb.save(f"{DATA_SAVE}/{self.fileName}.csv")
            elif self.indexBackup == 1:
                self.wb.save(f"{DATA_SAVE}/{self.fileName}_backup.csv")
                self.indexBackup = 0
            else:
                self.wb.save(f"{DATA_SAVE}/{self.fileName}_{self.repeatSaveData}.csv")
        except PermissionError:
            error = "permission"
        except AttributeError:
            error = "attribute"
            traceback.print_exc()
        except Exception:
            error = "other"
            traceback.print_exc()
        self.saveFinished.emit(error)

    def onSaveFinished(self, error):
        """
        - GUI thread: update widgets after the file was written
        """
        self.startStopSaving.setEnabled(True)
        self.savingBar.setVisible(False)
        self.backupSave.setVisible(False)
        self.worker.stop()
        if not error:
            return
        self.indexButtonSave = 0
        self.label_errorSaveFile.setVisible(True)
        self.label_saveFile.setVisible(False)
        if error == "permission":
            self.label_errorSaveFile.setText(f"!!! Excel file {self.fileName} is open. Close and try again !!!")
        elif error == "attribute":
            self.label_errorSaveFile.setText("!!! File not saved. Write file name and press enter !!!")
        else:
            self.label_errorSaveFile.setText(f"!!! File {self.fileName} not saved !!!")

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
            else:
                self.repeatSaveData = 0
                self.ExcelFile.setStyleSheet(ButtonStyleWhite)
                self.refreshSaveData.stop()
                self.iconSaveData.addPixmap(QtGui.QPixmap(os.path.abspath(f'{IMAGE_PATH_OTHER}/SaveOff.png')))
                self.startStopSaving.setIcon(self.iconSaveData)
                self.startSaveThread()
                self.timeSave =self.indexSaveData * 0.001     # calculation saving time
                if self.indexSaveData > 3000:
                    print('saving')
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
            self.startSaveThread()
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
            self.indexSaveData = 0
            self.excelFile(self.fileName)
        allParameters = []
        self.label_saveFile.setVisible(True)
        if self.refreshSaving != self.excelRefresh.value():
            self.refreshSaveData.setInterval(int(self.excelRefresh.value()*1000))
            #self.refreshSaveData.setInterval(int(self.excelRefresh.value()*1)) # Test
            self.refreshSaving = self.excelRefresh.value()

        digitalPot = [self.readDigitalPot0,self.readDigitalPot1,self.readDigitalPot2,self.readDigitalPot3,self.readDigitalPot4,self.readDigitalPot5]
        digitalOut = [self.index_on_off,self.index_out[0],self.index_out[1],self.index_out[2],self.index_out[3],self.index_out[4],self.index_out[5],self.index_out[6],self.index_out[7],self.index_out[8],self.index_out[9],self.index_out[10],self.index_out[11],self.index_out[12],self.index_out[13],self.index_out[14],self.index_out[15],]
        
        readPwm1= [int(self.read_pwm_all[0]['f']),int(self.read_pwm_all[0]['d'])]
        readPwm2= [int(self.read_pwm_all[1]['f']),int(self.read_pwm_all[1]['d'])]
        dacSet = [self.readDac0,self.readDac1,self.readDac2,self.readDac3,self.readDac4,self.readDac5,self.readDac6,self.readDac7]
        allParameters.extend(digitalPot)
        allParameters.extend(digitalOut)
        allParameters.extend(self.read_adc_all)
        allParameters.extend(self.readVoltage)
        allParameters.extend(readPwm1)
        allParameters.extend(self.readPwm1)
        allParameters.extend(readPwm2)
        allParameters.extend(self.readPwm2)
        allParameters.extend([1 if b else 0 for b in self.read_input])
        allParameters.extend(dacSet)
        allParameters.extend(self.readPwmOld)
        RowName = self.sheet.cell(row = self.indexSaveData+2, column = 1) 
        RowName.value = self.time.toString('dd-MM-yyyy')
        RowName = self.sheet.cell(row = self.indexSaveData+2, column = 2) 
        RowName.value = self.time.toString('hh:mm:ss')
        for index, name in enumerate(allParameters):
            RowName = self.sheet.cell(row = self.indexSaveData+2, column = index+3)
            RowName.value=name

        self.indexSaveData += 1

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
                        if box_mark_name(self.box_mark_data, 'DIGITAL_POT', index, '') == '':
                            digitalPot.append(f'setPot{index}')
                        else:
                            digitalPot.append(box_mark_name(self.box_mark_data, 'DIGITAL_POT', index, ''))
                    except IndexError:
                        digitalPot.append(f'setPot{index}')
                    except AttributeError:
                        digitalPot.append(f'setPot{index}')
                digitalOut.append('On/Off')
                for index in range(16):
                    try:
                        if box_mark_name(self.box_mark_data, 'OUTPUT', index, '') == '':
                            digitalOut.append(f'switch{index}')
                        else:
                            digitalOut.append(box_mark_name(self.box_mark_data, 'OUTPUT', index, ''))
                    except IndexError:
                        digitalOut.append(f'switch{index}')
                    except AttributeError:
                        digitalOut.append(f'switch{index}')
                    
                for index in range(4):
                    try:
                        if box_mark_name(self.box_mark_data, 'READ_ADC', index, '') == '':
                            readAdc.append(f'readADC{index}')
                        else:
                            readAdc.append(box_mark_name(self.box_mark_data, 'READ_ADC', index, ''))
                    except IndexError:
                        readAdc.append(f'readADC{index}')
                    except AttributeError: 
                        readAdc.append(f'readADC{index}')
                for index in range(4):
                    try:
                        if box_mark_name(self.box_mark_data, 'SET_VOLTAGE', index, '') == '':
                            setVoltage.append(f'setVoltage{index}')
                        else:
                            setVoltage.append(box_mark_name(self.box_mark_data, 'SET_VOLTAGE', index, ''))
                            
                    except IndexError:
                        setVoltage.append(f'setVoltage{index}')
                    except AttributeError:         
                        setVoltage.append(f'setVoltage{index}')
                readPwm1.append('readPwm1')
                readPwm1.append('readDuty1')
                setPwm1.append('setPwm1')
                setPwm1.append('setDuty1')
                readPwm2.append('readPwm2')
                readPwm2.append('readDuty2')
                setPwm2.append('setPwm2')
                setPwm2.append('setDuty2')
                for index in range(32):
                    try:
                        if box_mark_name(self.box_mark_data, 'INPUT', index, '') == '':
                            digitalInput.append(f'IN{index}')
                        else:
                            digitalInput.append(box_mark_name(self.box_mark_data, 'INPUT', index, ''))
                    except IndexError:
                        digitalInput.append(f'IN{index}')
                    except AttributeError:         
                        digitalInput.append(f'IN{index}')    
                for index in range(8):
                    try:
                        if box_mark_name(self.box_mark_data, 'DAC_POT', index, '') == '':
                            dacSet.append(f'setDac{index}')
                        else:
                            dacSet.append(box_mark_name(self.box_mark_data, 'DAC_POT', index, ''))
                    except IndexError:
                        dacSet.append(f'setDac{index}')
                    except AttributeError:         
                        dacSet.append(f'setDac{index}') 
                freqOldBox.append('setFreq(duty50%)')
                dutyOldBox.append('setDuty(2kHz)')
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
                columnName.value = 'date'
                columnName = self.sheet.cell(row = 1, column = 2) 
                columnName.value = 'time'
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
                self.label_errorSaveFile.setText("!!! CONNECT DIGITAL BOX !!!")
            
            if self.indexButtonSave >=2:
                self.indexButtonSave =0
        
        except PermissionError:
            self.label_errorSaveFile.setVisible(True)
            self.label_saveFile.setVisible(False)
            self.label_errorSaveFile.setText(f"!!! Excel file {self.fileName} is open. Close and try again !!!")
