"""Tests for external source scanners."""

from unittest.mock import patch

import pytest

from file_organizer.sources import gdrive, github


def test_github_scan_missing_gh_binary(tmp_path):
    """GitHub scan surfaces missing gh CLI errors."""
    scanner = github.GitHubScanner(clone_path=str(tmp_path))

    with patch("file_organizer.sources.github.subprocess.run", side_effect=FileNotFoundError("gh not found")):
        with pytest.raises(FileNotFoundError):
            scanner.scan()


def test_gdrive_missing_dependencies_raises_import_error(monkeypatch, tmp_path):
    """Google Drive scanner fails fast when dependencies are unavailable."""
    monkeypatch.setattr(gdrive, "GDRIVE_AVAILABLE", False)

    with pytest.raises(ImportError):
        gdrive.GoogleDriveScanner(credentials_path=str(tmp_path / "creds.json"))


def test_gdrive_workspace_files_skipped_without_download(monkeypatch, tmp_path):
    """Workspace files are skipped when download=False."""
    monkeypatch.setattr(gdrive, "GDRIVE_AVAILABLE", True)
    scanner = gdrive.GoogleDriveScanner(
        credentials_path=str(tmp_path / "creds.json"),
        download_path=str(tmp_path / "downloads"),
    )

    item = {
        "id": "file-1",
        "name": "Spec Doc",
        "mimeType": "application/vnd.google-apps.document",
        "size": "0",
        "createdTime": "2023-01-01T00:00:00Z",
        "modifiedTime": "2023-01-02T00:00:00Z",
    }

    assert scanner._create_file_metadata(item, download=False) is None
