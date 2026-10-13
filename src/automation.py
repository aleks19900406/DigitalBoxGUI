import os
from pathlib import Path
from PyQt5.QtWidgets import QMainWindow, QPlainTextEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator
from PyQt5.uic import loadUi
from DigitalBox.Connection import data
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from DigitalBox.lib import *
from . import state
from .paths import AUTO_TEST_PATH, QT_DESIGNER
from .styles import ButtonStyleOff, ButtonStyleOff2, MainScreenStyle


class CreateAutoTest(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Dict = {}
        self.DictRunTest ={}
        # to store files in a list
        self.listDirectory = []
        self.dir_list = os.listdir(AUTO_TEST_PATH)
        self.dir_list.insert(0,'')
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
        state.mainWindow.closeRunAutoTest()    
    def testButton(self):
        # Kill all child processes
        for child in self.all_processes:
            child.kill()
            #self.pQ.kill()
    
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
        self.runAllTest()
        #self.thread_run_test.start(self.runAllTest)
    
    def runAllTest(self):
        self.listScript =[]
        self.all_processes = []
        for index in range(len(self.listDirectory)):
            iterator = QTreeWidgetItemIterator(self.tree,QTreeWidgetItemIterator.Checked)
            while iterator.value():
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
        DacScreen = QT_DESIGNER / 'AutoTest.ui'
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
        state.mainWindow.closeRunAutoTest()    
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
