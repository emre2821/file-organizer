"""Core file organization engine."""

import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from .models import (
    FileMetadata, OrganizationPlan, OperationType, 
    ConflictResolution, Transaction
)
from .config import Config


class FileOrganizer:
    """Organizes files based on configuration rules."""
    
    def __init__(self, config: Config):
        """Initialize organizer.
        
        Args:
            config: Configuration instance
        """
        self.config = config
    
    def create_organization_plan(
        self, 
        files: List[FileMetadata]
    ) -> List[OrganizationPlan]:
        """Create organization plan for files.
        
        Args:
            files: List of file metadata
            
        Returns:
            List of organization plans
        """
        plans = []
        
        for file_meta in files:
            # Detect project if not already set
            if not file_meta.project:
                file_meta.project = self._detect_project(file_meta)
            
            # Detect category if not already set
            if not file_meta.category:
                file_meta.category = self.config.get_category_for_extension(
                    file_meta.extension
                )
            
            # Generate destination path
            dest_path = self._generate_destination_path(file_meta)
            
            # Determine operation type
            operation = OperationType(self.config.get('safety.mode', 'copy'))
            
            # Create plan
            plan = OrganizationPlan(
                file_metadata=file_meta,
                destination_path=dest_path,
                operation=operation
            )
            
            # Check for conflicts
            if dest_path.exists():
                plan.conflict = True
                plan.conflict_resolution = ConflictResolution(
                    self.config.get('safety.conflict_resolution', 'rename')
                )
                
                # Resolve conflict based on strategy
                plan = self._resolve_conflict(plan)
            
            plans.append(plan)
        
        return plans
    
    def _detect_project(self, file_meta: FileMetadata) -> str:
        """Detect project for a file.
        
        Args:
            file_meta: File metadata
            
        Returns:
            Project name
        """
        # Check GitHub repo name first
        if file_meta.github_repo:
            return self._clean_project_name(file_meta.github_repo)
        
        # Check custom patterns
        patterns = self.config.get_project_patterns()
        
        # Search in filename and parent folder
        search_text = f"{file_meta.filename} {file_meta.parent_folder or ''}".lower()
        
        for pattern in patterns:
            keywords = pattern.get('keywords', [])
            if any(keyword.lower() in search_text for keyword in keywords):
                return pattern['name']
        
        # Check parent folder name
        if file_meta.parent_folder:
            return self._clean_project_name(file_meta.parent_folder)
        
        # Default project
        return self.config.get('organization.projects.default', 'Uncategorized')
    
    def _clean_project_name(self, name: str) -> str:
        """Clean project name for use in paths.
        
        Args:
            name: Raw project name
            
        Returns:
            Cleaned project name
        """
        # Remove special characters, keep alphanumeric, spaces, hyphens, underscores
        cleaned = re.sub(r'[^\w\s-]', '', name)
        # Replace multiple spaces/hyphens with single
        cleaned = re.sub(r'[-\s]+', '-', cleaned)
        return cleaned.strip('-_')
    
    def _generate_destination_path(self, file_meta: FileMetadata) -> Path:
        """Generate destination path for a file.
        
        Args:
            file_meta: File metadata
            
        Returns:
            Destination path
        """
        base_path = Path(self.config.get('organization.base_path'))
        structure_template = self.config.get('organization.structure', ['{filename}'])[0]
        
        # Prepare template variables
        variables = {
            'project': file_meta.project or 'Uncategorized',
            'category': file_meta.category or 'other',
            'year': str(file_meta.modified_date.year),
            'month': f"{file_meta.modified_date.month:02d}",
            'day': f"{file_meta.modified_date.day:02d}",
            'filename': self._apply_naming_convention(file_meta),
            'original_name': file_meta.filename,
            'extension': file_meta.extension.lstrip('.'),
        }
        
        # Replace template variables
        path_str = structure_template
        for key, value in variables.items():
            path_str = path_str.replace(f'{{{key}}}', value)
        
        return base_path / path_str
    
    def _apply_naming_convention(self, file_meta: FileMetadata) -> str:
        """Apply naming convention to filename.
        
        Args:
            file_meta: File metadata
            
        Returns:
            Formatted filename
        """
        naming_config = self.config.get('organization.naming', {})
        template = naming_config.get('template', '{original_name}')
        
        # Prepare variables
        date_format = naming_config.get('date_format', '%Y%m%d')
        variables = {
            'original_name': file_meta.stem,
            'date': file_meta.modified_date.strftime(date_format),
            'year': str(file_meta.modified_date.year),
            'month': f"{file_meta.modified_date.month:02d}",
            'day': f"{file_meta.modified_date.day:02d}",
            'project': file_meta.project or 'unknown',
            'category': file_meta.category or 'other',
        }
        
        # Apply template
        filename = template
        for key, value in variables.items():
            filename = filename.replace(f'{{{key}}}', value)
        
        # Apply transformations
        if naming_config.get('lowercase', False):
            filename = filename.lower()
        
        replace_spaces = naming_config.get('replace_spaces')
        if replace_spaces:
            filename = filename.replace(' ', replace_spaces)
        
        # Add extension
        filename = f"{filename}{file_meta.extension}"
        
        # Enforce max length
        max_length = naming_config.get('max_length', 255)
        if len(filename) > max_length:
            # Truncate stem, keep extension
            stem_max = max_length - len(file_meta.extension)
            filename = filename[:stem_max] + file_meta.extension
        
        return filename
    
    def _resolve_conflict(self, plan: OrganizationPlan) -> OrganizationPlan:
        """Resolve file conflict.
        
        Args:
            plan: Organization plan with conflict
            
        Returns:
            Updated plan
        """
        resolution = plan.conflict_resolution
        
        if resolution == ConflictResolution.SKIP:
            plan.skip = True
            plan.skip_reason = "File already exists"
        
        elif resolution == ConflictResolution.RENAME:
            # Add numeric suffix
            counter = 1
            base_path = plan.destination_path.parent
            stem = plan.destination_path.stem
            extension = plan.destination_path.suffix
            
            while True:
                new_path = base_path / f"{stem}_{counter}{extension}"
                if not new_path.exists():
                    plan.destination_path = new_path
                    plan.conflict = False
                    break
                counter += 1
        
        elif resolution == ConflictResolution.KEEP_NEWEST:
            # Compare modification times
            existing_mtime = plan.destination_path.stat().st_mtime
            new_mtime = plan.file_metadata.modified_date.timestamp()
            
            if new_mtime <= existing_mtime:
                plan.skip = True
                plan.skip_reason = "Existing file is newer"
        
        elif resolution == ConflictResolution.KEEP_OLDEST:
            # Compare modification times
            existing_mtime = plan.destination_path.stat().st_mtime
            new_mtime = plan.file_metadata.modified_date.timestamp()
            
            if new_mtime >= existing_mtime:
                plan.skip = True
                plan.skip_reason = "Existing file is older"
        
        elif resolution == ConflictResolution.OVERWRITE:
            # Will overwrite, no changes needed
            plan.conflict = False
        
        # PROMPT will be handled by CLI
        
        return plan
    
    def execute_plan(
        self, 
        plans: List[OrganizationPlan],
        dry_run: bool = False
    ) -> List[Transaction]:
        """Execute organization plans.
        
        Args:
            plans: List of organization plans
            dry_run: If True, don't actually perform operations
            
        Returns:
            List of transaction records
        """
        transactions = []
        
        for plan in plans:
            if plan.skip:
                continue
            
            transaction = Transaction(
                timestamp=datetime.now(),
                operation=plan.operation,
                source_path=plan.file_metadata.source_path,
                destination_path=plan.destination_path,
                success=False
            )
            
            if dry_run:
                transaction.success = True
                transactions.append(transaction)
                continue
            
            try:
                # Create destination directory
                plan.destination_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Create backup if enabled
                if self.config.get('safety.create_backup', False):
                    backup_path = self._create_backup(plan.file_metadata.source_path)
                    transaction.backup_path = backup_path
                
                # Perform operation
                if plan.operation == OperationType.COPY:
                    shutil.copy2(
                        plan.file_metadata.source_path, 
                        plan.destination_path
                    )
                else:  # MOVE
                    shutil.move(
                        str(plan.file_metadata.source_path), 
                        str(plan.destination_path)
                    )
                
                # Preserve timestamps if configured
                if self.config.get('safety.preserve_timestamps', True):
                    stat = plan.file_metadata.source_path.stat()
                    shutil.copystat(
                        plan.file_metadata.source_path,
                        plan.destination_path
                    )
                
                transaction.success = True
                
            except Exception as e:
                transaction.error = str(e)
            
            transactions.append(transaction)
        
        return transactions
    
    def _create_backup(self, source_path: Path) -> Path:
        """Create backup of a file.
        
        Args:
            source_path: Path to file to backup
            
        Returns:
            Path to backup file
        """
        backup_dir = Path(self.config.get('safety.backup_path'))
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(source_path, backup_path)
        return backup_path
