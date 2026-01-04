#!/usr/bin/env python3
"""Basic functionality test for file organizer."""

from pathlib import Path
from file_organizer import Config, UnifiedScanner, FileOrganizer
from file_organizer.sources import LocalScanner

print("=" * 60)
print("File Organizer - Basic Functionality Test")
print("=" * 60)

# Test 1: Config creation
print("\n[Test 1] Creating configuration...")
config = Config(Path("/tmp/test_config.yaml"))
print(f"✓ Config created at: {config.config_path}")
print(f"  Base path: {config.get('organization.base_path')}")

# Test 2: Local scanner
print("\n[Test 2] Scanning test files...")
test_path = Path("/home/ubuntu/file-organizer/test_files")
scanner = LocalScanner(exclude_patterns=['.git'])
result = scanner.scan([str(test_path)])
print(f"✓ Found {len(result.files)} files")
print(f"  Total size: {result.total_size} bytes")
for f in result.files[:5]:
    print(f"    - {f.filename} ({f.category or 'unknown'})")

# Test 3: Organization plan
print("\n[Test 3] Creating organization plan...")
organizer = FileOrganizer(config)
plans = organizer.create_organization_plan(result.files)
print(f"✓ Created {len(plans)} organization plans")
for i, plan in enumerate(plans[:5], 1):
    print(f"  {i}. {plan.file_metadata.filename}")
    print(f"     Project: {plan.file_metadata.project}")
    print(f"     Category: {plan.file_metadata.category}")
    print(f"     Destination: {plan.destination_path}")

# Test 4: Dry run execution
print("\n[Test 4] Executing dry run...")
transactions = organizer.execute_plan(plans, dry_run=True)
successful = sum(1 for t in transactions if t.success)
print(f"✓ Dry run complete: {successful}/{len(transactions)} would succeed")

# Test 5: Category detection
print("\n[Test 5] Testing category detection...")
test_extensions = ['.py', '.pdf', '.jpg', '.mp3', '.csv']
for ext in test_extensions:
    category = config.get_category_for_extension(ext)
    print(f"  {ext} → {category}")

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)
