import os
from pathlib import Path
from PyQt5 import QtGui
from PyQt5.QtWidgets import QMainWindow
from PyQt5.uic import loadUi
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from DigitalBox.lib import *
from . import state
from .paths import IMAGES_PATH, QT_DESIGNER
from .styles import ButtonStyleOff2, ButtonStyleOn2, MainScreenStyle


class HusaSetModule(QMainWindow):
    def __init__(self):
        super().__init__()
        ########################## SCREEN PATH CONVERT #############################
        HusaScreen = QT_DESIGNER / 'HusaSetModel.ui'
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
        state.mainWindow.closeHusaScreen()    
      ########## AUTO SET HUSA MODEL PB AND LB MODEL ############################
    def set_model_1(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_1.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=state.mainWindow.husaAutoSetModule('M1')
        LB_MODEL = getLBModel(self,'M1')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
     
    def set_model_2(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_2.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=state.mainWindow.husaAutoSetModule('M2')
        LB_MODEL = getLBModel(self,'M2')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
        
    def set_model_3(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_3.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=state.mainWindow.husaAutoSetModule('M3')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
    
    def set_model_4(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_4.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=state.mainWindow.husaAutoSetModule('M4')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
 
    def set_model_5(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_5.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=state.mainWindow.husaAutoSetModule('M5')    
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
        
    def set_model_6(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_6.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=state.mainWindow.husaAutoSetModule('M6')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
       
    def set_model_7(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_7.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=state.mainWindow.husaAutoSetModule('M7')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
       
    def set_model_8(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_8.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=state.mainWindow.husaAutoSetModule('M8')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
      
    def set_model_9(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_9.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=state.mainWindow.husaAutoSetModule('M9')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
    
    def set_model_10(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_10.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=state.mainWindow.husaAutoSetModule('M10')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
    
    def set_model_11(self):
        for index in range(1,12):
            eval(f'self.MODEL_{index}.setStyleSheet(ButtonStyleOff2)')
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.MODEL_11.setStyleSheet(ButtonStyleOn2)
        PB_MODEL,LB_MODEL=state.mainWindow.husaAutoSetModule('M11')
        eval(f'self.M{LB_MODEL}_LB.setStyleSheet(ButtonStyleOn2)')
    ########## SET ONLY LB MODEL ##################################################    
    def set_LB_model_1(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.M1_LB.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.husaSetLBModule('M1')
    
    def set_LB_model_2(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.M2_LB.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.husaSetLBModule('M2')
    
    def set_LB_model_3(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.M3_LB.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.husaSetLBModule('M3')
    
    def set_LB_model_4(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.M4_LB.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.husaSetLBModule('M4')      
    
    def set_LB_model_5(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.M5_LB.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.husaSetLBModule('M5')
    
    def set_LB_model_6(self):
        for index in range(1,7):
            eval(f'self.M{index}_LB.setStyleSheet(ButtonStyleOff2)')
        self.M6_LB.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.husaSetLBModule('M6')

class Bio21PyroSetSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        ########################## SCREEN PATH CONVERT #############################
        PyroScreen = QT_DESIGNER / 'Bio21PyroSetSystem.ui'
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
        state.mainWindow.closePyroScreen()    
    ################# ACTIVATE SELECTED SYSTEM ######################################
    def set_system0(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM0.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.pyroSetSystem('STANDBY')
    
    def set_system1(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM1.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.pyroSetSystem('PREHEAT')
      
    def set_system2(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM2.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.pyroSetSystem('SYSTEM1')
    
    def set_system3(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM3.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.pyroSetSystem('SYSTEM2')
    
    def set_system4(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM4.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.pyroSetSystem('SYSTEM3')
    
    def set_system5(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM5.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.pyroSetSystem('SYSTEM4')
    
    def set_system6(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM6.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.pyroSetSystem('SYSTEM5')
    
    def set_system7(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM7.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.pyroSetSystem('SYSTEM6')
    
    def set_system8(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM8.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.pyroSetSystem('SYSTEM7')
    
    def set_system9(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM9.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.pyroSetSystem('SYSTEM8')
    
    def set_system10(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM10.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.pyroSetSystem('SYSTEM9')
    
    def set_system11(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM11.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.pyroSetSystem('SYSTEM10')
    
    def set_system12(self):
        for index in range(0,13):
            eval(f'self.SYSTEM{index}.setStyleSheet(ButtonStyleOff2)')
        self.SYSTEM12.setStyleSheet(ButtonStyleOn2)
        state.mainWindow.pyroSetSystem('PYRO')
    
    def setSystemPyro(self):
        systemPyro = self.set_system0()
        state.mainWindow.pyroSetSystem(systemPyro)
