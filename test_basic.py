"""Basic functionality tests for file organizer."""

from pathlib import Path

import pytest

from file_organizer import Config, FileOrganizer, UnifiedScanner
from file_organizer.sources import LocalScanner


@pytest.fixture()
def temp_config(tmp_path: Path) -> Config:
    """Create a temporary configuration isolated from user files."""
    cfg_path = tmp_path / "config.yaml"
    cfg = Config(cfg_path)
    cfg.set("organization.base_path", str(tmp_path / "organized"))
    cfg.set("safety.create_backup", False)
    cfg.set("safety.backup_path", str(tmp_path / "backups"))
    cfg.set("sources.local.paths", [])
    cfg.save()
    return cfg


def test_config_creation_and_defaults(temp_config: Config):
    """Config is created with sensible defaults and remains loadable."""
    assert temp_config.config_path.exists()
    assert temp_config.get("organization.base_path") is not None
    # Ensure empty/invalid config would regenerate defaults
    temp_config.config_path.write_text("")
    temp_config.load()
    assert temp_config.get("organization.categories")  # defaults restored


def test_local_scanner_reads_sample_files(temp_config: Config):
    """Local scanner finds files in the bundled test_files directory."""
    sample_dir = Path(__file__).parent / "test_files" / "docs"
    scanner = LocalScanner(exclude_patterns=[".git"])
    result = scanner.scan([str(sample_dir)])

    assert len(result.files) == 2
    filenames = sorted(f.filename for f in result.files)
    assert filenames == ["data.csv", "readme.md"]
    assert result.total_size >= 0
    assert not result.errors


def test_create_plan_and_execute_copy(temp_config: Config, tmp_path: Path):
    """Create an organization plan and copy files into the temp base path."""
    sample_dir = Path(__file__).parent / "test_files" / "docs"
    # Point config to the sample directory via the unified scanner
    temp_config.set("sources.local.paths", [str(sample_dir)])
    temp_config.save()
    unified = UnifiedScanner(temp_config)
    files = unified.get_all_files()
    assert files, "Unified scanner should return files"

    organizer = FileOrganizer(temp_config)
    plans = organizer.create_organization_plan(files)
    assert plans, "Organization plans should be generated"

    transactions = organizer.execute_plan(plans, dry_run=False)
    assert all(t.success for t in transactions)

    # Files should now exist in the configured base path
    for plan in plans:
        assert plan.destination_path.exists()


def test_dry_run_does_not_create_files(temp_config: Config):
    """Dry runs mark success without touching the filesystem."""
    sample_dir = Path(__file__).parent / "test_files" / "docs"
    scanner = LocalScanner()
    scan_result = scanner.scan([str(sample_dir)])

    organizer = FileOrganizer(temp_config)
    plans = organizer.create_organization_plan(scan_result.files)
    txns = organizer.execute_plan(plans, dry_run=True)

    assert all(t.success for t in txns)
    for plan in plans:
        assert not plan.destination_path.exists()
