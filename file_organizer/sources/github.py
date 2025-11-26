"""GitHub repository scanner."""

import subprocess
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from ..models import FileMetadata, ScanResult


class GitHubScanner:
    """Scans GitHub repositories for files."""
    
    def __init__(
        self, 
        clone_path: str,
        exclude_patterns: List[str] = None
    ):
        """Initialize GitHub scanner.
        
        Args:
            clone_path: Path where repos will be cloned
            exclude_patterns: List of patterns to exclude
        """
        self.clone_path = Path(clone_path).expanduser().resolve()
        self.clone_path.mkdir(parents=True, exist_ok=True)
        self.exclude_patterns = exclude_patterns or ['.git']
    
    def scan(self, repos: List[str] = None) -> ScanResult:
        """Scan GitHub repositories.
        
        Args:
            repos: List of repo names (e.g., ['owner/repo']). If None, scans all accessible repos.
            
        Returns:
            ScanResult with found files
        """
        files = []
        errors = []
        total_size = 0
        
        # Get list of repos to scan
        if repos is None or len(repos) == 0:
            repos = self._get_all_repos()
        
        for repo in repos:
            try:
                repo_files, repo_size = self._scan_repo(repo)
                files.extend(repo_files)
                total_size += repo_size
            except Exception as e:
                errors.append(f"Error scanning repo {repo}: {e}")
        
        return ScanResult(
            source_type='github',
            source_path=f"{len(repos)} repositories",
            files=files,
            total_size=total_size,
            scan_time=datetime.now(),
            errors=errors
        )
    
    def _get_all_repos(self) -> List[str]:
        """Get all accessible GitHub repositories.
        
        Returns:
            List of repository names
        """
        try:
            result = subprocess.run(
                ['gh', 'repo', 'list', '--limit', '1000', '--json', 'nameWithOwner'],
                capture_output=True,
                text=True,
                check=True
            )
            
            import json
            repos_data = json.loads(result.stdout)
            return [repo['nameWithOwner'] for repo in repos_data]
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to list GitHub repos: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse GitHub CLI output: {e}")
    
    def _scan_repo(self, repo: str) -> tuple[List[FileMetadata], int]:
        """Scan a single GitHub repository.
        
        Args:
            repo: Repository name (owner/repo)
            
        Returns:
            Tuple of (files, total_size)
        """
        # Clone or update repo
        repo_name = repo.split('/')[-1]
        repo_path = self.clone_path / repo_name
        
        if repo_path.exists():
            # Update existing repo
            try:
                subprocess.run(
                    ['git', 'pull'],
                    cwd=repo_path,
                    capture_output=True,
                    check=True
                )
            except subprocess.CalledProcessError:
                # If pull fails, remove and re-clone
                shutil.rmtree(repo_path)
                self._clone_repo(repo, repo_path)
        else:
            # Clone new repo
            self._clone_repo(repo, repo_path)
        
        # Scan files in repo
        files = []
        total_size = 0
        
        for item in repo_path.rglob('*'):
            # Skip excluded patterns
            if self._should_exclude(item, repo_path):
                continue
            
            if not item.is_file():
                continue
            
            try:
                file_meta = FileMetadata.from_path(
                    item,
                    source_type='github',
                    github_repo=repo
                )
                files.append(file_meta)
                total_size += file_meta.size
            except Exception:
                continue
        
        return files, total_size
    
    def _clone_repo(self, repo: str, dest_path: Path) -> None:
        """Clone a GitHub repository.
        
        Args:
            repo: Repository name (owner/repo)
            dest_path: Destination path for clone
        """
        try:
            subprocess.run(
                ['gh', 'repo', 'clone', repo, str(dest_path)],
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to clone {repo}: {e.stderr.decode()}")
    
    def _should_exclude(self, path: Path, repo_root: Path) -> bool:
        """Check if path should be excluded.
        
        Args:
            path: Path to check
            repo_root: Root of the repository
            
        Returns:
            True if should be excluded
        """
        import fnmatch
        
        # Get relative path from repo root
        try:
            rel_path = path.relative_to(repo_root)
        except ValueError:
            return False
        
        # Check each part of the path
        for part in rel_path.parts:
            for pattern in self.exclude_patterns:
                if fnmatch.fnmatch(part, pattern):
                    return True
        
        return False
    
    def cleanup(self) -> None:
        """Clean up cloned repositories."""
        if self.clone_path.exists():
            shutil.rmtree(self.clone_path)
