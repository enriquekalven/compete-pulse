from tenacity import retry, wait_exponential, stop_after_attempt
import requests
import json
from typing import List, Dict, Any
from rich.console import Console
console = Console()

class GoogleChatBridge:
    """
    Bridge to send updates to Google Chat via Webhooks.
    """

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
    def post_report(self, knowledge: List[Dict[str, Any]]):
        """
        Formats and posts the report to Google Chat.
        """
        if not self.webhook_url:
            console.print('[red]Error: Google Chat Webhook URL not configured.[/red]')
            return
        if not knowledge:
            return
        cards = []
        roadmap_items = [k for k in knowledge if k['category'] == 'roadmap' or 'release' in k['source']]
        if roadmap_items:
            sections = []
            for item in roadmap_items[:3]:
                sections.append({'header': f"🗺️ {item['source'].upper()}: {item['title']}", 'widgets': [{'textParagraph': {'text': item.get('bridge', 'New tech detected.')}}, {'buttons': [{'textButton': {'text': 'OPEN DOCS', 'onClick': {'openLink': {'url': item.get('source_url', 'https://cloud.google.com/vertex-ai/docs/release-notes')}}}}]}]})
            cards.append({'header': {'title': 'Compete Pulse AGENT: ROADMAP BRIDGE', 'subtitle': 'Actionable Field Intel', 'imageUrl': 'https://fonts.gstatic.com/s/i/short-term/release/googleg/bolt/default/24px.svg'}, 'sections': sections})
        trend_items = [k for k in knowledge if k['category'] != 'roadmap']
        if trend_items:
            trend_sections = []
            for item in trend_items[:3]:
                trend_sections.append({'header': f"💡 {item['title']}", 'widgets': [{'textParagraph': {'text': item.get('summary', '')[:200] + '...'}}, {'buttons': [{'textButton': {'text': 'READ MORE', 'onClick': {'openLink': {'url': item.get('source_url', '#')}}}}]}]})
            cards.append({'header': {'title': 'AI KNOWLEDGE & TRENDS', 'subtitle': 'Market Pulse'}, 'sections': trend_sections})
        message = {'cards': cards}
        try:
            response = requests.post(self.webhook_url, json=message, timeout=10)
            response.raise_for_status()
            console.print('[green]Successfully posted report to Google Chat.[/green]')
        except Exception as e:
            console.print(f'[red]Failed to post to Google Chat: {e}[/red]')
            raise e