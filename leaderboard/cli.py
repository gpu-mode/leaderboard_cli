import click
import requests
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from .submit import submit_single_kernel, submit_directory_kernels
from .config import save_token, load_token, load_config, clear_token


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
@click.option('--endpoint', default='http://localhost:8000/api/submit', help='API endpoint URL')
def submit(
    operation: Optional[str],
    overload: Optional[str],
    dsl: str,
    device: str,
    file_path: Optional[str],
    directory_path: Optional[str],
    endpoint: str
):
    """Submit kernel implementation(s) to the leaderboard server.
    
    Requires authentication. Run 'leaderboard login' first.
    
    Examples:
    
      # Submit a single kernel file
      leaderboard submit --op add --overload Tensor --dsl cutedsl --device A100 --file add_v1.py
      
      # Submit multiple kernels from a directory
      leaderboard submit --dsl triton --device A100 --directory generated_kernels/
    """
    # Check authentication
    token = load_token()
    if not token:
        console.print("[red]Error: Not authenticated[/red]")
        console.print("Run [cyan]leaderboard login[/cyan] to authenticate first")
        raise click.Abort()
    
    # Validate input
    if not file_path and not directory_path:
        console.print("[red]Error: Either --file or --directory must be specified[/red]")
        raise click.Abort()
    
    if file_path and directory_path:
        console.print("[red]Error: Cannot specify both --file and --directory[/red]")
        raise click.Abort()
    
    try:
        if file_path:
            # Single file submission
            if not operation:
                console.print("[red]Error: --op is required for single file submission[/red]")
                raise click.Abort()
            
            result = submit_single_kernel(
                operation=operation,
                overload=overload,
                dsl=dsl,
                device=device,
                file_path=file_path,
                endpoint=endpoint,
                token=token
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
                dsl=dsl,
                device=device,
                directory_path=directory_path,
                endpoint=endpoint,
                token=token
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
    
    except requests.exceptions.ConnectionError:
        console.print(f"[red]Error: Could not connect to server at {endpoint}[/red]")
        console.print("[yellow]Make sure the server is running (see server/README.md)[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@cli.command()
@click.option('--op', '--operation', 'operation', help='Filter by operation type')
@click.option('--dsl', help='Filter by DSL type')
@click.option('--device', help='Filter by device type')
@click.option('--limit', default=20, help='Maximum number of results (default: 20)')
@click.option('--endpoint', default='http://localhost:8000', help='API base URL')
def list(operation: Optional[str], dsl: Optional[str], device: Optional[str], limit: int, endpoint: str):
    """List submitted kernels from the server.
    
    Examples:
    
      # List all submissions
      leaderboard list
      
      # List submissions for a specific operation
      leaderboard list --op add
    """
    try:
        # Build query parameters
        params = {'limit': limit}
        if operation:
            params['operation'] = operation
        if dsl:
            params['dsl'] = dsl
        if device:
            params['device'] = device
        
        # Query server
        response = requests.get(f"{endpoint}/api/submissions", params=params)
        response.raise_for_status()
        data = response.json()
        
        submissions = data.get('submissions', [])
        
        if not submissions:
            console.print("[yellow]No submissions found[/yellow]")
            return
        
        console.print(f"\n[bold]Found {data['count']} submission(s)[/bold]\n")
        
        for sub in submissions:
            panel_content = (
                f"[bold]ID:[/bold] {sub['id']}\n"
                f"[bold]Operation:[/bold] {sub['operation']}\n"
                f"[bold]Overload:[/bold] {sub.get('overload') or 'N/A'}\n"
                f"[bold]DSL:[/bold] {sub['dsl']}\n"
                f"[bold]Device:[/bold] {sub['device']}\n"
                f"[bold]File:[/bold] {sub['file_name']}\n"
                f"[bold]Submitted by:[/bold] {sub.get('username', 'Unknown')}\n"
                f"[bold]Submitted:[/bold] {sub['timestamp']}"
            )
            
            console.print(Panel(panel_content, border_style="blue"))
            console.print()
    
    except requests.exceptions.ConnectionError:
        console.print(f"[red]Error: Could not connect to server at {endpoint}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@cli.command()
@click.argument('submission_id', type=int)
@click.option('--endpoint', default='http://localhost:8000', help='API base URL')
def show(submission_id: int, endpoint: str):
    """Show details of a specific submission by ID.
    
    Example:
    
      leaderboard show 1
    """
    try:
        response = requests.get(f"{endpoint}/api/submissions/{submission_id}")
        response.raise_for_status()
        submission = response.json()
        
        # Show full details
        console.print(f"\n[bold cyan]Submission #{submission['id']}[/bold cyan]\n")
        
        info_table = Table(show_header=False, box=None)
        info_table.add_column("Field", style="bold")
        info_table.add_column("Value")
        
        info_table.add_row("Operation", submission['operation'])
        info_table.add_row("Overload", submission.get('overload') or 'N/A')
        info_table.add_row("DSL", submission['dsl'])
        info_table.add_row("Device", submission['device'])
        info_table.add_row("File Name", submission['file_name'])
        info_table.add_row("Submitted by", submission.get('username', 'Unknown'))
        info_table.add_row("Timestamp", submission['timestamp'])
        
        console.print(info_table)
        console.print(f"\n[bold]File Content:[/bold]\n")
        console.print(Panel(submission['file_content'], border_style="green"))
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Submission {submission_id} not found[/red]")
        else:
            console.print(f"[red]Error: {str(e)}[/red]")
    except requests.exceptions.ConnectionError:
        console.print(f"[red]Error: Could not connect to server at {endpoint}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@cli.command()
@click.option('--endpoint', default='http://localhost:8000', help='API base URL')
def login(endpoint: str):
    """Authenticate with GitHub.
    
    You need a GitHub Personal Access Token.
    Generate one at: https://github.com/settings/tokens
    
    Required scopes: read:user, user:email
    """
    console.print("[bold]GitHub Authentication[/bold]\n")
    console.print("Generate a Personal Access Token at: https://github.com/settings/tokens")
    console.print("Required scopes: [cyan]read:user[/cyan], [cyan]user:email[/cyan]\n")
    
    github_token = Prompt.ask("Enter your GitHub token", password=True)
    
    if not github_token:
        console.print("[red]Error: Token cannot be empty[/red]")
        return
    
    try:
        # Authenticate with server
        response = requests.post(
            f"{endpoint}/api/auth/github",
            json={"github_token": github_token},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        # Save token locally
        save_token(data["access_token"], data["user"]["username"])
        
        console.print(Panel(
            f"[green]✓[/green] Successfully authenticated!\n\n"
            f"[bold]Username:[/bold] {data['user']['username']}\n"
            f"[bold]Name:[/bold] {data['user'].get('name', 'N/A')}",
            title="Authentication Successful",
            border_style="green"
        ))
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            console.print("[red]Error: Invalid GitHub token[/red]")
        else:
            console.print(f"[red]Error: {e.response.text}[/red]")
    except requests.exceptions.ConnectionError:
        console.print(f"[red]Error: Could not connect to server at {endpoint}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@cli.command()
def logout():
    """Log out and clear authentication token."""
    config = load_config()
    if not config:
        console.print("[yellow]You are not logged in[/yellow]")
        return
    
    clear_token()
    console.print("[green]✓[/green] Successfully logged out")


@cli.command()
@click.option('--endpoint', default='http://localhost:8000', help='API base URL')
def whoami(endpoint: str):
    """Show current authenticated user."""
    config = load_config()
    
    if not config:
        console.print("[yellow]You are not logged in[/yellow]")
        console.print("Run [cyan]leaderboard login[/cyan] to authenticate")
        return
    
    console.print(Panel(
        f"[bold]Username:[/bold] {config.get('username', 'Unknown')}",
        title="Current User",
        border_style="blue"
    ))


if __name__ == '__main__':
    cli()
