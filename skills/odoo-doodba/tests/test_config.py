import tempfile
import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parents[1] / 'indexer' / 'scripts'))
from config import find_odoo_path


class OdooPathTest(unittest.TestCase):
    def test_finds_community_tree_from_addons_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'addons').mkdir()
            self.assertEqual(find_odoo_path([root]), root)

    def test_falls_back_when_candidates_are_not_source_trees(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fallback = Path.cwd()
            self.assertEqual(find_odoo_path([root]), fallback)

    def test_ignores_unsupported_version_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / 'odoo16'
            current = root / 'odoo17'
            (old / 'odoo').mkdir(parents=True)
            (current / 'odoo').mkdir(parents=True)
            (old / 'odoo' / 'release.py').write_text('version_info = (16, 0, 0, FINAL, 0, "")\n')
            (current / 'odoo' / 'release.py').write_text('version_info = (17, 0, 0, FINAL, 0, "")\n')
            self.assertEqual(find_odoo_path([old, current]), current)


if __name__ == '__main__':
    unittest.main()
