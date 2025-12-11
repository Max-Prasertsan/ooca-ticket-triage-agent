"""
Runner Module
==============

Command-line interface for the support ticket triage agent.

Provides a CLI for processing tickets from files or stdin,
and outputs results as JSON.

Usage:
    python -m src.triage_agent.runner
    python -m src.triage_agent.runner --input tickets.json
    python -m src.triage_agent.runner --output results.json
"""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from src.triage_agent.config import Config, setup_logging
from src.triage_agent.core.agent import TriageAgent
from src.triage_agent.models.ticket import SAMPLE_TICKETS, SupportTicket
from src.triage_agent.models.triage_output import TriageOutput

console = Console()
logger = logging.getLogger(__name__)


def process_tickets(
    agent: TriageAgent,
    tickets: list[SupportTicket],
    verbose: bool = False
) -> list[TriageOutput]:
    """
    Process a list of tickets through the triage agent.
    
    Args:
        agent: The triage agent instance.
        tickets: List of tickets to process.
        verbose: Whether to print detailed output.
    
    Returns:
        list[TriageOutput]: List of triage results.
    """
    results = []
    
    for i, ticket in enumerate(tickets, 1):
        if verbose:
            console.print(f"\n[bold blue]Processing ticket {i}/{len(tickets)}:[/bold blue]")
            console.print(Panel(
                f"[bold]{ticket.subject}[/bold]\n\n{ticket.body[:200]}...",
                title=f"Ticket: {ticket.ticket_id}",
                subtitle=f"Customer: {ticket.customer_email}"
            ))
        
        try:
            result = agent.triage(ticket)
            results.append(result)
            
            if verbose:
                display_result(result)
                
        except Exception as e:
            logger.error(f"Failed to process ticket {ticket.ticket_id}: {e}")
            console.print(f"[red]Error processing {ticket.ticket_id}: {e}[/red]")
    
    return results


def display_result(result: TriageOutput) -> None:
    """
    Display a triage result in a formatted table.
    
    Args:
        result: The triage output to display.
    """
    # Classification table
    table = Table(title=f"Triage Result: {result.ticket_id}", show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Urgency", f"[bold]{result.urgency.value.upper()}[/bold]")
    table.add_row("Issue Type", result.issue_type.value)
    table.add_row("Sentiment", result.customer_sentiment.value)
    table.add_row("Product", result.product or "N/A")
    table.add_row("Risk Signals", ", ".join([s.value for s in result.customer_risk_signals]) or "None")
    table.add_row("Recommended Action", f"[bold]{result.recommended_action.value}[/bold]")
    table.add_row("Specialist Queue", result.recommended_specialist_queue.value)
    table.add_row("Confidence", f"{result.confidence_score:.0%}")
    
    console.print(table)
    
    # Tool calls
    if result.tool_calls:
        console.print("\n[bold cyan]Tool Calls:[/bold cyan]")
        for call in result.tool_calls:
            status = "✓" if call.success else "✗"
            console.print(f"  {status} {call.tool_name}")
    
    # KB Results
    if result.knowledge_base_results:
        console.print("\n[bold cyan]Knowledge Base Results:[/bold cyan]")
        for kb in result.knowledge_base_results[:3]:
            console.print(f"  • {kb.title} (score: {kb.relevance_score:.2f})")
    
    # Suggested reply
    if result.suggested_reply:
        console.print("\n[bold cyan]Suggested Reply:[/bold cyan]")
        console.print(Panel(result.suggested_reply, border_style="green"))
    
    # Reasoning
    if result.reasoning:
        console.print(f"\n[dim]Reasoning: {result.reasoning}[/dim]")


def load_tickets_from_file(filepath: str) -> list[SupportTicket]:
    """
    Load tickets from a JSON file.
    
    Args:
        filepath: Path to the JSON file.
    
    Returns:
        list[SupportTicket]: List of parsed tickets.
    """
    with open(filepath, "r") as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return [SupportTicket.model_validate(t) for t in data]
    else:
        return [SupportTicket.model_validate(data)]


def save_results(results: list[TriageOutput], filepath: str) -> None:
    """
    Save results to a JSON file.
    
    Args:
        results: List of triage outputs.
        filepath: Path to save to.
    """
    data = [r.model_dump() for r in results]
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    console.print(f"[green]Results saved to {filepath}[/green]")


@click.command()
@click.option(
    "--input", "-i", "input_file",
    type=click.Path(exists=True),
    help="Input JSON file with tickets (uses sample tickets if not provided)"
)
@click.option(
    "--output", "-o", "output_file",
    type=click.Path(),
    help="Output JSON file for results"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    default=True,
    help="Show detailed output"
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    default=False,
    help="Minimal output (JSON only)"
)
def main(
    input_file: Optional[str],
    output_file: Optional[str],
    verbose: bool,
    quiet: bool
) -> None:
    """
    Support Ticket Triage Agent CLI.
    
    Process support tickets and output triage results.
    """
    # Setup
    config = Config()
    setup_logging(config)
    
    if quiet:
        verbose = False
    
    # Header
    if verbose:
        console.print("\n[bold blue]╔═══════════════════════════════════════╗[/bold blue]")
        console.print("[bold blue]║   Support Ticket Triage Agent v1.0    ║[/bold blue]")
        console.print("[bold blue]╚═══════════════════════════════════════╝[/bold blue]\n")
        
        if not config.is_api_key_set():
            console.print("[yellow]⚠ OPENAI_API_KEY not set - using rule-based fallback[/yellow]\n")
    
    # Load tickets
    if input_file:
        tickets = load_tickets_from_file(input_file)
        if verbose:
            console.print(f"Loaded {len(tickets)} tickets from {input_file}")
    else:
        tickets = SAMPLE_TICKETS
        if verbose:
            console.print(f"Using {len(tickets)} sample tickets")
    
    # Initialize agent
    agent = TriageAgent(config)
    
    if verbose:
        console.print(f"Agent initialized with {len(agent.tool_registry)} tools")
        console.print(f"Available tools: {', '.join(agent.tool_registry.get_names())}\n")
    
    # Process tickets
    results = process_tickets(agent, tickets, verbose)
    
    # Output results
    if output_file:
        save_results(results, output_file)
    elif quiet:
        # JSON output only
        output = [r.model_dump() for r in results]
        print(json.dumps(output, indent=2, default=str))
    
    # Summary
    if verbose:
        console.print("\n[bold blue]═══════════════════════════════════════[/bold blue]")
        console.print(f"[bold]Processed {len(results)} tickets[/bold]")
        
        # Stats
        urgency_counts = {}
        action_counts = {}
        for r in results:
            urgency_counts[r.urgency.value] = urgency_counts.get(r.urgency.value, 0) + 1
            action_counts[r.recommended_action.value] = action_counts.get(r.recommended_action.value, 0) + 1
        
        console.print(f"\nUrgency distribution: {urgency_counts}")
        console.print(f"Action distribution: {action_counts}")


if __name__ == "__main__":
    main()