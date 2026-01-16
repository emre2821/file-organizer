"""Google Drive scanner."""

import io
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import pickle
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False

from ..models import FileMetadata, ScanResult


class GoogleDriveScanner:
    """Scans Google Drive for files."""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(
        self,
        credentials_path: str,
        download_path: str = '/tmp/gdrive-files',
        exclude_patterns: List[str] = None,
        export_formats: Optional[Dict[str, str]] = None
    ):
        """Initialize Google Drive scanner.
        
        Args:
            credentials_path: Path to OAuth credentials JSON
            download_path: Path where files will be downloaded
            exclude_patterns: List of patterns to exclude
            export_formats: Mapping of Google Workspace MIME types to export MIME types
        """
        if not GDRIVE_AVAILABLE:
            raise ImportError(
                "Google Drive support requires: pip install google-api-python-client "
                "google-auth-httplib2 google-auth-oauthlib"
            )
        
        self.credentials_path = Path(credentials_path).expanduser()
        self.download_path = Path(download_path).expanduser().resolve()
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.exclude_patterns = exclude_patterns or []
        self.export_formats = export_formats or {}
        self.service = None
    
    def authenticate(self) -> None:
        """Authenticate with Google Drive API."""
        creds = None
        token_path = self.credentials_path.parent / 'token.pickle'
        
        # Load existing credentials
        if token_path.exists():
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}\n"
                        "Please download OAuth credentials from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path),
                    self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def scan(
        self,
        folder_ids: List[str] = None,
        download: bool = False
    ) -> ScanResult:
        """Scan Google Drive for files.
        
        Args:
            folder_ids: List of folder IDs to scan. If None, scans root.
            download: If True, download files to local path
            
        Returns:
            ScanResult with found files
        """
        if not self.service:
            self.authenticate()
        
        files = []
        errors = []
        total_size = 0
        
        # Get folders to scan
        if folder_ids is None or len(folder_ids) == 0:
            folder_ids = ['root']
        
        for folder_id in folder_ids:
            try:
                folder_files, folder_size = self._scan_folder(folder_id, download)
                files.extend(folder_files)
                total_size += folder_size
            except Exception as e:
                errors.append(f"Error scanning folder {folder_id}: {e}")
        
        return ScanResult(
            source_type='gdrive',
            source_path=f"{len(folder_ids)} folders",
            files=files,
            total_size=total_size,
            scan_time=datetime.now(),
            errors=errors
        )
    
    def _scan_folder(
        self,
        folder_id: str,
        download: bool = False
    ) -> tuple[List[FileMetadata], int]:
        """Recursively scan a Google Drive folder.
        
        Args:
            folder_id: Google Drive folder ID
            download: If True, download files
            
        Returns:
            Tuple of (files, total_size)
        """
        files = []
        total_size = 0
        
        # Query for all items in folder
        query = f"'{folder_id}' in parents and trashed=false"
        
        page_token = None
        while True:
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents)",
                pageToken=page_token
            ).execute()
            
            items = results.get('files', [])
            
            for item in items:
                # Skip if matches exclude pattern
                if self._should_exclude(item['name']):
                    continue
                
                # If it's a folder, recurse
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    folder_files, folder_size = self._scan_folder(item['id'], download)
                    files.extend(folder_files)
                    total_size += folder_size
                else:
                    # It's a file
                    try:
                        file_meta = self._create_file_metadata(item, download)
                        if file_meta:
                            files.append(file_meta)
                            total_size += file_meta.size
                    except Exception as e:
                        continue
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        
        return files, total_size
    
    def _create_file_metadata(
        self,
        item: Dict[str, Any],
        download: bool = False
    ) -> Optional[FileMetadata]:
        """Create FileMetadata from Google Drive file item.
        
        Args:
            item: Google Drive file item
            download: If True, download the file
            
        Returns:
            FileMetadata or None if file should be skipped
        """
        # Handle Google Workspace files (Docs, Sheets, etc.)
        if item['mimeType'].startswith('application/vnd.google-apps.'):
            if not download:
                return None

            export_mime_type = self._get_export_mime_type(item['mimeType'])
            export_path = self._export_google_app(item, export_mime_type)
            size = export_path.stat().st_size

            created = datetime.fromisoformat(item['createdTime'].replace('Z', '+00:00'))
            modified = datetime.fromisoformat(item['modifiedTime'].replace('Z', '+00:00'))
            extension = export_path.suffix.lower()

            return FileMetadata(
                source_path=export_path,
                source_type='gdrive',
                filename=export_path.name,
                extension=extension,
                size=size,
                created_date=created,
                modified_date=modified,
                metadata={
                    'gdrive_id': item['id'],
                    'mime_type': item['mimeType'],
                    'original_mime_type': item['mimeType'],
                    'export_mime_type': export_mime_type,
                    'original_filename': item['name']
                }
            )
        
        # Get file size
        size = int(item.get('size', 0))
        
        # Parse dates
        created = datetime.fromisoformat(item['createdTime'].replace('Z', '+00:00'))
        modified = datetime.fromisoformat(item['modifiedTime'].replace('Z', '+00:00'))
        
        # Determine local path
        if download:
            local_path = self._download_file(item['id'], item['name'])
        else:
            # Create virtual path
            local_path = self.download_path / item['name']
        
        # Get extension
        extension = Path(item['name']).suffix.lower()
        
        return FileMetadata(
            source_path=local_path,
            source_type='gdrive',
            filename=item['name'],
            extension=extension,
            size=size,
            created_date=created,
            modified_date=modified,
            metadata={'gdrive_id': item['id'], 'mime_type': item['mimeType']}
        )

    def _get_export_mime_type(self, original_mime_type: str) -> str:
        """Determine export MIME type for a Google Workspace file."""
        if original_mime_type in self.export_formats:
            return self.export_formats[original_mime_type]
        return self.export_formats.get('default', 'application/pdf')

    def _extension_for_mime_type(self, mime_type: str) -> str:
        """Return file extension for a MIME type."""
        known_extensions = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            'application/vnd.oasis.opendocument.text': '.odt',
            'application/vnd.oasis.opendocument.spreadsheet': '.ods',
            'application/vnd.oasis.opendocument.presentation': '.odp',
            'text/plain': '.txt',
            'text/csv': '.csv',
            'image/png': '.png',
            'image/jpeg': '.jpg'
        }
        if mime_type in known_extensions:
            return known_extensions[mime_type]
        extension = mimetypes.guess_extension(mime_type) or ''
        return extension

    def _export_google_app(self, item: Dict[str, Any], export_mime_type: str) -> Path:
        """Export a Google Workspace file to the specified MIME type."""
        extension = self._extension_for_mime_type(export_mime_type)
        filename = item['name']
        if extension and not filename.lower().endswith(extension):
            filename = f"{filename}{extension}"

        request = self.service.files().export(fileId=item['id'], mimeType=export_mime_type)

        file_path = self.download_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with io.FileIO(str(file_path), 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

        return file_path
    
    def _download_file(self, file_id: str, filename: str) -> Path:
        """Download a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            filename: Filename
            
        Returns:
            Path to downloaded file
        """
        request = self.service.files().get_media(fileId=file_id)
        
        file_path = self.download_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with io.FileIO(str(file_path), 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        
        return file_path
    
    def _should_exclude(self, filename: str) -> bool:
        """Check if file should be excluded.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if should be excluded
        """
        import fnmatch
        
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        
        return False
