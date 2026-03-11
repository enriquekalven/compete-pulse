from typing import Literal
from tenacity import retry, wait_exponential, stop_after_attempt
import os
import requests
from datetime import datetime
from typing import List, Dict, Any
from rich.console import Console
console = Console()

class GitHubBridge:
    """
    Bridge to post Compete Pulse reports as GitHub Issues.
    This provides an automated notification channel without requiring email credentials.
    """

    def __init__(self, repo: str=None, token: str=None):
        self.repo = repo or os.environ.get('GITHUB_REPOSITORY')
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.api_url = f'https://api.github.com/repos/{self.repo}/issues'

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
    def post_report(self, knowledge: List[Dict[str, Any]], tldr: str=None, date_range: str=None, gaps: str=None):
        """
        Posts the synthesized report as a new GitHub Issue.
        """
        if not self.repo or not self.token:
            console.print('[yellow]Skipping GitHub Issue: GITHUB_TOKEN or GITHUB_REPOSITORY not set.[/yellow]')
            return
        if not knowledge:
            return
        date_suffix = f' ({date_range})' if date_range else ''
        title = f'🚀 Compete Pulse Pulse: {len(knowledge)} New Updates{date_suffix}'
        body = self._format_markdown_report(knowledge, tldr, date_range, gaps)
        try:
            response = requests.post(self.api_url, headers={'Authorization': f'token {self.token}', 'Accept': 'application/vnd.github.v3+json'}, json={'title': title, 'body': body, 'labels': ['pulse', 'automated']}, timeout=15)
            response.raise_for_status()
            console.print(f"[green]Successfully posted report to GitHub Issues: {response.json().get('html_url')}[/green]")
        except Exception as e:
            console.print(f'[red]Failed to post to GitHub: {e}[/red]')
            raise e # Re-raise for retry

    def _format_markdown_report(self, knowledge: List[Dict[str, Any]], tldr: str=None, date_range: str=None, gaps: str=None) -> str:
        report = '# 🚀 Compete Pulse Field Pulse\n'
        if date_range:
            report += f'**Pulse Period:** {date_range}\n\n'
        report += f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} PST\n\n"
        report += '---\n\n'
        report += '## 🎯 Executive Synthesis\n'
        if tldr:
            report += f'> {tldr}\n\n'
        else:
            report += 'Review industry trends and roadmap shifts below for market context.\n\n'
        
        if gaps:
            report += '## 🛡️ Strategic Battlecard: Gaps & Advantages\n'
            report += f'{gaps}\n\n'

        report += '---\n\n'
        grouped_knowledge = {}
        for item in knowledge:
            source = item.get('source', 'General Update').replace('-', ' ').title()
            if source not in grouped_knowledge:
                grouped_knowledge[source] = []
            grouped_knowledge[source].append(item)
        report += '## 🗺️ Service & Roadmap Updates\n'
        report += '*Grouped by Knowledge Stream*\n\n'
        for source, items in grouped_knowledge.items():
            report += f'### 📦 {source}\n'
            for item in items:
                tags_str = ' '.join([f'`{t}`' for t in item.get('tags', [])])
                bridge = item.get('bridge', 'New tech detected. Review impacts on developer velocity.')
                report += f"#### {item['title']} {tags_str}\n"
                report += f'**🚀 Field Impact:** {bridge}\n\n'
                report += f"{item.get('summary', '')}\n\n"
                report += f"**[🔗 Open Documentation]({item.get('source_url', '#')})**\n\n"
            report += '---\n'
        report += '\n\n**Note:** This report is synthesized by the **Compete Pulse Agent** based on live documentation and release feeds.\n'
        return report