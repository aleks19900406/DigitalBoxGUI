from time import sleep
from PyQt5.QtCore import QObject, pyqtSignal


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
