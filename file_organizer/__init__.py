"""File Organizer - Flexible file organization tool."""

__version__ = '1.0.0'
__author__ = 'Emre'
__description__ = 'Organize files from multiple sources with customizable schemas'

from .config import Config
from .scanner import UnifiedScanner
from .organizer import FileOrganizer
from .safety import TransactionLogger, SafetyValidator
from .models import FileMetadata, OrganizationPlan, ScanResult

__all__ = [
    'Config',
    'UnifiedScanner',
    'FileOrganizer',
    'TransactionLogger',
    'SafetyValidator',
    'FileMetadata',
    'OrganizationPlan',
    'ScanResult',
]
