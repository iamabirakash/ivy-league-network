import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters
    text = re.sub(r'[^\w\s\-.,;:!?()]', '', text)
    return text.strip()


def extract_email(text):
    """Extract email from text"""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None


def extract_phone(text):
    """Extract phone number from text"""
    phone_pattern = r'(\+?\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}'
    matches = re.findall(phone_pattern, text)
    return matches[0] if matches else None


def parse_date_range(text):
    """Parse date range like 'June 1-15, 2024'"""
    patterns = [
        r'(\w+)\s+(\d+)-(\d+),\s+(\d{4})',  # June 1-15, 2024
        r'(\w+)\s+(\d+)\s+-\s+(\w+)\s+(\d+),\s+(\d{4})',  # June 1 - July 15, 2024
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # Parse based on pattern
            return match.groups()
    
    return None


def normalize_url(url, base_url):
    """Normalize relative URLs to absolute"""
    if not url:
        return None
    
    if url.startswith('http'):
        return url
    elif url.startswith('//'):
        return f"https:{url}"
    elif url.startswith('/'):
        # Remove trailing slash from base_url if present
        base = base_url.rstrip('/')
        return f"{base}{url}"
    else:
        return f"{base_url}/{url}"