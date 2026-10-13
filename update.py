import sys
import subprocess
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from PyQt5.QtWidgets import QPushButton, QLabel, QVBoxLayout, QWidget, QApplication
from PyQt5.QtCore import QThread, pyqtSignal


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
PROTECTED_DIRECTORIES = ("data", "config_file")


def run_git(directory, *arguments, check=True):
    environment = os.environ.copy()
    environment["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(
        ["git", "-C", str(directory), *arguments],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8", errors="replace", env=environment,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Git update failed.")
    return result


def update_repository(directory=APP_DIR, status=None):
    directory = Path(directory).resolve()
    repository = Path(run_git(directory, "rev-parse", "--show-toplevel").stdout.strip())
    protected_paths = [(directory / name).relative_to(repository).as_posix() for name in PROTECTED_DIRECTORIES]
    exclusions = [f":(top,exclude,literal){name}" for name in protected_paths]
    staged = run_git(repository, "diff", "--cached", "--quiet", check=False)
    if staged.returncode == 1:
        raise RuntimeError("Finish or unstage the prepared commit before updating. No files were changed.")
    if staged.returncode:
        raise RuntimeError(staged.stderr.strip())
    dirty = run_git(repository, "diff", "--quiet", "--", ".", *exclusions, check=False)
    if dirty.returncode == 1:
        raise RuntimeError("Local code changes outside data/config_file prevent updating. Save or commit them first.")
    if dirty.returncode:
        raise RuntimeError(dirty.stderr.strip())
    run_git(repository, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    for name in PROTECTED_DIRECTORIES:
        if (directory / name).is_symlink():
            raise RuntimeError(f"Cannot update with a symbolic link as the protected directory: {name}")
    backup = Path(tempfile.mkdtemp(prefix="box-gui-update-"))
    existed = {}
    try:
        for name in PROTECTED_DIRECTORIES:
            source = directory / name
            existed[name] = source.exists()
            if source.is_dir():
                shutil.copytree(source, backup / name, symlinks=True)
            elif source.exists():
                shutil.copy2(source, backup / name)
    except Exception:
        shutil.rmtree(backup)
        raise
    previous_stash = run_git(repository, "rev-parse", "--verify", "refs/stash", check=False).stdout.strip()
    saved_stash = None
    try:
        if status:
            status("Protecting local data and configuration...")
        run_git(repository, "stash", "push", "--all", "--message", "box-gui-update-" + uuid.uuid4().hex,
                "--", *[f":(top,literal){name}" for name in protected_paths])
        current_stash = run_git(repository, "rev-parse", "--verify", "refs/stash", check=False).stdout.strip()
        if current_stash and current_stash != previous_stash:
            saved_stash = current_stash
        if status:
            status("Checking the configured GitLab branch for updates...")
        result = run_git(repository, "pull", "--ff-only")
    finally:
        try:
            for name in PROTECTED_DIRECTORIES:
                target = directory / name
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target)
                elif target.exists() or target.is_symlink():
                    target.unlink()
                if existed[name]:
                    source = backup / name
                    if source.is_dir():
                        shutil.copytree(source, target, symlinks=True)
                    else:
                        shutil.copy2(source, target)
        except Exception as error:
            raise RuntimeError(f"Could not restore local data. Backup retained at {backup}: {error}") from error
        if saved_stash:
            stashes = run_git(repository, "stash", "list", "--format=%H").stdout.splitlines()
            if saved_stash in stashes:
                run_git(repository, "stash", "drop", f"stash@{{{stashes.index(saved_stash)}}}")
        shutil.rmtree(backup)
    return (result.stdout + result.stderr).strip()

class GitPullThread(QThread):
    # Define a signal to communicate the result back to the main thread
    update_status = pyqtSignal(str)
    #disableButton = pyqtSignal()  # Signal to disable the button
    restartBox = pyqtSignal()  # Signal to disable the button
    buttonEnable = pyqtSignal()
    def run(self):
        try:
            output = update_repository(status=self.update_status.emit)
            self.update_status.emit(f"Update completed; local data and configuration preserved.\n{output}")
            self.restartBox.emit()
        except Exception as error:
            self.update_status.emit(f"Update failed: {error}")
            self.buttonEnable.emit()
    def stop(self):
        self.wait()
    
    
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
        self.status_label.setWordWrap(True)

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
        if self.restart_program('BOX_GUI.exe'):
            self.close()

    def restart_program(self,exe_path):
        try:
            executable = APP_DIR / exe_path
            if executable.is_file():
                command = [str(executable)]
            elif not getattr(sys, "frozen", False) and (APP_DIR / "BOX_GUI.py").is_file():
                command = [sys.executable, str(APP_DIR / "BOX_GUI.py")]
            else:
                raise FileNotFoundError(str(executable))
            subprocess.Popen(command, cwd=str(APP_DIR))
            return True
        except Exception as e:
            self.update_status_label(f"Update completed, but restarting failed: {e}")
            self.enable_button()
            return False

    def closeEvent(self, event):
        if self.git_thread.isRunning():
            event.ignore()
        else:
            event.accept()


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
    app = QApplication(sys.argv)
    # Create and show the main window
    window = GitPullApp()
    window.show()
    sys.exit(app.exec_())
    # Run the application event loop

# Run the script
if __name__ == "__main__":
    main()