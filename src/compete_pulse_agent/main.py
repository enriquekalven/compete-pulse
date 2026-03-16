from tenacity import retry, wait_exponential, stop_after_attempt
import typer
import os
from typing import Optional, List
from .core.agent import CompetePulseAgent
from .core.chat_bridge import GoogleChatBridge
from .core.email_bridge import EmailBridge
from .core.github_bridge import GitHubBridge
app = typer.Typer(help='Compete Pulse Agent: Browsing and Promoting AI Knowledge')

@app.command()
def report(days: int=typer.Option(1, '--days', '-d', help='Number of days to look back'), 
           project: str = typer.Option("project-maui", "--project", help="GCP Project ID"),
           infographic: bool = typer.Option(False, "--infographic", help="Generate a visual pulse infographic")):
    """Generate the AI Field Promotion Report locally."""
    agent = CompetePulseAgent(project_id=project)
    knowledge = agent.browse_knowledge()
    from .core.agent import parse_date
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    filtered = [item for item in knowledge if parse_date(item.get('date', '')) >= cutoff]
    synthesized = agent.synthesize_reports(filtered)
    
    if infographic:
        agent.generate_infographic(synthesized)
        
    agent.promote_learnings(synthesized, days=days)

@app.command()
def chat(webhook_url: str=typer.Option(None, '--webhook-url', envvar='GCHAT_WEBHOOK_URL', help='Google Chat Webhook URL'), days: int=typer.Option(1, '--days', '-d', help='Number of days to look back'), project: str = typer.Option("project-maui", "--project", help="GCP Project ID")):
    """Scan and post the report to Google Chat."""
    if not webhook_url:
        typer.echo('Error: Webhook URL must be provided via --webhook-url or GCHAT_WEBHOOK_URL env var.')
        raise typer.Exit(code=1)
    agent = CompetePulseAgent(project_id=project)
    knowledge = agent.browse_knowledge()
    from .core.agent import parse_date
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    filtered = [item for item in knowledge if parse_date(item.get('date', '')) >= cutoff]
    synthesized = agent.synthesize_reports(filtered)
    bridge = GoogleChatBridge(webhook_url)
    bridge.post_report(synthesized.get('items', []))

@app.command()
def email(recipient: str=typer.Argument(..., help='Recipient email address'), 
          sender: str=typer.Option(None, '--sender', envvar='COMPETE_PULSE_SENDER_EMAIL', help='Sender email address'), 
          password: str=typer.Option(None, '--password', envvar='COMPETE_PULSE_SENDER_PASSWORD', help='Sender email password/token'), 
          days: int=typer.Option(1, '--days', '-d', help='Number of days to look back'), 
          project: str = typer.Option("project-maui", "--project", help="GCP Project ID"),
          infographic: bool = typer.Option(False, "--infographic", help="Generate and embed a visual pulse infographic")):
    """Scan and send the report via Email."""
    agent = CompetePulseAgent(project_id=project)
    knowledge = agent.browse_knowledge()
    from .core.agent import parse_date
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    filtered = [item for item in knowledge if parse_date(item.get('date', '')) >= cutoff]
    synthesized = agent.synthesize_reports(filtered)
    
    infographic_path = None
    if infographic:
        infographic_path = agent.generate_infographic(synthesized)
        
    start_date = cutoff.strftime('%Y-%m-%d')
    end_date = now.strftime('%Y-%m-%d')
    date_range = f'{start_date} to {end_date}'
    bridge = EmailBridge(recipient, sender, password)
    bridge.post_report(synthesized.get('items', []), tldr=synthesized.get('tldr'), date_range=date_range, infographic_path=infographic_path, gaps=synthesized.get('gaps'))

@app.command()
def github(days: int=typer.Option(1, '--days', '-d', help='Number of days to look back'), project: str = typer.Option("project-maui", "--project", help="GCP Project ID")):
    """Dispatch the AI Field Promotion Report as a GitHub Issue."""
    agent = CompetePulseAgent(project_id=project)
    knowledge = agent.browse_knowledge()
    from .core.agent import parse_date
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    filtered = [item for item in knowledge if parse_date(item.get('date', '')) >= cutoff]
    synthesized = agent.synthesize_reports(filtered)
    start_date = cutoff.strftime('%Y-%m-%d')
    end_date = now.strftime('%Y-%m-%d')
    date_range = f'{start_date} to {end_date}'
    bridge = GitHubBridge()
    bridge.post_report(synthesized.get('items', []), tldr=synthesized.get('tldr'), date_range=date_range, gaps=synthesized.get('gaps'))

@app.command()
def query(text: str = typer.Argument(..., help="Text to search for in the knowledge base"), project: str = typer.Option("project-maui", "--project", help="GCP Project ID")):
    """Query the persistent knowledge base (RAG)."""
    agent = CompetePulseAgent(project_id=project)
    results = agent.query_knowledge(text)
    if not results:
        typer.echo("No relevant pulses found.")
        return
    
    from rich.console import Console
    from rich.table import Table
    console = Console()
    table = Table(title=f"RAG Results for: {text}")
    table.add_column("Score", justify="right", style="cyan")
    table.add_column("Source", style="magenta")
    table.add_column("Pulse", style="green")
    
    for r in results:
        # Distance is used as score (lower is better for cosine distance in some libs, but metadata/distance depends on chroma config)
        table.add_row(f"{r['distance']:.4f}", r['metadata']['source'], r['document'][:200] + "...")
    
    console.print(table)

@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000):
    """Launch the AI Agent FastAPI service."""
    import uvicorn
    typer.echo(f"🚀 Starting Compete Pulse Agent API on {host}:{port}")
    uvicorn.run("compete_pulse_agent.core.api:app", host=host, port=port, reload=True)

@app.command()
def ingest(uris: List[str] = typer.Argument(..., help="List of Google Drive URLs or GCS URIs to ingest"), project: str = typer.Option("project-maui", "--project", help="GCP Project ID")):
    """Ingest Workspace documents (Slides, Docs, Sheets) link by link or folder by folder."""
    agent = CompetePulseAgent(project_id=project)
    agent.ingest_documents(uris)
    typer.echo(f"🚀 Ingestion request submitted for {len(uris)} sources. Documents are being processed by Vertex AI RAG Engine.")

@app.command()
def audit_maturity(package: str = typer.Argument(..., help="PyPI package name to audit"), project: str = typer.Option("project-maui", "--project", help="GCP Project ID")):
    """Perform a deep audit of a package's history and maturity (Initial Deep Ingestion)."""
    agent = CompetePulseAgent(project_id=project)
    wisdom = agent.audit_maturity(package)
    if "wisdom" in wisdom:
        from rich.console import Console
        from rich.panel import Panel
        from rich.markdown import Markdown
        console = Console()
        console.print(Panel(Markdown(wisdom["wisdom"]), title=f"🧠 CompetePulse WISDOM: {package}", border_style="magenta"))

@app.command()
def response(competitor_product: str = typer.Argument(..., help="Competitor product name to analyze (e.g. 'Claude CoWork')"), 
             target: str = typer.Option("Gemini Enterprise", "--target", "-t", help="Google product to compare against (e.g. 'Agent Builder', 'ADK')"),
             project: str = typer.Option("project-maui", "--project", help="GCP Project ID"),
             raw: bool = typer.Option(False, "--raw", help="Output raw markdown instead of rich rendered text")):
    """Generate a 'Rapid Response' battlecard for a specific competitor product."""
    agent = CompetePulseAgent(project_id=project)
    response_markdown = agent.generate_rapid_response(competitor_product, google_product=target)
    
    if raw:
        print(response_markdown)
    else:
        from rich.console import Console
        from rich.markdown import Markdown
        console = Console()
        console.print(Markdown(response_markdown))

@app.command()
def version():
    """Show version."""
    typer.echo('Compete Pulse Agent v0.1.0 (ADK Powered)')
if __name__ == '__main__':
    app()