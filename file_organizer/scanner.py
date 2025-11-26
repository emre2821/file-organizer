"""Unified file scanner coordinating all sources."""

from typing import List, Dict, Any
from .models import FileMetadata, ScanResult
from .config import Config
from .sources import LocalScanner, GitHubScanner, GoogleDriveScanner


class UnifiedScanner:
    """Coordinates scanning from multiple sources."""
    
    def __init__(self, config: Config):
        """Initialize unified scanner.
        
        Args:
            config: Configuration instance
        """
        self.config = config
    
    def scan_all_sources(self) -> Dict[str, ScanResult]:
        """Scan all enabled sources.
        
        Returns:
            Dictionary mapping source type to ScanResult
        """
        results = {}
        
        # Scan local filesystem
        if self.config.get('sources.local.enabled', True):
            local_result = self._scan_local()
            if local_result:
                results['local'] = local_result
        
        # Scan GitHub
        if self.config.get('sources.github.enabled', False):
            github_result = self._scan_github()
            if github_result:
                results['github'] = github_result
        
        # Scan Google Drive
        if self.config.get('sources.google_drive.enabled', False):
            gdrive_result = self._scan_gdrive()
            if gdrive_result:
                results['gdrive'] = gdrive_result
        
        return results
    
    def _scan_local(self) -> ScanResult:
        """Scan local filesystem.
        
        Returns:
            ScanResult or None if no paths configured
        """
        paths = self.config.get('sources.local.paths', [])
        if not paths:
            return None
        
        exclude_patterns = self.config.get('sources.local.exclude_patterns', [])
        scanner = LocalScanner(exclude_patterns=exclude_patterns)
        
        return scanner.scan(paths)
    
    def _scan_github(self) -> ScanResult:
        """Scan GitHub repositories.
        
        Returns:
            ScanResult or None if GitHub not configured
        """
        clone_path = self.config.get('sources.github.clone_path')
        repos = self.config.get('sources.github.repos', [])
        exclude_patterns = self.config.get('sources.local.exclude_patterns', [])
        
        scanner = GitHubScanner(
            clone_path=clone_path,
            exclude_patterns=exclude_patterns
        )
        
        return scanner.scan(repos)
    
    def _scan_gdrive(self) -> ScanResult:
        """Scan Google Drive.
        
        Returns:
            ScanResult or None if Google Drive not configured
        """
        credentials_path = self.config.get('sources.google_drive.credentials_path')
        folders = self.config.get('sources.google_drive.folders', [])
        exclude_patterns = self.config.get('sources.local.exclude_patterns', [])
        
        scanner = GoogleDriveScanner(
            credentials_path=credentials_path,
            exclude_patterns=exclude_patterns
        )
        
        return scanner.scan(folder_ids=folders)
    
    def get_all_files(self) -> List[FileMetadata]:
        """Get all files from all sources.
        
        Returns:
            List of all file metadata
        """
        all_files = []
        results = self.scan_all_sources()
        
        for source_type, result in results.items():
            all_files.extend(result.files)
        
        return all_files
