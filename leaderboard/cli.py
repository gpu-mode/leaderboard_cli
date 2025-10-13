"""Main CLI interface for BackendBench."""

import click
import os
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .database import SubmissionDB
from .submit import submit_single_kernel, submit_directory_kernels


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Leaderboard CLI - Submit and manage kernel implementations."""
    pass


@cli.command()
@click.option('--op', '--operation', 'operation', help='Operation type (e.g., add, mul, matmul)')
@click.option('--overload', help='Overload type (e.g., Tensor, Float)')
@click.option('--dsl', required=True, help='DSL type (e.g., cutedsl, triton)')
@click.option('--device', required=True, help='Device type (e.g., A100, H100)')
@click.option('--file', 'file_path', type=click.Path(exists=True), help='Path to kernel file')
@click.option('--directory', 'directory_path', type=click.Path(exists=True), help='Path to directory containing kernels')
@click.option('--endpoint', default='http://localhost:8000/submit', help='API endpoint URL')
@click.option('--local-only', is_flag=True, default=True, help='Store submissions locally only (default: True)')
def submit(
    operation: Optional[str],
    overload: Optional[str],
    dsl: str,
    device: str,
    file_path: Optional[str],
    directory_path: Optional[str],
    endpoint: str,
    local_only: bool
):
    """Submit kernel implementation(s) to the leaderboard.
    
    Examples:
    
      # Submit a single kernel file
      backendbench submit --op add --overload Tensor --dsl cutedsl --device A100 --file add_implementation_v1.py
      
      # Submit multiple kernels from a directory
      backendbench submit --dsl triton --device A100 --directory generated_kernels/
    """
    # Validate input
    if not file_path and not directory_path:
        console.print("[red]Error: Either --file or --directory must be specified[/red]")
        raise click.Abort()
    
    if file_path and directory_path:
        console.print("[red]Error: Cannot specify both --file and --directory[/red]")
        raise click.Abort()
    
    # Initialize database
    db = SubmissionDB()
    
    try:
        if file_path:
            # Single file submission
            if not operation:
                console.print("[red]Error: --op is required for single file submission[/red]")
                raise click.Abort()
            
            result = submit_single_kernel(
                db=db,
                operation=operation,
                overload=overload,
                dsl=dsl,
                device=device,
                file_path=file_path,
                endpoint=endpoint,
                local_only=local_only
            )
            
            if result['success']:
                console.print(Panel(
                    f"[green]✓[/green] Successfully submitted kernel!\n\n"
                    f"[bold]Submission ID:[/bold] {result['submission_id']}\n"
                    f"[bold]Operation:[/bold] {operation}\n"
                    f"[bold]DSL:[/bold] {dsl}\n"
                    f"[bold]Device:[/bold] {device}\n"
                    f"[bold]File:[/bold] {result['file_name']}",
                    title="Submission Successful",
                    border_style="green"
                ))
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
        
        else:
            # Directory submission
            results = submit_directory_kernels(
                db=db,
                dsl=dsl,
                device=device,
                directory_path=directory_path,
                endpoint=endpoint,
                local_only=local_only
            )
            
            # Display results
            success_count = sum(1 for r in results if r['success'])
            total_count = len(results)
            
            console.print(f"\n[bold]Submission Summary:[/bold]")
            console.print(f"Total files processed: {total_count}")
            console.print(f"[green]Successful: {success_count}[/green]")
            console.print(f"[red]Failed: {total_count - success_count}[/red]\n")
            
            # Show details table
            table = Table(title="Submission Details")
            table.add_column("File", style="cyan")
            table.add_column("Operation", style="magenta")
            table.add_column("Status", style="green")
            table.add_column("ID")
            
            for result in results:
                status = "✓" if result['success'] else "✗"
                status_style = "green" if result['success'] else "red"
                table.add_row(
                    result['file_name'],
                    result.get('operation', 'N/A'),
                    f"[{status_style}]{status}[/{status_style}]",
                    str(result.get('submission_id', '-'))
                )
            
            console.print(table)
    
    finally:
        db.close()


@cli.command()
@click.option('--op', '--operation', 'operation', help='Filter by operation type')
@click.option('--dsl', help='Filter by DSL type')
@click.option('--device', help='Filter by device type')
@click.option('--limit', default=20, help='Maximum number of results (default: 20)')
@click.option('--show-content', is_flag=True, help='Show file content')
def list(operation: Optional[str], dsl: Optional[str], device: Optional[str], limit: int, show_content: bool):
    """List submitted kernels from local database.
    
    Examples:
    
      # List all submissions
      backendbench list
      
      # List submissions for a specific operation
      backendbench list --op add
      
      # List submissions with file content
      backendbench list --show-content --limit 5
    """
    db = SubmissionDB()
    
    try:
        submissions = db.get_submissions(
            operation=operation,
            dsl=dsl,
            device=device,
            limit=limit
        )
        
        if not submissions:
            console.print("[yellow]No submissions found[/yellow]")
            return
        
        console.print(f"\n[bold]Found {len(submissions)} submission(s)[/bold]\n")
        
        for sub in submissions:
            panel_content = (
                f"[bold]ID:[/bold] {sub['id']}\n"
                f"[bold]Operation:[/bold] {sub['operation']}\n"
                f"[bold]Overload:[/bold] {sub['overload'] or 'N/A'}\n"
                f"[bold]DSL:[/bold] {sub['dsl']}\n"
                f"[bold]Device:[/bold] {sub['device']}\n"
                f"[bold]File:[/bold] {sub['file_name']}\n"
                f"[bold]Submitted:[/bold] {sub['timestamp']}"
            )
            
            if show_content:
                panel_content += f"\n\n[bold]Content:[/bold]\n{sub['file_content'][:500]}"
                if len(sub['file_content']) > 500:
                    panel_content += "\n[dim]...(truncated)[/dim]"
            
            console.print(Panel(panel_content, border_style="blue"))
            console.print()
    
    finally:
        db.close()


@cli.command()
@click.argument('submission_id', type=int)
def show(submission_id: int):
    """Show details of a specific submission by ID.
    
    Example:
    
      backendbench show 1
    """
    db = SubmissionDB()
    
    try:
        submission = db.get_submission_by_id(submission_id)
        
        if not submission:
            console.print(f"[red]Submission {submission_id} not found[/red]")
            return
        
        # Show full details
        console.print(f"\n[bold cyan]Submission #{submission['id']}[/bold cyan]\n")
        
        info_table = Table(show_header=False, box=None)
        info_table.add_column("Field", style="bold")
        info_table.add_column("Value")
        
        info_table.add_row("Operation", submission['operation'])
        info_table.add_row("Overload", submission['overload'] or 'N/A')
        info_table.add_row("DSL", submission['dsl'])
        info_table.add_row("Device", submission['device'])
        info_table.add_row("File Name", submission['file_name'])
        info_table.add_row("File Path", submission['file_path'] or 'N/A')
        info_table.add_row("Timestamp", submission['timestamp'])
        
        console.print(info_table)
        console.print(f"\n[bold]File Content:[/bold]\n")
        console.print(Panel(submission['file_content'], border_style="green"))
    
    finally:
        db.close()


if __name__ == '__main__':
    cli()

