from typing import Literal
from tenacity import retry, wait_exponential, stop_after_attempt
try:
    from google.adk.agents.context_cache_config import ContextCacheConfig
except ImportError:
    ContextCacheConfig = None
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from rich.console import Console
console = Console()

class EmailBridge:
    """
    Bridge to send Compete Pulse reports via Email.
    """

    def __init__(self, recipient: str, sender_email: str=None, sender_password: str=None, smtp_server: str='smtp.gmail.com', smtp_port: int=587):
        self.recipient = recipient
        self.sender_email = sender_email or os.environ.get('COMPETE_PULSE_SENDER_EMAIL')
        self.sender_password = sender_password or os.environ.get('COMPETE_PULSE_SENDER_PASSWORD')
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.context_cache = None
        if ContextCacheConfig:
            self.context_cache = ContextCacheConfig(ttl_seconds=3600)

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
    def post_report(self, knowledge: List[Dict[str, Any]], tldr: str=None, date_range: str=None, infographic_path: str=None, gaps: str=None):
        """
        Formats and sends the report via Email.
        """
        if not self.sender_email or not self.sender_password:
            console.print('[red]Error: Email credentials (CompetePulse_SENDER_EMAIL/CompetePulse_SENDER_PASSWORD) not set.[/red]')
            return
        if not knowledge:
            return
        try:
            msg = MIMEMultipart()
            msg['From'] = f'Compete Pulse Agent <{self.sender_email}>'
            msg['To'] = self.recipient
            subject = f'📡 Compete Pulse Pulse: {len(knowledge)} New Technical Updates'
            if date_range:
                subject += f' ({date_range})'
            msg['Subject'] = subject
            
            # Embed image if provided
            infographic_cid = None
            if infographic_path and os.path.exists(infographic_path):
                from email.mime.image import MIMEImage
                infographic_cid = 'infographic_image'
                with open(infographic_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-ID', f'<{infographic_cid}>')
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(infographic_path))
                    msg.attach(img)

            html_content = self._format_html_report(knowledge, tldr, date_range, infographic_cid=infographic_cid, gaps=gaps)
            msg.attach(MIMEText(html_content, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            console.print(f'[green]Successfully emailed report to {self.recipient}.[/green]')
        except Exception as e:
            console.print(f'[red]Failed to send email: {e}[/red]')
            raise e

    def _md_to_html(self, text: str) -> str:
        """
        Simple markdown to HTML converter for basic pulse elements.
        Handles bolding (**text**) and bullets (- or *).
        """
        import re
        # Bolding
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #0f172a;">\1</strong>', text)
        # Bullets
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                lines.append(f'<div style="margin-bottom: 8px; padding-left: 20px; position: relative;"><span style="position: absolute; left: 0; color: #6366f1;">•</span>{line[2:]}</div>')
            elif line:
                lines.append(f'<div style="margin-bottom: 8px;">{line}</div>')
        return '\n'.join(lines)

    def _format_html_report(self, knowledge: List[Dict[str, Any]], tldr: str=None, date_range: str=None, infographic_cid: str=None, gaps: str=None) -> str:
        # Group and rank by impact
        grouped_knowledge = {}
        for item in knowledge:
            source = item.get('source', 'General Update').replace('-', ' ').title()
            if source not in grouped_knowledge:
                grouped_knowledge[source] = []
            grouped_knowledge[source].append(item)

        # Sort sections by the highest impact score within them
        sorted_sources = sorted(
            grouped_knowledge.keys(),
            key=lambda s: max([item.get('impact_score', 0) for item in grouped_knowledge[s]]),
            reverse=True
        )

        # Designer Color Palette
        color_map = {
            'Gemini': '#6366f1',   # Indigo 500
            'Vertex': '#0ea5e9',   # Sky 500
            'Security': '#f43f5e', # Rose 500
            'Agent': '#10b981',    # Emerald 500
            'Infrastructure': '#64748b', # Slate 500
            'Search': '#f59e0b',   # Amber 500
            'Openai': '#10a37f',   # OpenAI Green
            'Anthropic': '#cc785c' # Anthropic Tan/Orange
        }

        # Table of Contents / Radar Section
        radar_items = []
        for s in sorted_sources:
            for item in grouped_knowledge[s]:
                if item.get('impact_score', 0) >= 70:
                    radar_items.append(item)
        
        radar_html = ''
        if radar_items:
            radar_links = ''
            for i, item in enumerate(radar_items[:6]):
                score_color = '#e11d48' if item.get('impact_score', 0) >= 90 else '#d97706'
                item_id = f"pulse-{i}"
                item['anchor_id'] = item_id
                radar_links += f'''
                <div style="margin-bottom: 10px;">
                    <a href="#{item_id}" style="text-decoration: none; color: #334155; display: flex; align-items: center; font-size: 0.9rem;">
                        <span style="color: {score_color}; font-weight: 800; font-family: monospace; margin-right: 12px; font-size: 0.8rem;">[{item.get('impact_score', 0)}]</span>
                        <span style="flex-grow: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 600;">{item['title']}</span>
                        <span style="color: #6366f1; font-weight: 800; margin-left: 8px;">&rarr;</span>
                    </a>
                </div>
                '''
            radar_html = f'''
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin-bottom: 32px;">
                <h2 style="margin: 0 0 16px 0; color: #1e293b; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">🛰️ Pulse Radar: High-Signal Updates</h2>
                {radar_links}
            </div>
            '''

        sections = ''
        for source in sorted_sources:
            items = grouped_knowledge[source]
            card_color = '#3b82f6' # Blue 500
            for key, val in color_map.items():
                if key.lower() in source.lower():
                    card_color = val
                    break

            sections += f'''
            <div style="margin-top: 48px; margin-bottom: 24px; border-left: 4px solid {card_color}; padding-left: 16px;">
                <h2 style="color: {card_color}; font-size: 1rem; text-transform: uppercase; font-weight: 800; letter-spacing: 0.1em; margin: 0;">
                    {source}
                </h2>
            </div>
            '''
            for item in items:
                bridge = item.get('bridge', 'Strategizing field alignment...')
                tags_html = ''
                item_tags = item.get('tags', [])
                
                # Priority Logic
                p_bg, p_fg, p_label = '#f1f5f9', '#64748b', 'Standard'
                impact_score = item.get('impact_score', 0)
                
                if impact_score >= 90:
                    p_bg, p_fg, p_label = '#fff1f2', '#e11d48', 'Mission Critical'
                elif impact_score >= 70:
                    p_bg, p_fg, p_label = '#fffbeb', '#d97706', 'High Impact'
                elif any(x in str(item_tags) for x in ['Security', 'Governance']):
                    p_bg, p_fg, p_label = '#fff1f2', '#e11d48', 'Security Critical'

                for t in item_tags:
                    tags_html += f'<span style="background-color: #f8fafc; color: #475569; padding: 2px 8px; border-radius: 9999px; font-size: 10px; margin-right: 4px; font-weight: 600; text-transform: uppercase; border: 1px solid #e2e8f0;">{t}</span>'

                summary_html = self._md_to_html(item.get('summary', 'Technical analysis in progress.'))
                score_badge = f'<span style="margin-left: 8px; background-color: #f1f5f9; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 9px; font-family: monospace; font-weight: 700; border: 1px solid #e2e8f0;">INTEL SCORE: {impact_score}</span>'
                item_id = item.get('anchor_id', '')

                sections += f'''
                <div id="{item_id}" style="margin-bottom: 32px; background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                    <div style="padding: 24px;">
                        <div style="margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
                             <div style="display: flex; align-items: center;">
                                <span style="font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: {p_fg}; background-color: {p_bg}; padding: 2px 8px; border-radius: 4px;">{p_label}</span>
                                {score_badge}
                             </div>
                             <div style="display: flex;">{tags_html}</div>
                        </div>
                        <h3 style="margin: 0 0 16px 0; color: #0f172a; font-size: 1.15rem; font-weight: 700; line-height: 1.3;">{item['title']}</h3>
                        
                        <div style="background-color: #f8fafc; padding: 18px; border-radius: 8px; margin-bottom: 24px; border-left: 4px solid {card_color}; shadow: inset 0 2px 4px 0 rgba(0,0,0,0.02);">
                             <p style="margin: 0; color: #1e293b; font-size: 0.95rem; font-weight: 600; line-height: 1.6;">{bridge}</p>
                        </div>

                        <div style="color: #475569; font-size: 0.9rem; line-height: 1.7; margin-bottom: 24px;">
                            {summary_html}
                        </div>

                        <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 16px; border-top: 1px solid #f1f5f9;">
                            <a href="{item.get('source_url', '#')}" style="font-size: 0.8rem; font-weight: 800; color: {card_color}; text-decoration: none; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center;">
                                Engineering Docs 
                                <span style="margin-left: 6px; font-size: 1.1rem;">&rarr;</span>
                            </a>
                            <span style="font-size: 11px; color: #94a3b8; font-weight: 600;">PUBLISHED: {item.get('date', '')[:10]}</span>
                        </div>
                    </div>
                </div>
                '''

        infographic_sec = f'''
        <div style="margin-bottom: 40px; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; background-color: #f8fafc; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="padding: 14px 24px; border-bottom: 1px solid #e2e8f0; background-color: #ffffff; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 18px; margin-right: 10px;">📊</span>
                    <span style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: #475569;">Field Intelligence Visualization</span>
                </div>
                <span style="font-size: 10px; font-weight: 700; color: #94a3b8;">v2.5 Hybrid Engine</span>
            </div>
            <img src="cid:{infographic_cid}" alt="Strategic Synthesis" style="width: 100%; display: block; max-height: 600px; object-fit: contain;">
        </div>
        ''' if infographic_cid else ''

        tldr_sec = f'''
        <div style="background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%); border: 1px solid #fde68a; padding: 28px; border-radius: 12px; margin-bottom: 40px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <div style="background-color: #fcd34d; width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-right: 16px;">
                    <span style="font-size: 20px;">🎯</span>
                </div>
                <h2 style="margin: 0; color: #92400e; font-size: 1.1rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">Executive Synthesis</h2>
            </div>
            <p style="margin: 0; color: #78350f; font-weight: 500; line-height: 1.7; font-size: 1.05rem; font-style: italic;">{tldr}</p>
        </div>
        ''' if tldr else ''

        gaps_html = self._md_to_html(gaps) if gaps else ''
        gaps_sec = f'''
        <div style="background: linear-gradient(135deg, #fdf2f2 0%, #fee2e2 100%); border: 1px solid #fecaca; padding: 28px; border-radius: 12px; margin-bottom: 40px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <div style="background-color: #fca5a5; width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-right: 16px;">
                    <span style="font-size: 20px;">🛡️</span>
                </div>
                <h2 style="margin: 0; color: #991b1b; font-size: 1.1rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">Strategic Battlecard: Gaps & Advantages</h2>
            </div>
            <div style="margin: 0; color: #7f1d1d; font-weight: 600; line-height: 1.7; font-size: 0.95rem;">
                {gaps_html}
            </div>
        </div>
        ''' if gaps else ''

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Compete Pulse Field Pulse</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');
                body {{ font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f1f5f9; color: #334155; }}
            </style>
        </head>
        <body>
            <div style="max-width: 800px; margin: 0 auto; background-color: #f8fafc;">
                <header style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); padding: 48px 32px; text-align: left; border-radius: 0 0 24px 24px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);">
                    <div style="display: flex; align-items: center; margin-bottom: 16px;">
                        <span style="background-color: #6366f1; color: white; padding: 4px 12px; border-radius: 6px; font-weight: 800; font-size: 12px; letter-spacing: 0.1em;">FIELD PROMOTION</span>
                        <span style="color: #94a3b8; font-size: 12px; font-weight: 600; margin-left: auto;">{date_range}</span>
                    </div>
                    <h1 style="color: #ffffff; font-size: 2.5rem; font-weight: 800; margin: 0; letter-spacing: -0.02em;">Compete Pulse Pulse</h1>
                    <p style="color: #c7d2fe; font-size: 1.1rem; margin: 12px 0 0 0; font-weight: 500; opacity: 0.9;">Technical Roadmap Intel for Field Architects</p>
                </header>

                <main style="padding: 40px 24px;">
                    {tldr_sec}
                    {radar_html}
                    {infographic_sec}
                    {gaps_sec}
                    
                    <div style="font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.2em; color: #94a3b8; margin-bottom: 24px; display: flex; align-items: center;">
                        <span style="flex-grow: 1; height: 1px; background-color: #e2e8f0; margin-right: 16px;"></span>
                        Technical Roadmap Deep-Dive
                        <span style="flex-grow: 1; height: 1px; background-color: #e2e8f0; margin-left: 16px;"></span>
                    </div>
                    
                    {sections}
                </main>

                <footer style="background-color: #ffffff; padding: 40px 32px; border-top: 1px solid #e2e8f0; text-align: center;">
                    <div style="margin-bottom: 24px;">
                        <span style="font-size: 24px;">🚀</span>
                    </div>
                    <p style="margin: 0; color: #64748b; font-size: 0.9rem; font-weight: 600;">Synthesized by Compete Pulse Agent v0.1.2</p>
                    <p style="margin: 4px 0 24px 0; color: #94a3b8; font-size: 0.8rem; font-weight: 500;">Powered by **Gemini 2.5 Pro & Flash** Hybrid Engine</p>
                    
                    <div style="background-color: #fff1f2; color: #e11d48; padding: 12px 24px; border-radius: 8px; display: inline-block; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; border: 1px solid #fecaca;">
                        Google Cloud Confidential • Internal Use Only
                    </div>
                </footer>
            </div>
        </body>
        </html>
        """