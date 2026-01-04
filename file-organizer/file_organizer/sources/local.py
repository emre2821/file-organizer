"""Local filesystem scanner."""

import fnmatch
from pathlib import Path
from typing import List, Set
from datetime import datetime
from ..models import FileMetadata, ScanResult


class LocalScanner:
    """Scans local filesystem for files."""
    
    def __init__(self, exclude_patterns: List[str] = None):
        """Initialize local scanner.
        
        Args:
            exclude_patterns: List of glob patterns to exclude
        """
        self.exclude_patterns = exclude_patterns or []
    
    def scan(self, paths: List[str]) -> ScanResult:
        """Scan local paths for files.
        
        Args:
            paths: List of paths to scan
            
        Returns:
            ScanResult with found files
        """
        files = []
        errors = []
        total_size = 0
        
        for path_str in paths:
            path = Path(path_str).expanduser().resolve()
            
            if not path.exists():
                errors.append(f"Path does not exist: {path}")
                continue
            
            if path.is_file():
                # Single file
                try:
                    file_meta = FileMetadata.from_path(path, source_type='local')
                    files.append(file_meta)
                    total_size += file_meta.size
                except Exception as e:
                    errors.append(f"Error scanning {path}: {e}")
            
            elif path.is_dir():
                # Directory - walk recursively
                try:
                    dir_files, dir_size = self._scan_directory(path)
                    files.extend(dir_files)
                    total_size += dir_size
                except Exception as e:
                    errors.append(f"Error scanning directory {path}: {e}")
        
        return ScanResult(
            source_type='local',
            source_path=', '.join(paths),
            files=files,
            total_size=total_size,
            scan_time=datetime.now(),
            errors=errors
        )
    
    def _scan_directory(self, directory: Path) -> tuple[List[FileMetadata], int]:
        """Recursively scan a directory.
        
        Args:
            directory: Directory to scan
            
        Returns:
            Tuple of (files, total_size)
        """
        files = []
        total_size = 0
        
        for item in directory.rglob('*'):
            # Skip if matches exclude pattern
            if self._should_exclude(item):
                continue
            
            # Only process files
            if not item.is_file():
                continue
            
            try:
                file_meta = FileMetadata.from_path(item, source_type='local')
                files.append(file_meta)
                total_size += file_meta.size
            except Exception as e:
                # Skip files we can't read
                continue
        
        return files, total_size
    
    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded.
        
        Args:
            path: Path to check
            
        Returns:
            True if should be excluded
        """
        path_str = str(path)
        
        for pattern in self.exclude_patterns:
            # Check if any part of the path matches the pattern
            if fnmatch.fnmatch(path.name, pattern):
                return True
            
            # Check if pattern is in any parent directory
            if pattern in path_str:
                return True
        
        return False
