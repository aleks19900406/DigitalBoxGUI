from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox,QMainWindow,QSlider,QAbstractButton,QApplication

import sys

class Slider(QSlider):
    minimumChanged = QtCore.Signal(int)
    maximumChanged = QtCore.Signal(int)

    def setMinimum(self, minimum):
        self.minimumChanged.emit(minimum)
        super(Slider, self).setMinimum(minimum)

    def setMaximum(self, maximum):
        self.maximumChanged.emit(maximum)
        super(Slider, self).setMaximum(maximum)

class Example(QMainWindow):
    def __init__(self):
        super(Example, self).__init__()
        self.initUI()

    def initUI(self):
        self.label = QtGui.QLabel(alignment=QtCore.Qt.AlignCenter)

        self.slider = Slider(tickPosition=QtGui.QSlider.TicksLeft,
            orientation=QtCore.Qt.Horizontal)
        slider_vbox = QtGui.QVBoxLayout()
        slider_hbox = QtGui.QHBoxLayout()
        slider_hbox.setContentsMargins(0, 0, 0, 0)
        slider_vbox.setContentsMargins(0, 0, 0, 0)
        slider_vbox.setSpacing(0)
        label_minimum = QtGui.QLabel(alignment=QtCore.Qt.AlignLeft)
        self.slider.minimumChanged.connect(label_minimum.setNum)
        label_maximum = QtGui.QLabel(alignment=QtCore.Qt.AlignRight)
        self.slider.maximumChanged.connect(label_maximum.setNum)
        slider_vbox.addWidget(self.slider)
        slider_vbox.addLayout(slider_hbox)
        slider_hbox.addWidget(label_minimum, QtCore.Qt.AlignLeft)
        slider_hbox.addWidget(label_maximum, QtCore.Qt.AlignRight)
        slider_vbox.addStretch()

        self.slider.setMinimum(0)
        self.slider.setMaximum(100)

        vbox = QtGui.QVBoxLayout(self)
        vbox.addLayout(slider_vbox)
        vbox.addWidget(self.label)
        self.setGeometry(300, 300, 300, 150)
        self.slider.valueChanged.connect(self.label.setNum)
        self.show()

def main():    
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()