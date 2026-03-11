import re

def scrub_pii(text: str) -> str:
    """
    Scrubs PII from the given text to prevent data exfiltration.
    Matches emails and potential phone numbers.
    """
    if not text:
        return text
    
    # Redact Emails
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', text)
    
    # Redact potential US Phone Numbers (Improved for robustness)
    text = re.sub(r'(?:\b|\+1[-. ]?)\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b', '[PHONE_REDACTED]', text)
    
    return text
