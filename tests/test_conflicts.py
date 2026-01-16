"""Tests for conflict resolution strategies."""

from pathlib import Path

from file_organizer import FileOrganizer
from file_organizer.models import FileMetadata


def _build_file_metadata(path: Path) -> FileMetadata:
    return FileMetadata.from_path(path, source_type="local")


def test_conflict_resolution_rename(temp_config, tmp_path):
    """Rename strategy appends a numeric suffix."""
    temp_config.set("safety.conflict_resolution", "rename")
    temp_config.save()

    source = tmp_path / "report.txt"
    source.write_text("new")

    base_path = Path(temp_config.get("organization.base_path"))
    base_path.mkdir(parents=True, exist_ok=True)
    existing = base_path / source.name
    existing.write_text("old")

    organizer = FileOrganizer(temp_config)
    plan = organizer.create_organization_plan([_build_file_metadata(source)])[0]

    assert plan.destination_path.name == "report_1.txt"
    assert not plan.skip
    assert not plan.conflict


def test_conflict_resolution_skip(temp_config, tmp_path):
    """Skip strategy marks the plan as skipped."""
    temp_config.set("safety.conflict_resolution", "skip")
    temp_config.save()

    source = tmp_path / "notes.txt"
    source.write_text("new")

    base_path = Path(temp_config.get("organization.base_path"))
    base_path.mkdir(parents=True, exist_ok=True)
    existing = base_path / source.name
    existing.write_text("old")

    organizer = FileOrganizer(temp_config)
    plan = organizer.create_organization_plan([_build_file_metadata(source)])[0]

    assert plan.skip
    assert plan.skip_reason == "File already exists"


def test_conflict_resolution_overwrite(temp_config, tmp_path):
    """Overwrite strategy keeps the original destination path."""
    temp_config.set("safety.conflict_resolution", "overwrite")
    temp_config.save()

    source = tmp_path / "photo.png"
    source.write_text("new")

    base_path = Path(temp_config.get("organization.base_path"))
    base_path.mkdir(parents=True, exist_ok=True)
    existing = base_path / source.name
    existing.write_text("old")

    organizer = FileOrganizer(temp_config)
    plan = organizer.create_organization_plan([_build_file_metadata(source)])[0]

    assert plan.destination_path == existing
    assert not plan.skip
    assert not plan.conflict
