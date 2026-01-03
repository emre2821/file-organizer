"""Configuration management for file organizer."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional


class Config:
    """Manages configuration loading and access."""
    
    DEFAULT_CONFIG_PATH = Path.home() / ".config" / "file-organizer" / "config.yaml"
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """Load configuration from file."""
        if not self.config_path.exists():
            self._create_default_config()
            return

        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # If the config file exists but is empty/invalid, recreate defaults
        if not isinstance(config_data, dict):
            self._create_default_config()
            return

        self.config = config_data
    
    def save(self) -> None:
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        default_config = {
            'organization': {
                'base_path': str(Path.home() / 'OrganizedFiles'),
                'structure': ['{project}/{category}/{year}/{filename}'],
                'projects': {
                    'detect_from': ['github_repo_name', 'folder_name', 'custom_patterns'],
                    'patterns': [],
                    'default': 'Uncategorized'
                },
                'categories': {
                    'code': {
                        'extensions': ['.py', '.js', '.java', '.cpp', '.h', '.c', '.cs', '.go', 
                                     '.rs', '.rb', '.php', '.swift', '.kt', '.ts', '.jsx', '.tsx']
                    },
                    'documents': {
                        'extensions': ['.pdf', '.docx', '.doc', '.txt', '.md', '.rtf', '.odt', 
                                     '.tex', '.pages']
                    },
                    'images': {
                        'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.bmp', '.webp', 
                                     '.ico', '.tiff', '.psd', '.ai']
                    },
                    'audio': {
                        'extensions': ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma']
                    },
                    'video': {
                        'extensions': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', 
                                     '.m4v', '.mpeg']
                    },
                    'archives': {
                        'extensions': ['.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.xz']
                    },
                    'data': {
                        'extensions': ['.json', '.csv', '.xml', '.yaml', '.yml', '.sql', '.db', 
                                     '.sqlite']
                    },
                    'spreadsheets': {
                        'extensions': ['.xlsx', '.xls', '.ods', '.numbers']
                    },
                    'presentations': {
                        'extensions': ['.pptx', '.ppt', '.odp', '.key']
                    }
                },
                'naming': {
                    'template': '{original_name}',
                    'date_format': '%Y%m%d',
                    'lowercase': False,
                    'replace_spaces': '_',
                    'max_length': 255
                }
            },
            'safety': {
                'mode': 'copy',
                'create_backup': True,
                'backup_path': str(Path.home() / '.config' / 'file-organizer' / 'backups'),
                'dry_run_default': True,
                'conflict_resolution': 'rename',
                'preserve_timestamps': True
            },
            'sources': {
                'local': {
                    'enabled': True,
                    'paths': [],
                    'exclude_patterns': [
                        'node_modules', '.git', '__pycache__', '.venv', 'venv',
                        '.DS_Store', 'Thumbs.db', '.idea', '.vscode'
                    ]
                },
                'github': {
                    'enabled': False,
                    'clone_path': '/tmp/file-organizer-github',
                    'repos': []
                },
                'google_drive': {
                    'enabled': False,
                    'credentials_path': str(Path.home() / '.config' / 'file-organizer' / 'gdrive_credentials.json'),
                    'folders': []
                }
            },
            'logging': {
                'level': 'INFO',
                'file': str(Path.home() / '.config' / 'file-organizer' / 'organizer.log'),
                'transaction_log': str(Path.home() / '.config' / 'file-organizer' / 'transactions.json')
            }
        }
        
        self.config = default_config
        self.save()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to config value (e.g., 'safety.mode')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to config value
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def get_category_for_extension(self, extension: str) -> str:
        """Get category for file extension.
        
        Args:
            extension: File extension (with or without dot)
            
        Returns:
            Category name or 'other'
        """
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        extension = extension.lower()
        categories = self.get('organization.categories', {})
        
        for category, config in categories.items():
            if extension in config.get('extensions', []):
                return category
        
        return 'other'
    
    def get_project_patterns(self) -> List[Dict[str, Any]]:
        """Get project detection patterns.
        
        Returns:
            List of project pattern dictionaries
        """
        return self.get('organization.projects.patterns', [])
    
    def add_project_pattern(self, name: str, keywords: List[str]) -> None:
        """Add a new project detection pattern.
        
        Args:
            name: Project name
            keywords: List of keywords to match
        """
        patterns = self.get_project_patterns()
        patterns.append({'name': name, 'keywords': keywords})
        self.set('organization.projects.patterns', patterns)
        self.save()
