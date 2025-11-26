# File Organizer - Architecture Design

## Project Overview
A flexible, safe file organization tool that can reorganize files from multiple sources (GitHub repos, Google Drive, local filesystem) based on customizable schemas.

## Core Components

### 1. Configuration System
- **Format**: YAML-based configuration
- **Features**:
  - Define folder structure rules
  - Naming conventions (templates with variables)
  - File type categorization
  - Project detection rules
  - Exclusion patterns

### 2. File Scanner
- Multi-source support:
  - Local filesystem walker
  - GitHub repository scanner (via API/CLI)
  - Google Drive scanner (via API)
- Metadata extraction (date, type, size, project hints)

### 3. Organization Engine
- Rule-based file classification
- Path generation based on schema
- Conflict detection and resolution
- Dry-run mode (preview without changes)

### 4. Safety Layer
- Preview mode (show all planned changes)
- Backup creation before operations
- Transaction log (undo capability)
- Conflict resolution strategies:
  - Skip
  - Rename with suffix
  - Prompt user
  - Keep newest/oldest

### 5. Execution Engine
- Safe file operations (copy vs move)
- Progress tracking
- Error handling and rollback
- Operation logging

### 6. CLI Interface
- Commands:
  - `scan` - Scan sources and show file inventory
  - `preview` - Preview organization changes
  - `organize` - Execute organization
  - `undo` - Rollback last operation
  - `config` - Manage configuration

## Configuration Schema Example

```yaml
# Organization rules
organization:
  base_path: "/path/to/organized/files"
  
  # Folder structure template
  structure:
    - "{project}/{category}/{year}/{filename}"
  
  # Project detection rules
  projects:
    detect_from:
      - github_repo_name
      - folder_name
      - custom_patterns
    
    patterns:
      - name: "SONGFORGE_AI"
        keywords: ["songforge", "music", "ai"]
      - name: "EdenOS"
        keywords: ["edenos", "daemon", "eden"]
    
    default: "Uncategorized"
  
  # Category rules
  categories:
    code:
      extensions: [".py", ".js", ".java", ".cpp", ".h"]
    documents:
      extensions: [".pdf", ".docx", ".txt", ".md"]
    images:
      extensions: [".jpg", ".png", ".gif", ".svg"]
    audio:
      extensions: [".mp3", ".wav", ".flac", ".ogg"]
    video:
      extensions: [".mp4", ".avi", ".mkv", ".mov"]
    archives:
      extensions: [".zip", ".tar", ".gz", ".rar"]
    data:
      extensions: [".json", ".csv", ".xml", ".yaml"]
  
  # Naming convention
  naming:
    template: "{date}_{original_name}"
    date_format: "%Y%m%d"
    lowercase: false
    replace_spaces: "_"
    max_length: 255

# Safety settings
safety:
  mode: "copy"  # or "move"
  create_backup: true
  backup_path: "/path/to/backups"
  dry_run_default: true
  conflict_resolution: "rename"  # skip, rename, prompt, keep_newest
  
# Sources
sources:
  local:
    enabled: true
    paths:
      - "/path/to/downloads"
      - "/path/to/documents"
    exclude_patterns:
      - "node_modules"
      - ".git"
      - "__pycache__"
  
  github:
    enabled: true
    clone_path: "/tmp/github_repos"
    repos: []  # Empty = all accessible repos
    
  google_drive:
    enabled: false
    credentials_path: "~/.config/file-organizer/gdrive_credentials.json"
    folders: []  # Empty = root

# Logging
logging:
  level: "INFO"
  file: "~/.config/file-organizer/organizer.log"
  transaction_log: "~/.config/file-organizer/transactions.json"
```

## Technology Stack
- **Python 3.8+**
- **Libraries**:
  - `click` - CLI framework
  - `pyyaml` - Configuration parsing
  - `google-api-python-client` - Google Drive API
  - `PyGithub` or `gh` CLI - GitHub integration
  - `pathlib` - Path operations
  - `shutil` - File operations
  - `rich` - Beautiful terminal output

## Directory Structure
```
file-organizer/
├── file_organizer/
│   ├── __init__.py
│   ├── cli.py              # CLI interface
│   ├── config.py           # Configuration management
│   ├── scanner.py          # File scanning logic
│   ├── organizer.py        # Organization engine
│   ├── safety.py           # Safety and backup logic
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── local.py        # Local filesystem
│   │   ├── github.py       # GitHub integration
│   │   └── gdrive.py       # Google Drive integration
│   └── utils.py            # Utility functions
├── config/
│   └── default_config.yaml
├── tests/
│   └── ...
├── README.md
├── requirements.txt
├── setup.py
└── .gitignore
```
