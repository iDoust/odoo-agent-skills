import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from validate import _core_files, validate_repository


class ValidateRepositoryTest(unittest.TestCase):
    def test_current_repository_is_valid(self):
        errors = validate_repository(Path(__file__).parent.parent)
        self.assertEqual(errors, [])

    def test_rejects_vendor_coupling_in_core_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "skills" / "example"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: example\ndescription: Example skill.\n---\n"
                "Use Claude for this task.\n",
                encoding="utf-8",
            )
            for version in ("17", "18", "19"):
                versions = root / "references" / "versions"
                versions.mkdir(parents=True, exist_ok=True)
                (versions / f"{version}.md").write_text("# Version\n", encoding="utf-8")

            errors = validate_repository(root)

        self.assertTrue(any("vendor coupling" in error for error in errors))

    def test_rejects_root_claude_marketplace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".claude-plugin").mkdir()
            for version in ("17", "18", "19"):
                versions = root / "references" / "versions"
                versions.mkdir(parents=True, exist_ok=True)
                (versions / f"{version}.md").write_text("# Version\n", encoding="utf-8")

            errors = validate_repository(root)

        self.assertTrue(any("root .claude-plugin" in error for error in errors))

    def test_ignores_generated_binary_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "skills" / "example" / "target" / "debug"
            artifact.mkdir(parents=True)
            (artifact / "binary").write_bytes(b"not utf-8")

            self.assertEqual(_core_files(root), [])


if __name__ == "__main__":
    unittest.main()
