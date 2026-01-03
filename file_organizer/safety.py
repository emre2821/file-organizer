"""Safety features including transaction logging and undo."""

import json
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .models import Transaction, OperationType
from .config import Config


class TransactionLogger:
    """Logs file operations for undo capability."""
    
    def __init__(self, config: Config):
        """Initialize transaction logger.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.log_path = Path(config.get('logging.transaction_log'))
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize log file if it doesn't exist
        if not self.log_path.exists():
            self._save_transactions([])
    
    def log_transactions(self, transactions: List[Transaction]) -> None:
        """Log a batch of transactions.
        
        Args:
            transactions: List of transactions to log
        """
        existing = self._load_transactions()
        existing.extend([t.to_dict() for t in transactions])
        self._save_transactions(existing)
    
    def get_recent_transactions(self, limit: int = 100) -> List[Transaction]:
        """Get recent transactions.
        
        Args:
            limit: Maximum number of transactions to return
            
        Returns:
            List of recent transactions
        """
        all_transactions = self._load_transactions()
        recent = all_transactions[-limit:] if len(all_transactions) > limit else all_transactions
        return [Transaction.from_dict(t) for t in reversed(recent)]
    
    def get_last_batch(self) -> List[Transaction]:
        """Get the most recent batch of transactions.
        
        Returns:
            List of transactions from the last batch
        """
        all_transactions = self._load_transactions()
        if not all_transactions:
            return []
        
        # Find the last batch (transactions with same timestamp minute)
        last_transaction = Transaction.from_dict(all_transactions[-1])
        last_timestamp = last_transaction.timestamp
        
        batch = []
        for t_dict in reversed(all_transactions):
            t = Transaction.from_dict(t_dict)
            # Group transactions within 1 minute as same batch
            if abs((t.timestamp - last_timestamp).total_seconds()) < 60:
                batch.insert(0, t)
            else:
                break
        
        return batch
    
    def undo_last_batch(self) -> tuple[int, int]:
        """Undo the last batch of transactions.
        
        Returns:
            Tuple of (successful_undos, failed_undos)
        """
        batch = self.get_last_batch()
        if not batch:
            return 0, 0
        
        successful = 0
        failed = 0
        
        for transaction in reversed(batch):
            if not transaction.success:
                continue
            
            try:
                if transaction.operation == OperationType.COPY:
                    # For copy operations, just delete the destination
                    if transaction.destination_path.exists():
                        transaction.destination_path.unlink()
                        successful += 1
                    
                elif transaction.operation == OperationType.MOVE:
                    # For move operations, move back from destination to source
                    if transaction.destination_path.exists():
                        # Restore from backup if available
                        if transaction.backup_path and transaction.backup_path.exists():
                            shutil.copy2(
                                transaction.backup_path,
                                transaction.source_path
                            )
                        else:
                            shutil.move(
                                str(transaction.destination_path),
                                str(transaction.source_path)
                            )
                        successful += 1
                
            except Exception as e:
                failed += 1
                print(f"Failed to undo {transaction.source_path}: {e}")
        
        # Remove undone transactions from log
        all_transactions = self._load_transactions()
        batch_size = len(batch)
        remaining = all_transactions[:-batch_size] if batch_size > 0 else all_transactions
        self._save_transactions(remaining)
        
        return successful, failed
    
    def clear_old_transactions(self, days: int = 30) -> int:
        """Clear transactions older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of transactions removed
        """
        all_transactions = self._load_transactions()
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        filtered = [
            t for t in all_transactions
            if datetime.fromisoformat(t['timestamp']).timestamp() > cutoff
        ]
        
        removed = len(all_transactions) - len(filtered)
        self._save_transactions(filtered)
        
        return removed
    
    def _load_transactions(self) -> List[dict]:
        """Load all transactions from log file.
        
        Returns:
            List of transaction dictionaries
        """
        try:
            with open(self.log_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_transactions(self, transactions: List[dict]) -> None:
        """Save transactions to log file.
        
        Args:
            transactions: List of transaction dictionaries
        """
        with open(self.log_path, 'w') as f:
            json.dump(transactions, f, indent=2)


class SafetyValidator:
    """Validates operations before execution."""
    
    @staticmethod
    def validate_destination_path(path: Path) -> tuple[bool, Optional[str]]:
        """Validate that destination path is safe.
        
        Args:
            path: Destination path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for system directories
        system_dirs = ['/bin', '/sbin', '/usr', '/etc', '/var', '/sys', '/proc', '/dev']
        path_str = str(path.absolute())
        
        for sys_dir in system_dirs:
            if path_str.startswith(sys_dir):
                return False, f"Cannot organize files into system directory: {sys_dir}"
        
        # Check path length
        if len(path_str) > 4096:
            return False, "Path too long (max 4096 characters)"
        
        # Check for invalid characters (Windows compatibility)
        invalid_chars = '<>:"|?*'
        if any(char in path.name for char in invalid_chars):
            return False, f"Filename contains invalid characters: {invalid_chars}"
        
        return True, None
    
    @staticmethod
    def estimate_disk_space(plans: List) -> int:
        """Estimate disk space needed for operations.
        
        Args:
            plans: List of organization plans
            
        Returns:
            Estimated bytes needed
        """
        total_size = 0
        
        for plan in plans:
            if plan.skip:
                continue
            
            # For copy operations, we need the full file size
            if plan.operation == OperationType.COPY:
                total_size += plan.file_metadata.size
            
            # For backups
            total_size += plan.file_metadata.size
        
        return total_size
    
    @staticmethod
    def check_available_space(path: Path, required_bytes: int) -> tuple[bool, int]:
        """Check if enough disk space is available.
        
        Args:
            path: Path to check space for
            required_bytes: Required bytes
            
        Returns:
            Tuple of (has_space, available_bytes)
        """
        stat = shutil.disk_usage(path)
        return stat.free >= required_bytes, stat.free
