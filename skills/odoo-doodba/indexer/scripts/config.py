"""Configuration management for the local Odoo indexer."""

import os
import re
from pathlib import Path


def _looks_like_odoo_tree(path: Path) -> bool:
    release_file = path / 'odoo' / 'release.py'
    if release_file.is_file():
        match = re.search(r'version_info\s*=\s*\((\d+),', release_file.read_text(encoding='utf-8'))
        if match and not 17 <= int(match.group(1)) <= 19:
            return False
    return (
        (path / 'addons').is_dir()
        or (path / 'odoo' / 'addons').is_dir()
        or (path / 'odoo' / 'release.py').is_file()
        or any(path.glob('*/__manifest__.py'))
    )


def find_odoo_path(candidates: list[Path]) -> Path:
    """Return the first candidate that looks like an Odoo source tree."""
    for path in candidates:
        if path.is_dir() and _looks_like_odoo_tree(path):
            return path
    return Path.cwd()


_configured_path = os.getenv('ODOO_PATH')
if _configured_path:
    ODOO_PATH = Path(_configured_path)
else:
    ODOO_PATH = find_odoo_path([
        Path.cwd(),
        Path.cwd() / 'odoo',
        Path.cwd() / 'src',
        Path.home() / 'odoo',
        *sorted(Path.home().glob('odoo*')),
    ])

# Optional settings
SQLITE_DB_PATH = Path(os.getenv('SQLITE_DB_PATH', str(Path.home() / '.odoo-indexer' / 'odoo_indexer.sqlite3')))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
MAX_CONCURRENT_MODULES = int(os.getenv('MAX_CONCURRENT_MODULES', '4'))
MAX_WORKER_PROCESSES = int(os.getenv('MAX_WORKER_PROCESSES', '0'))  # 0 = use CPU count
