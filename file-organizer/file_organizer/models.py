"""Data models for file organization."""

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class OperationType(Enum):
    """Type of file operation."""
    COPY = "copy"
    MOVE = "move"


class ConflictResolution(Enum):
    """Strategy for handling file conflicts."""
    SKIP = "skip"
    RENAME = "rename"
    PROMPT = "prompt"
    KEEP_NEWEST = "keep_newest"
    KEEP_OLDEST = "keep_oldest"
    OVERWRITE = "overwrite"


@dataclass
class FileMetadata:
    """Metadata for a file to be organized."""
    
    # Source information
    source_path: Path
    source_type: str  # 'local', 'github', 'gdrive'
    
    # File properties
    filename: str
    extension: str
    size: int
    created_date: datetime
    modified_date: datetime
    
    # Organization hints
    project: Optional[str] = None
    category: Optional[str] = None
    github_repo: Optional[str] = None
    parent_folder: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def stem(self) -> str:
        """Get filename without extension."""
        return Path(self.filename).stem
    
    @classmethod
    def from_path(cls, path: Path, source_type: str = 'local', **kwargs) -> 'FileMetadata':
        """Create FileMetadata from a file path.
        
        Args:
            path: Path to file
            source_type: Type of source ('local', 'github', 'gdrive')
            **kwargs: Additional metadata
            
        Returns:
            FileMetadata instance
        """
        stat = path.stat()
        
        return cls(
            source_path=path,
            source_type=source_type,
            filename=path.name,
            extension=path.suffix.lower(),
            size=stat.st_size,
            created_date=datetime.fromtimestamp(stat.st_ctime),
            modified_date=datetime.fromtimestamp(stat.st_mtime),
            parent_folder=path.parent.name,
            **kwargs
        )


@dataclass
class OrganizationPlan:
    """Plan for organizing a single file."""
    
    file_metadata: FileMetadata
    destination_path: Path
    operation: OperationType
    conflict: bool = False
    conflict_resolution: Optional[ConflictResolution] = None
    skip: bool = False
    skip_reason: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of the plan."""
        op = "→" if self.operation == OperationType.COPY else "⇒"
        status = ""
        
        if self.skip:
            status = f" [SKIP: {self.skip_reason}]"
        elif self.conflict:
            status = f" [CONFLICT: {self.conflict_resolution.value if self.conflict_resolution else 'unresolved'}]"
        
        return f"{self.file_metadata.source_path} {op} {self.destination_path}{status}"


@dataclass
class Transaction:
    """Record of a file operation for undo capability."""
    
    timestamp: datetime
    operation: OperationType
    source_path: Path
    destination_path: Path
    success: bool
    error: Optional[str] = None
    backup_path: Optional[Path] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'operation': self.operation.value,
            'source_path': str(self.source_path),
            'destination_path': str(self.destination_path),
            'success': self.success,
            'error': self.error,
            'backup_path': str(self.backup_path) if self.backup_path else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """Create Transaction from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            operation=OperationType(data['operation']),
            source_path=Path(data['source_path']),
            destination_path=Path(data['destination_path']),
            success=data['success'],
            error=data.get('error'),
            backup_path=Path(data['backup_path']) if data.get('backup_path') else None
        )


@dataclass
class ScanResult:
    """Result of scanning files from a source."""
    
    source_type: str
    source_path: str
    files: list[FileMetadata]
    total_size: int
    scan_time: datetime
    errors: list[str] = field(default_factory=list)
    
    def __len__(self) -> int:
        """Number of files scanned."""
        return len(self.files)
