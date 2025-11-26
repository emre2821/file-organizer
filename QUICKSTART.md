# Quick Start Guide

Get started with File Organizer in 5 minutes!

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

## First Run

### 1. Initialize Configuration

```bash
file-organizer init-config
```

This creates a config file at `~/.config/file-organizer/config.yaml`

### 2. Add Your Paths

Edit the config file to add paths you want to organize:

```bash
nano ~/.config/file-organizer/config.yaml
```

Update the `sources.local.paths` section:

```yaml
sources:
  local:
    enabled: true
    paths:
      - "/Users/yourname/Downloads"  # Mac
      # - "C:/Users/yourname/Downloads"  # Windows
      # - "/home/yourname/Downloads"  # Linux
```

### 3. Scan Your Files

```bash
file-organizer scan
```

This will show you what files were found.

### 4. Preview Organization

```bash
file-organizer preview
```

This shows you what the tool *would* do without actually moving anything.

### 5. Organize (Dry Run)

```bash
file-organizer organize
```

By default, this is a dry run - it won't actually move files. It just shows you what would happen.

### 6. Actually Organize

When you're ready:

```bash
file-organizer organize --execute
```

This will actually organize your files!

### 7. Undo (If Needed)

Made a mistake? No problem:

```bash
file-organizer undo
```

## Common Scenarios

### Organize Downloads by Date

Use the example config:

```bash
cp examples/config_by_date.yaml ~/.config/file-organizer/config.yaml
# Edit to add your Downloads path
file-organizer preview
file-organizer organize --execute
```

### Organize GitHub Repos

```bash
cp examples/config_github.yaml ~/.config/file-organizer/config.yaml
file-organizer preview
file-organizer organize --execute
```

### Organize by Project

```bash
cp examples/config_by_project.yaml ~/.config/file-organizer/config.yaml
# Edit to add your project keywords
file-organizer preview
file-organizer organize --execute
```

## Tips

1. **Always preview first**: Use `preview` to see what will happen
2. **Start with dry run**: The default `organize` command is safe
3. **Use undo**: If something goes wrong, `undo` will reverse it
4. **Check history**: Use `history` to see past operations
5. **Customize config**: The config file is very flexible - experiment!

## Need Help?

- Read the full [README.md](README.md)
- Check the [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Look at example configs in `examples/`
- Open an issue on GitHub

## Safety Features

File Organizer is designed to be safe:

- ✅ Dry-run by default
- ✅ Creates backups before moving files
- ✅ Logs all operations
- ✅ Undo capability
- ✅ Conflict resolution
- ✅ Disk space checking

You can't accidentally destroy your files!
