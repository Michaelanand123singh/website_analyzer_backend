import re
from urllib.parse import urljoin, urlparse

def clean_text(text):
    """Clean and normalize scraped text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:-]', '', text)
    
    return text.strip()

def extract_domain(url):
    """Extract domain from URL"""
    return urlparse(url).netloc

def is_valid_url(url):
    """Basic URL validation"""
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return pattern.match(url) is not None

def truncate_text(text, max_length=1000):
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."