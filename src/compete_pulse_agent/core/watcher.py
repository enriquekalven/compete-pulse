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
    """Parses dates like 'February 06, 2026', 'Feb 06, 2026', or ranges like 'Mar 2 - Mar 6'."""
    # Handle ranges: take the end of the range
    if ' - ' in date_str:
        date_str = date_str.split(' - ')[-1]
    
    # Common month names
    months = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
    
    # Try to extract month, day, and optional year
    match = re.search(f'({months})\\s+(\\d{{1,2}})(?:,\\s+(\\d{{4}}))?', date_str, re.IGNORECASE)
    if not match:
        return None
    
    month_name = match.group(1)[:3].title()
    day = match.group(3)
    year = match.group(4) or str(datetime.now().year)
    
    try:
        dt_str = f"{month_name} {day}, {year}"
        return datetime.strptime(dt_str, "%b %d, %Y").replace(tzinfo=timezone.utc)
    except Exception:
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
            
            # Improved pattern to catch 'Mar 2 - Mar 6' or 'March 15, 2026'
            date_pattern = r'([A-Z][a-z]+\s+\d{1,2}(?:\s*-\s*[A-Z][a-z]+\s+\d{1,2})?(?:,\s+\d{4})?)'
            
            # Extract dates and their positions
            all_dates = []
            for m in re.finditer(date_pattern, content):
                date_str = m.group(1)
                dt = parse_html_date(date_str)
                if dt: 
                    all_dates.append((dt, m.start(), m.end()))
            
            all_dates.sort(key=lambda x: x[1])

            for i, (dt, start_pos, end_pos) in enumerate(all_dates):
                # The content for this date is between this date and the next date
                next_pos = all_dates[i+1][1] if i + 1 < len(all_dates) else len(content)
                section_content = content[end_pos:next_pos]
                
                # Split section into potential update fragments (e.g. by bullet points or headers)
                # We try to keep paragraphs together if they belong to the same update
                fragments = re.split(r'<(?:h\d|li)[^>]*>', section_content)
                for frag in fragments:
                    clean_frag = re.sub(r'<[^>]+>', ' ', frag).strip()
                    if len(clean_frag) < 20: continue
                    
                    # Extract title: first link text or first line
                    link_match = re.search(r'<a[^>]*>(.*?)</a>', frag, flags=re.DOTALL)
                    if link_match:
                        title = re.sub(r'<[^>]+>', ' ', link_match.group(1)).strip()
                        summary = clean_frag.replace(title, '', 1).strip()[:500]
                    else:
                        lines = [l.strip() for l in clean_frag.split('\n') if l.strip()]
                        title = lines[0] if lines else "Update"
                        summary = "\n".join(lines[1:])[:500]
                    
                    if len(title) > 10 and title not in [u['title'] for u in updates]:
                        if not summary: summary = "Strategic update found on industry pulse feed."
                        
                        updates.append({
                            'title': title,
                            'date': dt.isoformat(),
                            'summary': summary,
                            'source_url': url,
                            'version': "N/A"
                        })
                    
                    if len(updates) >= max_items * 3: break
                if len(updates) >= max_items * 3: break
        
        updates.sort(key=lambda x: x['date'], reverse=True)
        return updates[:max_items]
    except Exception:
        return []

def fetch_latest_from_atom(url: str) -> Optional[Dict[str, str]]:
    updates = fetch_recent_updates(url, max_items=1)
    return updates[0] if updates else None
