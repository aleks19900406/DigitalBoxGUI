import sys
import time
from PyQt5.QtCore import QThread, pyqtSignal, QObject, pyqtSlot,QTimer
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QHBoxLayout, QProgressBar, QVBoxLayout


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Widget")
        self.h_box = QHBoxLayout(self)
        self.main_window_button = QPushButton("Start")
        self.popup = PopUpProgressB()  # Creating an instance instead as an attribute instead of creating one 
        # everytime the button is pressed 
        self.main_window_button.clicked.connect(self.popup.start_progress)  # To (re)start the progress
        self.h_box.addWidget(self.main_window_button)
        self.setLayout(self.h_box)
        self.show()


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
            time.sleep(0.1)
            self._step += 1
            self.stepIncreased.emit(self._step)
            time.sleep(0.1)
            print('step',self._step)
        print('finish')
        self._step = 0
        self.finished.emit()
    def stop(self):
        self._isRunning = False


class PopUpProgressB(QWidget):

    def __init__(self):
        super().__init__()
        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(30, 40, 500, 75)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.pbar)
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 550, 100)
        self.setWindowTitle('Progress Bar')
        # self.show()
        self.thread = QThread()
        self.worker = Worker()
        self.worker.stepIncreased.connect(self.on_count_changed)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.task)
        self.value1 = 22
        #self.thread.start()  # This was moved to start_progress

    def start_progress(self):  # To restart the progress every time
        print('start progress')
        self.show()
        self.thread.start()

    def on_count_changed(self, value):
        self.worker.setValue(22)
        self.pbar.setValue(int(value*(100/self.value)))
        if int(value*(100/self.value)) >=100: 
            self.thread.terminate()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())