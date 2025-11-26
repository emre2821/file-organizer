# File Organizer

A flexible, safe file organization tool that can reorganize files from multiple sources (GitHub repos, Google Drive, local filesystem) based on customizable schemas.

## Features

- **Multi-Source Support**: Organize files from local filesystem, GitHub repositories, and Google Drive
- **Customizable Schema**: Define your own folder structure and naming conventions via YAML config
- **Safety First**: 
  - Dry-run mode by default
  - Backup creation before operations
  - Transaction logging with undo capability
  - Conflict resolution strategies
- **Smart Detection**: Automatically detect projects and categorize files
- **Rich CLI**: Beautiful terminal interface with progress tracking
- **Flexible**: Copy or move files, preserve timestamps, handle duplicates

## Installation

```bash
# Clone the repository
git clone https://github.com/emre2821/file-organizer.git
cd file-organizer

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Quick Start

1. **Initialize configuration**:
```bash
file-organizer init-config
```

This creates a config file at `~/.config/file-organizer/config.yaml`

2. **Edit configuration** to add your source paths:
```bash
nano ~/.config/file-organizer/config.yaml
```

Add your local paths:
```yaml
sources:
  local:
    enabled: true
    paths:
      - "/path/to/your/downloads"
      - "/path/to/your/documents"
```

3. **Scan your files**:
```bash
file-organizer scan
```

4. **Preview organization**:
```bash
file-organizer preview
```

5. **Organize files** (dry-run by default):
```bash
file-organizer organize
```

6. **Actually execute** (when you're ready):
```bash
file-organizer organize --execute
```

## Configuration

The configuration file uses YAML format and allows you to customize every aspect of file organization.

### Folder Structure

Define your folder structure using template variables:

```yaml
organization:
  base_path: "/path/to/organized/files"
  structure:
    - "{project}/{category}/{year}/{filename}"
```

Available variables:
- `{project}` - Detected project name
- `{category}` - File category (code, documents, images, etc.)
- `{year}`, `{month}`, `{day}` - Date components
- `{filename}` - Processed filename
- `{original_name}` - Original filename
- `{extension}` - File extension

### Project Detection

Automatically detect projects based on patterns:

```yaml
organization:
  projects:
    patterns:
      - name: "SONGFORGE_AI"
        keywords: ["songforge", "music", "ai"]
      - name: "EdenOS"
        keywords: ["edenos", "daemon", "eden"]
    default: "Uncategorized"
```

### File Categories

Files are automatically categorized by extension:

- **code**: `.py`, `.js`, `.java`, `.cpp`, etc.
- **documents**: `.pdf`, `.docx`, `.txt`, `.md`, etc.
- **images**: `.jpg`, `.png`, `.gif`, `.svg`, etc.
- **audio**: `.mp3`, `.wav`, `.flac`, etc.
- **video**: `.mp4`, `.avi`, `.mkv`, etc.
- **archives**: `.zip`, `.tar`, `.gz`, etc.
- **data**: `.json`, `.csv`, `.xml`, etc.

You can customize categories in the config file.

### Naming Convention

Customize how files are named:

```yaml
organization:
  naming:
    template: "{date}_{original_name}"
    date_format: "%Y%m%d"
    lowercase: false
    replace_spaces: "_"
    max_length: 255
```

### Safety Settings

```yaml
safety:
  mode: "copy"  # or "move"
  create_backup: true
  backup_path: "/path/to/backups"
  dry_run_default: true
  conflict_resolution: "rename"  # skip, rename, prompt, keep_newest, keep_oldest, overwrite
  preserve_timestamps: true
```

### Sources

#### Local Filesystem

```yaml
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
```

#### GitHub

```yaml
sources:
  github:
    enabled: true
    clone_path: "/tmp/file-organizer-github"
    repos: []  # Empty = all accessible repos, or specify: ["owner/repo1", "owner/repo2"]
```

**Note**: GitHub CLI (`gh`) must be installed and authenticated.

#### Google Drive

```yaml
sources:
  google_drive:
    enabled: true
    credentials_path: "~/.config/file-organizer/gdrive_credentials.json"
    folders: []  # Empty = root, or specify folder IDs
```

**Setup Google Drive**:
1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable Google Drive API
3. Create OAuth 2.0 credentials
4. Download credentials JSON and save to the path specified in config
5. First run will open browser for authentication

## Usage

### Commands

#### `scan`
Scan all configured sources and show file inventory.

```bash
file-organizer scan
file-organizer scan --config /path/to/config.yaml
```

#### `preview`
Preview organization changes without executing them.

```bash
file-organizer preview
file-organizer preview --limit 100
```

#### `organize`
Execute file organization.

```bash
file-organizer organize              # Dry-run (safe, no changes)
file-organizer organize --execute    # Actually organize files
```

#### `undo`
Undo the last organization operation.

```bash
file-organizer undo
```

#### `history`
Show recent organization operations.

```bash
file-organizer history
file-organizer history --limit 50
```

#### `init-config`
Initialize a new configuration file.

```bash
file-organizer init-config
file-organizer init-config --config /path/to/config.yaml
```

#### `show-config`
Show current configuration.

```bash
file-organizer show-config
```

## Examples

### Example 1: Organize Downloads by Type and Date

```yaml
organization:
  base_path: "~/OrganizedFiles"
  structure:
    - "{category}/{year}-{month}/{filename}"
  naming:
    template: "{date}_{original_name}"
    date_format: "%Y%m%d"

sources:
  local:
    enabled: true
    paths:
      - "~/Downloads"
```

Result:
```
OrganizedFiles/
├── documents/
│   └── 2025-11/
│       └── 20251125_report.pdf
├── images/
│   └── 2025-11/
│       └── 20251125_screenshot.png
└── code/
    └── 2025-11/
        └── 20251125_script.py
```

### Example 2: Organize by Project

```yaml
organization:
  base_path: "~/Projects"
  structure:
    - "{project}/{category}/{filename}"
  projects:
    patterns:
      - name: "WebApp"
        keywords: ["webapp", "frontend", "backend"]
      - name: "DataScience"
        keywords: ["ml", "data", "analysis"]

sources:
  local:
    enabled: true
    paths:
      - "~/Documents"
      - "~/Downloads"
```

Result:
```
Projects/
├── WebApp/
│   ├── code/
│   │   ├── app.js
│   │   └── index.html
│   └── documents/
│       └── design.pdf
└── DataScience/
    ├── code/
    │   └── analysis.py
    └── data/
        └── dataset.csv
```

### Example 3: GitHub Repos Organization

```yaml
organization:
  base_path: "~/CodeArchive"
  structure:
    - "{project}/{category}/{filename}"

sources:
  github:
    enabled: true
    clone_path: "/tmp/github-scan"
    repos: []  # Scans all your repos
```

This will:
1. Clone all your GitHub repos
2. Scan files in each repo
3. Organize them by repo name (project) and file type (category)

## Advanced Usage

### Custom Project Detection

Add custom patterns to automatically detect projects:

```python
from file_organizer import Config

config = Config()
config.add_project_pattern("MyProject", ["myproject", "proj"])
```

### Programmatic Usage

```python
from file_organizer import Config, UnifiedScanner, FileOrganizer, TransactionLogger

# Load config
config = Config()

# Scan files
scanner = UnifiedScanner(config)
files = scanner.get_all_files()

# Create organization plan
organizer = FileOrganizer(config)
plans = organizer.create_organization_plan(files)

# Execute (dry-run)
transactions = organizer.execute_plan(plans, dry_run=True)

# Execute for real
transactions = organizer.execute_plan(plans, dry_run=False)

# Log transactions
logger = TransactionLogger(config)
logger.log_transactions(transactions)

# Undo if needed
logger.undo_last_batch()
```

## Safety Features

### Dry-Run Mode
By default, all operations are in dry-run mode. This means the tool will show you what it *would* do without actually moving or copying files.

### Backups
When enabled, the tool creates backups of files before moving them. Backups are stored in the configured backup directory.

### Transaction Logging
Every operation is logged with:
- Timestamp
- Operation type (copy/move)
- Source and destination paths
- Success/failure status
- Error messages (if any)

### Undo Capability
You can undo the last batch of operations:

```bash
file-organizer undo
```

This will:
- For copied files: Delete the destination file
- For moved files: Move the file back to its original location (or restore from backup)

### Conflict Resolution

When a file already exists at the destination, you can choose how to handle it:

- **skip**: Don't process the file
- **rename**: Add a numeric suffix (e.g., `file_1.txt`)
- **keep_newest**: Only copy if the new file is newer
- **keep_oldest**: Only copy if the new file is older
- **overwrite**: Replace the existing file
- **prompt**: Ask the user what to do (interactive mode)

## Troubleshooting

### GitHub Authentication
If GitHub scanning fails:
```bash
gh auth login
gh auth status
```

### Google Drive Authentication
If Google Drive scanning fails:
1. Check credentials file exists
2. Delete `token.pickle` and re-authenticate
3. Verify Google Drive API is enabled in Cloud Console

### Permission Errors
If you get permission errors:
- Check file/folder permissions
- Ensure destination path is writable
- Run with appropriate user permissions

### Disk Space
The tool checks available disk space before organizing. If you see warnings:
- Free up disk space
- Change `mode` to "move" instead of "copy"
- Disable backups (not recommended)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this tool for any purpose.

## Author

Created by Emre

## Support

For issues, questions, or suggestions, please open an issue on GitHub.
