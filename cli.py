#!/usr/bin/env python3
"""
Google Ads Keyword Research CLI
Interactive terminal interface for keyword research and clustering.
"""

import sys
import os
import asyncio
from typing import List, Dict
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

# Add api to path
sys.path.append(os.path.join(os.path.dirname(__file__), "api"))

from keyword_planner import generate_keyword_ideas
from clustering import ClusteringEngine, Cluster
from sheets_exporter import create_and_export
from sheets_exporter_clustered import create_and_export_clustered

console = Console()

def print_banner():
    banner = """
    [bold blue]╔══════════════════════════════════════════════════════════════╗[/bold blue]
    [bold blue]║             GOOGLE ADS KEYWORD RESEARCH CLI                  ║[/bold blue]
    [bold blue]║             Hagakure Edition | v2.0.0                        ║[/bold blue]
    [bold blue]╚══════════════════════════════════════════════════════════════╝[/bold blue]
    """
    rprint(banner)

def display_clusters(clusters: List[Cluster]):
    table = Table(title="Generated Ad Groups (Hagakure)")
    
    table.add_column("Ad Group Name", style="cyan", no_wrap=True)
    table.add_column("Keywords", style="magenta")
    table.add_column("Vol", justify="right", style="green")
    
    total_kws = 0
    
    for cluster in clusters[:10]:  # Show top 10
        kw_count = len(cluster.keywords)
        total_kws += kw_count
        preview = ", ".join([k['keyword'] for k in cluster.keywords[:3]])
        if kw_count > 3:
            preview += f" (+{kw_count-3} more)"
            
        vol = sum(k.get('avgMonthlySearches', 0) for k in cluster.keywords)
        table.add_row(cluster.name, preview, f"{vol:,}")
        
    console.print(table)
    
    if len(clusters) > 10:
        rprint(f"[italic]...and {len(clusters)-10} more groups[/italic]")
        
    # Show negatives if any
    if clusters and clusters[0].negative_candidates:
        neg_count = len(clusters[0].negative_candidates)
        rprint(f"\n[bold red]⚠️  Found {neg_count} Negative Keyword Candidates[/bold red]")
        rprint(f"[red]{', '.join(clusters[0].negative_candidates[:5])}...[/red]")

import argparse

def main():
    parser = argparse.ArgumentParser(description="Google Ads Keyword Research CLI")
    parser.add_argument("--url", help="Target website URL")
    parser.add_argument("--method", type=int, choices=[1, 2, 3], help="Clustering method (1=Rule, 2=ML, 3=Hybrid)")
    parser.add_argument("--export", choices=['y', 'n'], help="Auto-export to Sheets (y/n)")
    
    args = parser.parse_args()

    print_banner()
    
    # 1. Get Input
    if args.url:
        url = args.url
        rprint(f"[bold green]Target URL:[/bold green] {url}")
    else:
        url = Prompt.ask("[bold green]Enter Website URL[/bold green]", default="https://www.netflix.com")
    
    # 2. Select Method
    if args.method:
        method_choice = args.method
        method_names = {1: "The Strict Linguist", 2: "The Semantic Brain", 3: "The Hybrid Strategist"}
        rprint(f"[bold yellow]Selected Method:[/bold yellow] {method_names.get(method_choice)}")
    else:
        rprint("\n[bold yellow]Select Clustering Method:[/bold yellow]")
        rprint("1. [cyan]The Strict Linguist[/cyan] (Rule-Based) - Fast, strict control")
        rprint("2. [magenta]The Semantic Brain[/magenta] (ML-Based) - AI-powered intent grouping")
        rprint("3. [green]The Hybrid Strategist[/green] (Recommended) - Best of both worlds")
        
        method_choice = IntPrompt.ask("Choice", choices=["1", "2", "3"], default=3)
    
    # 3. Fetch Keywords
    keywords = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="Fetching keywords from Google Ads...", total=None)
        
        # Call API (synchronous for now, but wrapped in spinner)
        result = generate_keyword_ideas(url)
        
        if not result.get('success'):
            rprint(f"[bold red]Error:[/bold red] {result.get('error')}")
            return
            
        keywords = result.get('keywords', [])
        rprint(f"[bold green]✅ Found {len(keywords)} raw keywords[/bold green]")

    # 4. Cluster Keywords
    engine = ClusteringEngine()
    clusters = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Clustering keywords (Hagakure Logic)...", total=None)
        
        if method_choice == 1:
            clusters = engine.cluster_rule_based(keywords)
        elif method_choice == 2:
            clusters = engine.cluster_ml_semantic(keywords)
        else:
            clusters = engine.cluster_hybrid(keywords)
            
    # 5. Display Results
    display_clusters(clusters)
    
    # 6. Export
    should_export = False
    if args.export:
        should_export = (args.export == 'y')
    else:
        should_export = (Prompt.ask("\nExport to Google Sheets?", choices=["y", "n"], default="y") == "y")

    if should_export:
        rprint("[italic]Exporting clustered ad groups...[/italic]")
        sheet_url = create_and_export_clustered(clusters, url)
        if sheet_url:
            rprint(f"[bold green]🚀 Exported:[/bold green] {sheet_url}")
        else:
            rprint("[bold red]Export failed[/bold red]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        rprint("\n[bold red]Aborted by user[/bold red]")
        sys.exit(0)
