import sys
import subprocess
from PyQt5.QtWidgets import QPushButton, QLabel, QVBoxLayout, QWidget, QApplication
from PyQt5.QtCore import QThread, pyqtSignal
from time import sleep

class GitPullThread(QThread):
    # Define a signal to communicate the result back to the main thread
    update_status = pyqtSignal(str)
    #disableButton = pyqtSignal()  # Signal to disable the button
    restartBox = pyqtSignal()  # Signal to disable the button
    buttonEnable = pyqtSignal()
    def run(self):
        # Run the git pull command in the background
        result = subprocess.run("git pull", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.update_status.emit( result.stdout)
        # Check if the pull was successful and emit the appropriate status
        if result.returncode == 0:
            self.update_status.emit(f"Successfully pulled the latest updates.\n{result.stdout}")
            #self.disableButton.emit()
            self.restartBox.emit()
        else:
            self.update_status.emit(f"Error pulling updates: {result.stderr}\n !!! Connect to local network or turn on VPN !!!")
            self.buttonEnable.emit()
    def stop(self):
        self.quit()  # Gracefully quit the event loop (if running)
        self.wait()  # Wait for the thread to finish cleanup
        self.terminate()
    
    
class GitPullApp(QWidget):
    def __init__(self):
        super().__init__()
        
        self.init_ui()
        # Initialize the thread for Git pulling
        self.git_thread = GitPullThread()
        self.git_thread.update_status.connect(self.update_status_label)
        self.git_thread.restartBox.connect(self.restart_box)
        self.git_thread.buttonEnable.connect(self.enable_button)
    
    def init_ui(self):
        # Set up the window
        self.setWindowTitle("Git Pull")
        self.setGeometry(300, 300, 400, 200)

        self.pull_button = QPushButton("GUI update", self)
        self.pull_button.clicked.connect(self.pull_updates)
        self.status_label = QLabel("Click the button to pull updates.", self)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.pull_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)
    
    def pull_updates(self):
        # Start the Git pull thread
        self.pull_button.setEnabled(False)
        self.status_label.setText("Pulling updates...")
        self.git_thread.start()

    def update_status_label(self, status_text):
        # This function is called when the thread emits a signal
        self.status_label.setText(status_text)
    
        # Check if git pull was successful and update the label accordingly
    def enable_button(self):
        # This function is called when the close button is clicked
        self.pull_button.setEnabled(True)
       
    def restart_box(self):
        self.close()
        self.restart_program('BOX_GUI.exe')

    def restart_program(self,exe_path):
        try:
            print(f"Restarting {exe_path}...")
            subprocess.run(exe_path, shell=True)
        except Exception as e:
            print(f"Error restarting program: {e}")  


def kill_process(exe_name):
    try:
        result = subprocess.run(f"taskkill /f /im {exe_name}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print(f"Successfully terminated {exe_name}.")
        else:
            print(f"Error: {exe_name} could not be terminated. {result.stderr}")
    except Exception as e:
        print(f"Error occurred while killing process: {e}")

        
def main():
    kill_process('BOX_GUI.exe')
    app = QApplication(sys.argv)
    # Create and show the main window
    window = GitPullApp()
    window.show()
    sys.exit(app.exec_())
    # Run the application event loop

# Run the script
if __name__ == "__main__":
    main()