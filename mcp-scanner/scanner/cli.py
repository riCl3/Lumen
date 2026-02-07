"""
Command Line Interface for MCP Scanner.
"""
import click
import json
import sys
from pathlib import Path
from typing import Dict, Any

try:
    from scanner.discovery import FileScanner
    from scanner.analyzer import StaticAnalyzer
    from scanner.manifest import ManifestGenerator
except ImportError:
    # Allow running from root without package install for dev
    sys.path.append(str(Path(__file__).parent.parent))
    from scanner.discovery import FileScanner
    from scanner.analyzer import StaticAnalyzer
    from scanner.manifest import ManifestGenerator

@click.group()
def main():
    """MCP Scanner CLI - Discover and Analyze MCP Servers"""
    pass

def get_color_for_risk(level: str) -> str:
    """Returns color string based on risk level."""
    if level == "SAFE":
        return "green"
    elif level == "MEDIUM":
        return "yellow"
    elif level == "HIGH":
        return "red"
    return "white"

@main.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--output', '-o', default='scan_results.json', help='Output JSON file path')
def scan(directory, output):
    """
    Run full scan pipeline on a directory.
    
    DIRECTORY: The root directory to scan for MCP servers.
    """
    click.echo(f"Starting scan of: {directory}")
    
    # Initialize components
    scanner = FileScanner()
    analyzer = StaticAnalyzer()
    manifest_gen = ManifestGenerator()
    
    # 1. Discovery Phase
    click.echo("Discovering MCP servers...")
    discovered_items = scanner.discover_servers(directory)
    
    if not discovered_items:
        click.secho("No MCP servers or tools found.", fg="yellow")
        return

    click.echo(f"Found {len(discovered_items)} potential items.")

    # 2. Analysis Phase
    with click.progressbar(discovered_items, label="Analyzing servers") as bar:
        for item in bar:
            # Only analyze python files
            if item["type"].startswith("python"):
                file_path = Path(item["path"])
                try:
                    content = file_path.read_text(encoding='utf-8')
                    analysis = analyzer.scan_code(content)
                    manifest_gen.add_server_analysis(item, analysis)
                except Exception as e:
                    click.echo(f"\nError analyzing {item['path']}: {e}", err=True)
            else:
                # For non-python (config files), add basic entry
                manifest_gen.add_server_analysis(item, {
                    "risk_score": 0, 
                    "risk_level": "UNKNOWN",
                    "breakdown": [{"description": "Config file - manual review required"}]
                })

    # 3. Save Results
    try:
        manifest_gen.save_to_file(output)
        click.echo(f"\nResults saved to: ", nl=False)
        click.secho(output, fg="blue", bold=True)
    except Exception as e:
        click.secho(f"Failed to save results: {e}", fg="red")
        sys.exit(1)

    # 4. Print Summary
    click.echo("\n" + manifest_gen.get_summary())


@main.command()
@click.argument('file_path', default='scan_results.json', type=click.Path(exists=True, dir_okay=False))
def report(file_path):
    """
    Display the last scan results in readable format.
    
    FILE_PATH: Path to the scan results JSON file (default: scan_results.json)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        click.secho(f"\nScan Report ({data.get('scan_date', 'Unknown Date')})", bold=True, underline=True)
        click.echo(f"Total Items: {data.get('total_servers_found', 0)}\n")
        
        servers = data.get('servers', [])
        if not servers:
            click.echo("No servers in report.")
            return
            
        for server in servers:
            name = server.get('name', 'Unknown')
            path = server.get('path', 'Unknown')
            risk = server.get('risk_analysis', {})
            level = risk.get('risk_level', 'UNKNOWN')
            score = risk.get('risk_score', 0)
            
            color = get_color_for_risk(level)
            
            click.secho(f"[{level}] {name}", fg=color, bold=True)
            click.echo(f"  Path: {path}")
            click.echo(f"  Score: {score}")
            
            breakdown = risk.get('breakdown', [])
            if breakdown:
                click.echo("  Findings:")
                for item in breakdown:
                    desc = item.get('description', '')
                    click.echo(f"    - {desc}")
            else:
                 click.echo("  No risky patterns found.")
            
            click.echo("-" * 40)
            
    except json.JSONDecodeError:
        click.secho("Error: Invalid JSON file.", fg="red")
    except Exception as e:
        click.secho(f"Error reading report: {e}", fg="red")

if __name__ == '__main__':
    main()
