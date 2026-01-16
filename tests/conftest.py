"""Shared pytest fixtures for file organizer tests."""

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "file-organizer"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from file_organizer import Config


@pytest.fixture()
def temp_config(tmp_path: Path) -> Config:
    """Create a temporary configuration isolated from user files."""
    cfg_path = tmp_path / "config.yaml"
    cfg = Config(cfg_path)
    cfg.set("organization.base_path", str(tmp_path / "organized"))
    cfg.set("organization.structure", ["{filename}"])
    cfg.set("organization.naming.template", "{original_name}")
    cfg.set("organization.naming.replace_spaces", "_")
    cfg.set("safety.create_backup", False)
    cfg.set("safety.backup_path", str(tmp_path / "backups"))
    cfg.set("sources.local.paths", [])
    cfg.save()
    return cfg
