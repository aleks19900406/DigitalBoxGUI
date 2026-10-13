"""Exercise protected-directory updates with real, local Git repositories."""

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
        for name, text in {
            "code.py": "old code", "data/value.txt": "old data",
            "data/deleted.txt": "old delete", "config_file/settings.json": "old config",
            ".gitignore": "data/*.log\n",
        }.items():
            path = self.author / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.git(self.author, "add", ".")
        self.git(self.author, "commit", "-m", "initial")
        self.git(self.author, "push", "-u", "origin", "HEAD")
        self.git(root, "clone", str(self.remote), str(self.local))

    def publish_update(self):
        (self.author / "code.py").write_text("new code", encoding="utf-8")
        (self.author / "data" / "value.txt").write_text("remote data", encoding="utf-8")
        (self.author / "config_file" / "settings.json").write_text("remote config", encoding="utf-8")
        (self.author / "data" / "remote-only.txt").write_text("new remote data", encoding="utf-8")
        self.git(self.author, "add", ".")
        self.git(self.author, "commit", "-m", "update")
        self.git(self.author, "push")

    def local_data(self):
        return {
            str(path.relative_to(self.local)): path.read_bytes()
            for name in ("data", "config_file")
            for path in (self.local / name).rglob("*") if path.is_file()
        }

    def change_local_data(self):
        (self.local / "data" / "value.txt").write_text("local measurements", encoding="utf-8")
        (self.local / "data" / "deleted.txt").unlink()
        (self.local / "data" / "new.txt").write_text("local only", encoding="utf-8")
        (self.local / "data" / "remote-only.txt").write_text("local file with remote name", encoding="utf-8")
        (self.local / "data" / "session.log").write_text("ignored data", encoding="utf-8")
        (self.local / "config_file" / "settings.json").write_text("local config", encoding="utf-8")

    def test_pull_preserves_all_local_data_and_existing_stash(self):
        (self.local / "code.py").write_text("saved work", encoding="utf-8")
        self.git(self.local, "stash", "push", "-m", "existing user stash")
        previous_stash = self.git(self.local, "stash", "list", "--format=%H")
        self.change_local_data()
        before = self.local_data()
        self.publish_update()
        update_repository(self.local)
        self.assertEqual(self.local_data(), before)
        self.assertEqual((self.local / "code.py").read_text(encoding="utf-8"), "new code")
        self.assertEqual(self.git(self.local, "rev-parse", "HEAD"), self.git(self.author, "rev-parse", "HEAD"))
        self.assertEqual(self.git(self.local, "stash", "list", "--format=%H"), previous_stash)
        update_repository(self.local)
        self.assertEqual(self.local_data(), before)

    def test_dirty_code_is_not_overwritten(self):
        self.change_local_data()
        before = self.local_data()
        (self.local / "code.py").write_text("local code", encoding="utf-8")
        self.publish_update()
        with self.assertRaisesRegex(RuntimeError, "Local code changes"):
            update_repository(self.local)
        self.assertEqual(self.local_data(), before)
        self.assertEqual((self.local / "code.py").read_text(encoding="utf-8"), "local code")

    def test_staged_changes_are_preserved(self):
        self.change_local_data()
        self.git(self.local, "add", "data/value.txt")
        before = self.git(self.local, "diff", "--cached")
        with self.assertRaisesRegex(RuntimeError, "prepared commit"):
            update_repository(self.local)
        self.assertEqual(self.git(self.local, "diff", "--cached"), before)

    def test_failed_fast_forward_restores_local_data(self):
        (self.local / "local-code.py").write_text("local commit", encoding="utf-8")
        self.git(self.local, "add", "local-code.py")
        self.git(self.local, "commit", "-m", "local commit")
        self.change_local_data()
        before = self.local_data()
        self.publish_update()
        with self.assertRaises(RuntimeError):
            update_repository(self.local)
        self.assertEqual(self.local_data(), before)
        self.assertEqual(self.git(self.local, "stash", "list"), "")

    def test_unavailable_remote_restores_local_data(self):
        self.change_local_data()
        before = self.local_data()
        original_head = self.git(self.local, "rev-parse", "HEAD")
        self.git(self.local, "remote", "set-url", "origin", str(self.local.parent / "missing.git"))
        with self.assertRaises(RuntimeError):
            update_repository(self.local)
        self.assertEqual(self.local_data(), before)
        self.assertEqual(self.git(self.local, "rev-parse", "HEAD"), original_head)
        self.assertEqual(self.git(self.local, "stash", "list"), "")


if __name__ == "__main__":
    unittest.main()