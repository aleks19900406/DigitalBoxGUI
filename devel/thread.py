import time
import sys
from PyQt5.QtCore import pyqtSlot, QThreadPool, QTimer
from PyQt5.QtWidgets import (
    QLabel,
    QWidget,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QApplication,
)


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setFixedSize(250, 100)
        self.setWindowTitle("Sheep Picker")

        self.sheep_number = 1
        self.timer = QTimer()
        self.picked_sheep_label = QLabel()
        self.counted_sheep_label = QLabel()

        self.layout = QVBoxLayout()
        self.main_widget = QWidget()
        self.thread_manager = QThreadPool()
        self.pick_sheep_button = QPushButton("Pick a sheep!")
        self.layout.addWidget(self.counted_sheep_label)
        self.layout.addWidget(self.pick_sheep_button)
        self.layout.addWidget(self.picked_sheep_label)

        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

        self.timer.timeout.connect(self.count_sheep)
        #self.pick_sheep_button.pressed.connect(self.pick_sheep_safely)
        self.DIGITAL_BOX_MAIN = QTimer()
        self.DIGITAL_BOX_MAIN.setInterval(3000)
        self.DIGITAL_BOX_MAIN.timeout.connect(self.pick_sheep_safely) #
        self.DIGITAL_BOX_MAIN.start() 
        self.timer.start()

    def count_sheep(self):
        self.sheep_number += 1
        self.counted_sheep_label.setText(f"Counted {self.sheep_number} sheep.")


    def pick_sheep(self):
        self.picked_sheep_label.setText(f"Sheep {self.sheep_number} picked!")
        print('executing 5s')
        for a  in range(10):
            print(a)
            time.sleep(1)
        

    def pick_sheep_safely(self):
        self.thread_manager.start(self.pick_sheep)  # ...since .start() is used!


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    app.exec()