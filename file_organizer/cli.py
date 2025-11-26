"""Command-line interface for file organizer."""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.tree import Tree
from rich import box

from .config import Config
from .scanner import UnifiedScanner
from .organizer import FileOrganizer
from .safety import TransactionLogger, SafetyValidator


console = Console()


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """File Organizer - Organize files from multiple sources with customizable schemas."""
    pass


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
def scan(config):
    """Scan all configured sources and show file inventory."""
    cfg = Config(Path(config) if config else None)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Scanning sources...", total=None)
        
        scanner = UnifiedScanner(cfg)
        results = scanner.scan_all_sources()
        
        progress.update(task, completed=True)
    
    # Display results
    console.print()
    for source_type, result in results.items():
        console.print(f"\n[bold cyan]{source_type.upper()}[/bold cyan]")
        console.print(f"  Source: {result.source_path}")
        console.print(f"  Files found: {len(result.files)}")
        console.print(f"  Total size: {_format_size(result.total_size)}")
        
        if result.errors:
            console.print(f"  [yellow]Errors: {len(result.errors)}[/yellow]")
            for error in result.errors[:5]:
                console.print(f"    • {error}")
    
    # Summary table
    total_files = sum(len(r.files) for r in results.values())
    total_size = sum(r.total_size for r in results.values())
    
    console.print()
    console.print(Panel(
        f"[bold]Total:[/bold] {total_files} files, {_format_size(total_size)}",
        title="Summary",
        border_style="green"
    ))


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
@click.option('--limit', '-l', type=int, default=50, help='Max number of plans to show')
def preview(config, limit):
    """Preview organization changes without executing them."""
    cfg = Config(Path(config) if config else None)
    
    # Scan files
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Scanning files...", total=None)
        scanner = UnifiedScanner(cfg)
        files = scanner.get_all_files()
        progress.update(task, completed=True)
        
        task = progress.add_task("Creating organization plan...", total=None)
        organizer = FileOrganizer(cfg)
        plans = organizer.create_organization_plan(files)
        progress.update(task, completed=True)
    
    # Display preview
    console.print()
    console.print(f"[bold]Organization Preview[/bold] ({len(plans)} files)")
    console.print()
    
    # Show sample plans
    for i, plan in enumerate(plans[:limit]):
        if plan.skip:
            console.print(f"[dim]{i+1}. {plan}[/dim]")
        elif plan.conflict:
            console.print(f"[yellow]{i+1}. {plan}[/yellow]")
        else:
            console.print(f"[green]{i+1}. {plan}[/green]")
    
    if len(plans) > limit:
        console.print(f"\n[dim]... and {len(plans) - limit} more[/dim]")
    
    # Statistics
    skipped = sum(1 for p in plans if p.skip)
    conflicts = sum(1 for p in plans if p.conflict)
    will_process = len(plans) - skipped
    
    table = Table(title="Statistics", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta", justify="right")
    
    table.add_row("Total files", str(len(plans)))
    table.add_row("Will process", str(will_process))
    table.add_row("Will skip", str(skipped))
    table.add_row("Conflicts", str(conflicts))
    
    console.print()
    console.print(table)
    
    # Disk space check
    validator = SafetyValidator()
    required_space = validator.estimate_disk_space(plans)
    base_path = Path(cfg.get('organization.base_path'))
    has_space, available = validator.check_available_space(base_path.parent, required_space)
    
    console.print()
    console.print(f"Required disk space: {_format_size(required_space)}")
    console.print(f"Available disk space: {_format_size(available)}")
    
    if not has_space:
        console.print("[bold red]⚠ Insufficient disk space![/bold red]")


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
@click.option('--dry-run/--execute', default=True, help='Dry run (default) or execute')
@click.confirmation_option(prompt='Are you sure you want to organize files?')
def organize(config, dry_run):
    """Execute file organization."""
    cfg = Config(Path(config) if config else None)
    
    # Override dry_run if specified
    if not dry_run:
        cfg.set('safety.dry_run_default', False)
    
    # Scan files
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Scanning files...", total=None)
        scanner = UnifiedScanner(cfg)
        files = scanner.get_all_files()
        progress.update(task, completed=True)
        
        task = progress.add_task("Creating organization plan...", total=None)
        organizer = FileOrganizer(cfg)
        plans = organizer.create_organization_plan(files)
        progress.update(task, completed=True)
        
        # Execute
        task = progress.add_task(
            f"{'[DRY RUN] ' if dry_run else ''}Organizing files...",
            total=len(plans)
        )
        
        transactions = organizer.execute_plan(plans, dry_run=dry_run)
        
        progress.update(task, completed=len(plans))
    
    # Log transactions
    if not dry_run:
        logger = TransactionLogger(cfg)
        logger.log_transactions(transactions)
    
    # Display results
    console.print()
    successful = sum(1 for t in transactions if t.success)
    failed = sum(1 for t in transactions if not t.success)
    
    if dry_run:
        console.print(Panel(
            f"[bold green]DRY RUN COMPLETE[/bold green]\n\n"
            f"Would process: {successful} files\n"
            f"Would fail: {failed} files\n\n"
            f"Run with [bold]--execute[/bold] to actually organize files.",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            f"[bold green]ORGANIZATION COMPLETE[/bold green]\n\n"
            f"Successful: {successful} files\n"
            f"Failed: {failed} files",
            border_style="green"
        ))
    
    # Show errors
    if failed > 0:
        console.print("\n[bold red]Errors:[/bold red]")
        for t in transactions:
            if not t.success and t.error:
                console.print(f"  • {t.source_path}: {t.error}")


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
@click.confirmation_option(prompt='Are you sure you want to undo the last operation?')
def undo(config):
    """Undo the last organization operation."""
    cfg = Config(Path(config) if config else None)
    logger = TransactionLogger(cfg)
    
    # Get last batch
    batch = logger.get_last_batch()
    
    if not batch:
        console.print("[yellow]No operations to undo[/yellow]")
        return
    
    console.print(f"[bold]Undoing {len(batch)} operations...[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Undoing...", total=None)
        successful, failed = logger.undo_last_batch()
        progress.update(task, completed=True)
    
    console.print()
    console.print(Panel(
        f"[bold green]UNDO COMPLETE[/bold green]\n\n"
        f"Successful: {successful}\n"
        f"Failed: {failed}",
        border_style="green" if failed == 0 else "yellow"
    ))


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
@click.option('--limit', '-l', type=int, default=20, help='Number of transactions to show')
def history(config, limit):
    """Show recent organization operations."""
    cfg = Config(Path(config) if config else None)
    logger = TransactionLogger(cfg)
    
    transactions = logger.get_recent_transactions(limit)
    
    if not transactions:
        console.print("[yellow]No transaction history[/yellow]")
        return
    
    table = Table(title="Transaction History", box=box.ROUNDED)
    table.add_column("Time", style="cyan")
    table.add_column("Operation", style="magenta")
    table.add_column("Source", style="white")
    table.add_column("Destination", style="white")
    table.add_column("Status", style="green")
    
    for t in transactions:
        status = "✓" if t.success else f"✗ {t.error}"
        table.add_row(
            t.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            t.operation.value,
            str(t.source_path)[:50],
            str(t.destination_path)[:50],
            status
        )
    
    console.print(table)


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
def init_config(config):
    """Initialize a new configuration file."""
    config_path = Path(config) if config else Config.DEFAULT_CONFIG_PATH
    
    if config_path.exists():
        if not click.confirm(f"Config already exists at {config_path}. Overwrite?"):
            return
    
    cfg = Config(config_path)
    console.print(f"[green]✓[/green] Configuration initialized at: {config_path}")
    console.print("\nEdit this file to customize your organization rules.")
    console.print(f"\nExample: [cyan]nano {config_path}[/cyan]")


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
def show_config(config):
    """Show current configuration."""
    cfg = Config(Path(config) if config else None)
    
    import yaml
    console.print(Panel(
        yaml.dump(cfg.config, default_flow_style=False, sort_keys=False),
        title=f"Configuration: {cfg.config_path}",
        border_style="cyan"
    ))


def _format_size(bytes_size: int) -> str:
    """Format bytes as human-readable size.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


if __name__ == '__main__':
    cli()
