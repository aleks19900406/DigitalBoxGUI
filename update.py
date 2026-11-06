import sys
import subprocess
import os
from pathlib import Path
from PyQt6.QtWidgets import QPushButton, QLabel, QVBoxLayout, QWidget, QApplication
from PyQt6.QtCore import QThread, pyqtSignal


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
# only these files/folders (any extension, e.g. BOX_GUI.exe) are taken from git, everything else stays local
UPDATED_ITEMS = ("BOX_GUI", "OvenDeviceConnect", "update")


def run_git(directory, *arguments, check=True, input=None):
    environment = os.environ.copy()
    environment["GIT_TERMINAL_PROMPT"] = "0"
    environment["GIT_LITERAL_PATHSPECS"] = "1"
    result = subprocess.run(
        ["git", "-C", str(directory), *arguments],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, input=input,
        encoding="utf-8", errors="replace", env=environment,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Git update failed.")
    return result


def is_updated_item(path):
    """True when the first part of the path is one of UPDATED_ITEMS (file with any extension or folder)."""
    first = path.split("/", 1)[0].casefold()
    return any(first == name.casefold() or first.startswith(name.casefold() + ".") for name in UPDATED_ITEMS)


def move_running_executable(repository, files):
    """A running exe cannot be overwritten on Windows, but it can be renamed."""
    if not getattr(sys, "frozen", False):
        return None
    executable = Path(sys.executable).resolve()
    try:
        relative = executable.relative_to(repository).as_posix()
    except ValueError:
        return None
    if relative not in files:
        return None
    old = executable.with_name(executable.name + ".old")
    if old.exists():
        old.unlink()
    executable.rename(old)
    return executable, old


def update_repository(directory=APP_DIR, status=None):
    directory = Path(directory).resolve()
    repository = Path(run_git(directory, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    prefix = directory.relative_to(repository).as_posix()
    prefix = "" if prefix == "." else prefix + "/"
    if status:
        status("Checking the configured GitLab branch for updates...")
    run_git(repository, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    run_git(repository, "fetch")
    upstream = run_git(repository, "rev-parse", "@{upstream}").stdout.strip()
    tree = run_git(repository, "ls-tree", "-r", "-z", "--name-only", upstream).stdout.split("\0")
    files = [path for path in tree if path.startswith(prefix) and is_updated_item(path[len(prefix):])]
    if not files:
        raise RuntimeError(f"No {', '.join(UPDATED_ITEMS)} files found on the update branch. No files were changed.")
    if status:
        status(f"Updating {', '.join(UPDATED_ITEMS)} ({len(files)} files)...")
    moved = move_running_executable(repository, files)
    try:
        run_git(repository, "checkout", upstream, "--pathspec-from-file=-", "--pathspec-file-nul", input="\0".join(files))
    except Exception:
        if moved and not moved[0].exists():
            moved[1].rename(moved[0])
        raise
    updated = sorted({path[len(prefix):].split("/", 1)[0] for path in files})
    return f"Updated to {upstream[:8]}: {', '.join(updated)}"

class GitPullThread(QThread):
    # Define a signal to communicate the result back to the main thread
    update_status = pyqtSignal(str)
    #disableButton = pyqtSignal()  # Signal to disable the button
    restartBox = pyqtSignal()  # Signal to disable the button
    buttonEnable = pyqtSignal()
    def run(self):
        try:
            output = update_repository(status=self.update_status.emit)
            self.update_status.emit(f"Update completed; all other local files preserved.\n{output}")
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
        if self.restart_program('BOX_GUI.exe' if os.name == "nt" else 'BOX_GUI'):
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


def main():
    # remove the old update exe left behind by the previous update
    try:
        (APP_DIR / "update.exe.old").unlink()
    except OSError:
        pass
    app = QApplication(sys.argv)
    # Create and show the main window
    window = GitPullApp()
    window.show()
    sys.exit(app.exec())
    # Run the application event loop

# Run the script
if __name__ == "__main__":
    main()