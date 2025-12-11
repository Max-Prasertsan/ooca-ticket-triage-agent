"""
Interactive Chat Interface
===========================

Provides a terminal-based interactive interface for the triage agent.

Usage:
    python -m src.triage_agent.chat
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from src.triage_agent.config import Config, setup_logging
from src.triage_agent.core.agent import TriageAgent
from src.triage_agent.models.ticket import SupportTicket
from src.triage_agent.models.triage_output import TriageOutput

console = Console()

# Ticket counter for auto-generating IDs
_ticket_counter = 0


def generate_ticket_id() -> str:
    """Generate a unique ticket ID."""
    global _ticket_counter
    _ticket_counter += 1
    timestamp = datetime.now().strftime("%Y%m%d")
    short_uuid = uuid.uuid4().hex[:6].upper()
    return f"T-{timestamp}-{short_uuid}"


def display_welcome():
    """Display welcome banner."""
    console.print()
    console.print(Panel.fit(
        "[bold blue]🎫 Support Ticket Triage Agent[/bold blue]\n\n"
        "Interactive terminal interface for triaging support tickets.\n"
        "Type [green]'help'[/green] for commands or [green]'quit'[/green] to exit.",
        border_style="blue"
    ))
    console.print()


def display_help():
    """Display help information."""
    help_text = """
[bold cyan]Available Commands:[/bold cyan]

  [green]new[/green]        - Create a new ticket interactively
  [green]quick[/green]      - Quick ticket entry (subject + body only)
  [green]sample[/green]     - Triage a sample ticket
  [green]json[/green]       - Enter a ticket as JSON
  [green]help[/green]       - Show this help message
  [green]quit[/green]       - Exit the application

[bold cyan]How it works:[/bold cyan]

1. Enter your support ticket details
2. The agent analyzes the ticket using AI + tools
3. You get urgency, sentiment, routing, and suggested reply

[bold cyan]Tips:[/bold cyan]

- Be detailed in ticket descriptions for better triage
- Include customer tier (free/pro/enterprise) for accurate routing
- Mention specific errors or regions for infrastructure issues
"""
    console.print(Panel(help_text, title="Help", border_style="cyan"))


def display_result(result: TriageOutput):
    """Display triage result in a formatted way."""
    # Urgency color coding
    urgency_colors = {
        "critical": "red bold",
        "high": "yellow",
        "medium": "blue",
        "low": "green"
    }
    urgency_color = urgency_colors.get(result.urgency.value, "white")
    
    # Main result table
    table = Table(title="📋 Triage Result", show_header=False, border_style="cyan")
    table.add_column("Field", style="cyan", width=25)
    table.add_column("Value", style="white")
    
    table.add_row("Ticket ID", result.ticket_id)
    table.add_row("Urgency", f"[{urgency_color}]{result.urgency.value.upper()}[/{urgency_color}]")
    table.add_row("Issue Type", result.issue_type.value)
    table.add_row("Sentiment", result.customer_sentiment.value)
    table.add_row("Product", result.product or "Not detected")
    
    risk_str = ", ".join([s.value for s in result.customer_risk_signals]) or "None"
    table.add_row("Risk Signals", risk_str)
    
    table.add_row("", "")  # Spacer
    table.add_row("[bold]Recommended Action[/bold]", f"[bold]{result.recommended_action.value}[/bold]")
    table.add_row("Specialist Queue", result.recommended_specialist_queue.value)
    table.add_row("Confidence", f"{result.confidence_score:.0%}")
    
    console.print()
    console.print(table)
    
    # Knowledge base results
    if result.knowledge_base_results:
        console.print("\n[bold cyan]📚 Knowledge Base Results:[/bold cyan]")
        for kb in result.knowledge_base_results[:3]:
            console.print(f"  • [green]{kb.title}[/green] (relevance: {kb.relevance_score:.2f})")
            console.print(f"    [dim]{kb.url}[/dim]")
    
    # Tool calls
    if result.tool_calls:
        console.print("\n[bold cyan]🔧 Tools Used:[/bold cyan]")
        for call in result.tool_calls:
            status = "✅" if call.success else "❌"
            console.print(f"  {status} {call.tool_name}")
    
    # Suggested reply
    if result.suggested_reply:
        console.print("\n[bold cyan]💬 Suggested Reply:[/bold cyan]")
        console.print(Panel(result.suggested_reply, border_style="green"))
    
    # Reasoning
    if result.reasoning:
        console.print(f"\n[dim]💭 Reasoning: {result.reasoning}[/dim]")
    
    console.print()


def get_ticket_interactive() -> Optional[SupportTicket]:
    """Get ticket details interactively."""
    console.print("\n[bold cyan]📝 Create New Ticket[/bold cyan]\n")
    
    try:
        # Auto-generate ticket ID
        ticket_id = generate_ticket_id()
        console.print(f"[dim]Ticket ID: {ticket_id}[/dim]\n")
        
        subject = Prompt.ask("Subject")
        
        if not subject.strip():
            console.print("[red]Subject cannot be empty[/red]")
            return None
        
        console.print("Body (enter your message, press Enter twice to finish):")
        lines = []
        empty_count = 0
        while empty_count < 1:
            line = input()
            if line == "":
                empty_count += 1
            else:
                empty_count = 0
                lines.append(line)
        body = "\n".join(lines)
        
        if not body.strip():
            console.print("[red]Body cannot be empty[/red]")
            return None
        
        customer_email = Prompt.ask("Customer Email", default="customer@example.com")
        customer_name = Prompt.ask("Customer Name (optional)", default="")
        customer_tier = Prompt.ask(
            "Customer Tier",
            choices=["free", "pro", "enterprise", "unknown"],
            default="unknown"
        )
        customer_region = Prompt.ask(
            "Customer Region (optional)",
            default=""
        )
        
        return SupportTicket(
            ticket_id=ticket_id,
            subject=subject,
            body=body,
            customer_email=customer_email,
            customer_name=customer_name or None,
            customer_tier=customer_tier,
            customer_region=customer_region or None,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        return None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None


def get_ticket_quick() -> Optional[SupportTicket]:
    """Get ticket with minimal input."""
    console.print("\n[bold cyan]⚡ Quick Ticket Entry[/bold cyan]\n")
    
    try:
        # Auto-generate ticket ID
        ticket_id = generate_ticket_id()
        console.print(f"[dim]Ticket ID: {ticket_id}[/dim]\n")
        
        subject = Prompt.ask("Subject")
        if not subject.strip():
            console.print("[red]Subject cannot be empty[/red]")
            return None
        
        console.print("Body (enter message, press Enter twice to finish):")
        lines = []
        empty_count = 0
        while empty_count < 1:
            line = input()
            if line == "":
                empty_count += 1
            else:
                empty_count = 0
                lines.append(line)
        body = "\n".join(lines)
        
        if not body.strip():
            console.print("[red]Body cannot be empty[/red]")
            return None
        
        # Ask for tier as it affects routing
        customer_tier = Prompt.ask(
            "Customer Tier",
            choices=["free", "pro", "enterprise"],
            default="free"
        )
        
        return SupportTicket(
            ticket_id=ticket_id,
            subject=subject,
            body=body,
            customer_email="customer@example.com",
            customer_tier=customer_tier,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        return None


def get_ticket_json() -> Optional[SupportTicket]:
    """Get ticket from JSON input."""
    console.print("\n[bold cyan]📄 JSON Ticket Entry[/bold cyan]")
    console.print("[dim]Paste your JSON and press Enter twice:[/dim]\n")
    
    try:
        lines = []
        empty_count = 0
        while empty_count < 1:
            line = input()
            if line == "":
                empty_count += 1
            else:
                empty_count = 0
                lines.append(line)
        
        json_str = "\n".join(lines)
        data = json.loads(json_str)
        return SupportTicket.model_validate(data)
        
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        return None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None


def get_sample_ticket() -> SupportTicket:
    """Get a sample ticket for demo."""
    from src.triage_agent.models.ticket import SAMPLE_TICKETS
    
    console.print("\n[bold cyan]📦 Sample Tickets[/bold cyan]\n")
    
    for i, ticket in enumerate(SAMPLE_TICKETS, 1):
        console.print(f"  [{i}] {ticket.subject[:50]}... ({ticket.customer_tier})")
    
    choice = Prompt.ask(
        "\nSelect sample",
        choices=[str(i) for i in range(1, len(SAMPLE_TICKETS) + 1)],
        default="1"
    )
    
    return SAMPLE_TICKETS[int(choice) - 1]


def process_ticket(agent: TriageAgent, ticket: SupportTicket):
    """Process a ticket and display results."""
    console.print("\n[bold yellow]⏳ Processing ticket...[/bold yellow]")
    
    try:
        result = agent.triage(ticket)
        display_result(result)
        
        # Offer to show JSON
        if Confirm.ask("Show raw JSON output?", default=False):
            console.print("\n[bold cyan]Raw JSON:[/bold cyan]")
            console.print_json(result.model_dump_json())
            
    except Exception as e:
        console.print(f"[red]Error processing ticket: {e}[/red]")


def main():
    """Main chat loop."""
    # Initialize
    config = Config()
    setup_logging(config)
    agent = TriageAgent(config)
    
    display_welcome()
    
    if not config.is_api_key_set():
        console.print("[yellow]⚠️  OPENAI_API_KEY not set - using rule-based fallback[/yellow]")
        console.print("[dim]Set your API key in .env for full AI-powered triage[/dim]\n")
    
    # Main loop
    while True:
        try:
            command = Prompt.ask(
                "\n[bold green]>[/bold green]",
                default="help"
            ).strip().lower()
            
            if command in ["quit", "exit", "q"]:
                console.print("\n[blue]Goodbye! 👋[/blue]\n")
                break
                
            elif command in ["help", "h", "?"]:
                display_help()
                
            elif command in ["new", "n", "create"]:
                ticket = get_ticket_interactive()
                if ticket:
                    process_ticket(agent, ticket)
                    
            elif command in ["quick", "qk", "fast"]:
                ticket = get_ticket_quick()
                if ticket:
                    process_ticket(agent, ticket)
                    
            elif command in ["sample", "s", "demo"]:
                ticket = get_sample_ticket()
                process_ticket(agent, ticket)
                
            elif command in ["json", "j"]:
                ticket = get_ticket_json()
                if ticket:
                    process_ticket(agent, ticket)
                    
            else:
                console.print(f"[yellow]Unknown command: '{command}'[/yellow]")
                console.print("Type [green]'help'[/green] for available commands")
                
        except KeyboardInterrupt:
            console.print("\n[dim]Press Ctrl+C again or type 'quit' to exit[/dim]")
        except EOFError:
            break


if __name__ == "__main__":
    main()