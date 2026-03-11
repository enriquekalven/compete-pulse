from tenacity import retry, wait_exponential, stop_after_attempt
import urllib.request
import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Optional
from datetime import datetime, timezone
import os

def clean_version(v_str: str) -> str:
    match = re.search('(\\d+\\.\\d+(?:\\.\\d+)?(?:[a-zA-Z]+\\d+)?)', v_str)
    if match:
        return match.group(1)
    return v_str.strip().lstrip('v')

def parse_html_date(date_str: str) -> Optional[datetime]:
    """Parses dates like 'February 06, 2026' or 'Feb 06, 2026'."""
    formats = ["%B %d, %Y", "%b %d, %Y"]
    clean_date = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str).strip()
    for fmt in formats:
        try:
            return datetime.strptime(clean_date, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def fetch_recent_updates(url: str, max_items: int = 5) -> List[Dict[str, str]]:
    """
    Fetches the most recent updates from an Atom, RSS, or HTML page.
    """
    # Detect Feed URLs (Atom, RSS, XML)
    if any(ext in url.lower() for ext in ['.xml', '.atom', '.rss', '/rss', '/feed']):
        try:
            items = _fetch_from_feed(url, max_items)
            if items:
                return items
        except Exception:
            pass
    
    # Fallback to HTML if RSS fails or if it's an HTML page
    return _fetch_from_html(url, max_items)

def _fetch_from_feed(url: str, max_items: int = 5) -> List[Dict[str, str]]:
    updates = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            tree = ET.parse(response)
            root = tree.getroot()
            ns_match = re.match(r'\{(.*)\}', root.tag)
            ns = {'ns': ns_match.group(1)} if ns_match else {}
            
            def find_nodes(parent, tag):
                if not ns: return parent.findall(tag)
                return parent.findall(f'ns:{tag}', ns)

            def find_node(parent, tag):
                if not ns: return parent.find(tag)
                return parent.find(f'ns:{tag}', ns)

            # Check if it's Atom
            entries = find_nodes(root, 'entry')
            if entries:
                for entry in entries[:max_items]:
                    title_node = find_node(entry, 'title')
                    updated_node = find_node(entry, 'updated')
                    content_node = find_node(entry, 'content') or find_node(entry, 'summary')
                    link_node = find_node(entry, 'link')

                    title = title_node.text if title_node is not None else "Untitled Update"
                    updated = updated_node.text if updated_node is not None else "N/A"
                    summary = "".join(content_node.itertext()).strip()[:500] if content_node is not None else ""
                    source_url = link_node.get('href', url) if link_node is not None else url

                    updates.append({
                        'version': "N/A",
                        'date': updated,
                        'title': title,
                        'summary': summary,
                        'source_url': source_url,
                        'source': url # Added source field
                    })
                return updates
            
            # Check if it's RSS
            channel = root.find('channel')
            if channel is not None:
                items = channel.findall('item')
                for item in items[:max_items]:
                    title = item.find('title').text if item.find('title') is not None else "Untitled"
                    date = item.find('pubDate').text if item.find('pubDate') is not None else "N/A"
                    summary = item.find('description').text if item.find('description') is not None else ""
                    summary = re.sub('<[^>]+>', '', summary).strip()[:500]
                    link = item.find('link').text if item.find('link') is not None else url
                    
                    updates.append({
                        'title': title,
                        'date': date,
                        'summary': summary,
                        'source_url': link,
                        'version': "N/A"
                    })
                return updates
    except Exception:
        pass
    return []

def _fetch_from_html(url: str, max_items: int = 5) -> List[Dict[str, str]]:
    updates = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8')
            
            # Identify date headers or meta dates
            date_pattern = r'([A-Z][a-z]+\s+\d{1,2},\s+\d{4})'
            
            # SIGNAL DETECTION PASS: Look for high-value product launches even if structural parsing fails
            high_value_signals = ['Gemini 3.1', 'Gemini 3', 'Claude 3.5 Sonnet', 'Vertex AI Agent Builder']
            for signal in high_value_signals:
                if signal.lower() in content.lower() and not any(signal.lower() in u['title'].lower() for u in updates):
                    # Try to extract a title from around the signal
                    signal_match = re.search(f'[^.>?!"\']*{re.escape(signal)}[^.>?!"\']*', content, re.IGNORECASE)
                    if signal_match:
                        updates.append({
                            'title': signal_match.group(0).strip()[:100],
                            'date': datetime.now(timezone.utc).isoformat(),
                            'summary': f"Significant roadmap signal detected: {signal}. Analysis suggests high field impact.",
                            'source_url': url,
                            'version': "Signal detected"
                        })

            # Standard heuristic for other articles
            all_dates = []
            for m in re.finditer(date_pattern, content):
                date_str = m.group(1)
                dt = parse_html_date(date_str)
                if dt: all_dates.append((dt, m.start()))
            
            for dt, pos in all_dates:
                # Look for a title nearby (usually before the date in modern HTML search/lists)
                nearby_content = content[max(0, pos-1000):pos+500]
                possible_titles = re.findall(r'<a[^>]*>(.*?)</a>', nearby_content, flags=re.DOTALL)
                if possible_titles:
                    title = re.sub(r'<[^>]+>', '', possible_titles[-1]).strip()
                else:
                    # Fallback: find first non-empty line after date in text
                    block = content[pos:pos+500]
                    clean_block = re.sub(r'<[^>]+>', '\n', block)
                    lines = [l.strip() for l in clean_block.split('\n') if l.strip()]
                    # Skip the date itself if it caught it
                    if lines and any(x in lines[0] for x in ['February', 'January', 'March']): # crude date check
                        lines = lines[1:]
                    title = lines[0] if lines else "Update"

                if len(title) > 10 and title not in [u['title'] for u in updates]:
                    updates.append({
                        'title': title,
                        'date': dt.isoformat(),
                        'summary': "Strategic update found on industry pulse feed.",
                        'source_url': url,
                        'version': "N/A"
                    })
                if len(updates) >= max_items: break
        return updates
    except Exception:
        return []

def fetch_latest_from_atom(url: str) -> Optional[Dict[str, str]]:
    updates = fetch_recent_updates(url, max_items=1)
    return updates[0] if updates else None
