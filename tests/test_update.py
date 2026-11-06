"""Exercise selective updates (BOX_GUI, OvenDeviceConnect, update) with real, local Git repositories."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from update import update_repository


class UpdateTests(unittest.TestCase):
    def git(self, directory, *arguments):
        result = subprocess.run(
            ["git", "-C", str(directory), "-c", "user.name=Update Test", "-c", "user.email=update@example.invalid", *arguments],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        if result.returncode:
            self.fail(result.stderr)
        return result.stdout.strip()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="update test ")
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.remote = root / "remote.git"
        self.author = root / "author"
        self.local = root / "local"
        self.remote.mkdir()
        self.git(self.remote, "init", "--bare")
        self.git(root, "clone", str(self.remote), str(self.author))
        self.write(self.author, {
            "BOX_GUI.exe": "old gui", "update.exe": "old update",
            "OvenDeviceConnect/dist/OvenDeviceConnect.exe": "old oven",
            "code.py": "old code", "updater_notes.txt": "old notes",
            "data/value.txt": "old data", "config_file/settings.json": "old config",
        })
        self.git(self.author, "add", ".")
        self.git(self.author, "commit", "-m", "initial")
        self.git(self.author, "push", "-u", "origin", "HEAD")
        self.git(root, "clone", str(self.remote), str(self.local))

    def write(self, directory, files):
        for name, text in files.items():
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def read(self, name):
        return (self.local / name).read_text(encoding="utf-8")

    def publish_update(self):
        self.write(self.author, {
            "BOX_GUI.exe": "new gui", "update.exe": "new update",
            "OvenDeviceConnect/dist/OvenDeviceConnect.exe": "new oven",
            "OvenDeviceConnect/dist/new.dll": "new dll",
            "code.py": "new code", "updater_notes.txt": "new notes",
            "data/value.txt": "remote data", "config_file/settings.json": "remote config",
        })
        self.git(self.author, "add", ".")
        self.git(self.author, "commit", "-m", "update")
        self.git(self.author, "push")

    def test_only_selected_items_are_updated(self):
        self.write(self.local, {"data/value.txt": "local data", "BOX_GUI.exe": "local gui", "code.py": "local code"})
        self.publish_update()
        update_repository(self.local)
        self.assertEqual(self.read("BOX_GUI.exe"), "new gui")
        self.assertEqual(self.read("update.exe"), "new update")
        self.assertEqual(self.read("OvenDeviceConnect/dist/OvenDeviceConnect.exe"), "new oven")
        self.assertEqual(self.read("OvenDeviceConnect/dist/new.dll"), "new dll")
        self.assertEqual(self.read("code.py"), "local code")
        self.assertEqual(self.read("updater_notes.txt"), "old notes")
        self.assertEqual(self.read("data/value.txt"), "local data")
        self.assertEqual(self.read("config_file/settings.json"), "old config")
        update_repository(self.local)
        self.assertEqual(self.read("BOX_GUI.exe"), "new gui")

    def test_update_from_subdirectory(self):
        self.write(self.author, {"app/BOX_GUI.exe": "old gui", "app/code.py": "old code"})
        self.git(self.author, "add", ".")
        self.git(self.author, "commit", "-m", "app")
        self.git(self.author, "push")
        self.git(self.local, "pull")
        self.write(self.author, {"app/BOX_GUI.exe": "new gui", "app/code.py": "new code"})
        self.publish_update()
        update_repository(self.local / "app")
        self.assertEqual(self.read("app/BOX_GUI.exe"), "new gui")
        self.assertEqual(self.read("app/code.py"), "old code")
        self.assertEqual(self.read("BOX_GUI.exe"), "old gui")

    def test_unavailable_remote_changes_nothing(self):
        original_head = self.git(self.local, "rev-parse", "HEAD")
        self.git(self.local, "remote", "set-url", "origin", str(self.local.parent / "missing.git"))
        with self.assertRaises(RuntimeError):
            update_repository(self.local)
        self.assertEqual(self.read("BOX_GUI.exe"), "old gui")
        self.assertEqual(self.git(self.local, "rev-parse", "HEAD"), original_head)


if __name__ == "__main__":
    unittest.main()