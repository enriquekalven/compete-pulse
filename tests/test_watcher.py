from tenacity import retry, wait_exponential, stop_after_attempt
import pytest
from compete_pulse_agent.core.watcher import fetch_recent_updates, clean_version
from unittest.mock import MagicMock, patch

def test_clean_version():
    assert clean_version('v1.2.3') == '1.2.3'
    assert clean_version('Release 1.24.0') == '1.24.0'
    assert clean_version('Version 2.0') == '2.0'
    assert clean_version('no version here') == 'no version here'

@patch('urllib.request.urlopen')
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def test_fetch_from_feed_atom(mock_urlopen):
    import io
    atom_xml = b'<?xml version="1.0" encoding="UTF-8"?>\n    <feed xmlns="http://www.w3.org/2005/Atom">\n      <entry>\n        <title>Test Update 1</title>\n        <updated>2026-02-06T12:00:00Z</updated>\n        <link href="https://example.com/1" />\n        <summary>Summary 1</summary>\n      </entry>\n      <entry>\n        <title>Test Update 2</title>\n        <updated>2026-02-05T12:00:00Z</updated>\n        <link href="https://example.com/2" />\n        <summary>Summary 2</summary>\n      </entry>\n    </feed>\n    '
    mock_response = io.BytesIO(atom_xml)
    mock_response.getcode = MagicMock(return_value=200)
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=None)
    mock_urlopen.return_value = mock_response
    updates = fetch_recent_updates('https://example.com/feed.atom', max_items=2)
    assert len(updates) == 2
    assert updates[0]['title'] == 'Test Update 1'
    assert updates[1]['title'] == 'Test Update 2'
    assert updates[0]['source_url'] == 'https://example.com/1'

@patch('urllib.request.urlopen')
@retry(wait=wait_exponential(multiplier=1, min=2, max=5), stop=stop_after_attempt(3))
def test_fetch_from_html(mock_urlopen):
    html_content = b'\n    <html>\n      <body>\n        <h3>Mar 6, 2026</h3>\n        <p><a href="https://example.com/item1">Feature: New AI Agent</a></p>\n        <p>This is a detailed summary for the new agent.</p>\n        <h3>March 5, 2026</h3>\n        <p><a href="https://example.com/item2">Announcement: Security fix</a></p>\n      </body>\n    </html>\n    '
    mock_response = MagicMock()
    mock_response.read.return_value = html_content
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response
    updates = fetch_recent_updates('https://docs.cloud.google.com/test-notes', max_items=2)
    assert len(updates) >= 1
    assert 'New AI Agent' in updates[0]['title']
    assert '2026-03-06' in updates[0]['date']

@patch('urllib.request.urlopen')
def test_fetch_from_html_signal_detection(mock_urlopen):
    # Test that 'Gemini 3.1' is caught by the logic when accompanied by a date
    html_content = b'<html><body><h3>March 10, 2026</h3><h5>Introducing Gemini 3.1 Pro on Google Cloud</h5><p>More technical details here.</p></body></html>'
    mock_response = MagicMock()
    mock_response.read.return_value = html_content
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response
    
    updates = fetch_recent_updates('https://cloud.google.com/blog/test', max_items=5)
    assert any('Gemini 3.1' in u['title'] for u in updates)
    assert any('2026-03-10' in u['date'] for u in updates)