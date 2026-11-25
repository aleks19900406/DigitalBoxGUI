"""Simple GitHub update checker - replaces old GitLab update."""

from PyQt6.QtWidgets import QMessageBox, QProgressDialog
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from pathlib import Path
import subprocess
import sys

try:
    import requests
    from packaging import version
except ImportError:
    requests = None
    version = None


class CheckUpdateThread(QThread):
    """Background thread to check for GitHub updates."""

    update_checked = pyqtSignal(dict)

    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
        self.daemon = True

    def run(self):
        """Check GitHub for updates."""
        if requests is None or version is None:
            self.update_checked.emit({
                "has_update": False,
                "version": None,
                "error": "requests or packaging not installed",
            })
            return

        try:
            url = "https://api.github.com/repos/aleks19900406/DigitalBoxGUI/releases/latest"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            release = response.json()
            latest_tag = release.get("tag_name", "").lstrip("v")

            try:
                has_update = version.parse(latest_tag) > version.parse(self.current_version)
            except Exception:
                has_update = False

            download_url = None
            for asset in release.get("assets", []):
                if asset.get("name", "").endswith(".exe"):
                    download_url = asset.get("browser_download_url")
                    break

            self.update_checked.emit({
                "has_update": has_update,
                "version": latest_tag,
                "download_url": download_url,
                "error": None,
            })

        except Exception as e:
            self.update_checked.emit({
                "has_update": False,
                "version": None,
                "error": str(e),
            })
        finally:
            self.quit()


def check_github_updates(parent_window, current_version: str = "5.4.0") -> bool:
    """Check GitHub for updates and show dialog."""
    if requests is None or version is None:
        QMessageBox.warning(
            parent_window,
            "Dependencies Missing",
            "requests or packaging library not installed.\n"
            "Run: pip install requests packaging"
        )
        return False

    progress = QProgressDialog("Checking for updates...", None, 0, 0, parent_window)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.show()

    check_thread = CheckUpdateThread(current_version)
    parent_window._update_check_thread = check_thread

    def on_update_checked(result):
        progress.close()

        try:
            check_thread.quit()
            check_thread.wait()
        except:
            pass

        if result.get("error"):
            QMessageBox.warning(
                parent_window,
                "Update Check Failed",
                f"Could not check for updates:\n{result['error']}"
            )
            return

        if not result.get("has_update"):
            new_version = result.get("version", "unknown")
            QMessageBox.information(
                parent_window,
                "No Updates Available",
                f"You are using the latest version.\n"
                f"Current: {current_version}\n"
                f"Latest: {new_version}"
            )
            return

        new_version = result.get("version", "unknown")
        reply = QMessageBox.question(
            parent_window,
            "Update Available",
            f"A new version is available!\n\n"
            f"Current: {current_version}\n"
            f"Latest: {new_version}\n\n"
            f"Update now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            parent_window.perform_github_update(result)

    check_thread.update_checked.connect(on_update_checked)
    check_thread.start()

    return True


def download_and_update(download_url: str, current_exe: Path) -> bool:
    """Download new version and prepare update."""
    if requests is None:
        return False

    try:
        temp_path = current_exe.parent / ".update_temp.exe"

        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()

        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        old_path = current_exe.parent / ".update_old.exe"
        if old_path.exists():
            old_path.unlink()

        if current_exe.exists():
            current_exe.rename(old_path)

        temp_path.rename(current_exe)

        if old_path.exists():
            old_path.unlink()

        return True

    except Exception as e:
        print(f"Update failed: {e}")
        return False
