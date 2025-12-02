"""
URL validation for YouTube links.
"""
import re
from typing import Optional, List

# YouTube URL patterns
YOUTUBE_PATTERNS = [
    # Standard youtube.com URLs
    r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
    r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})',
    r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    # Short youtu.be URLs
    r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
    # Mobile URLs
    r'(?:https?://)?m\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
]

# Combined pattern for extraction
YOUTUBE_REGEX = re.compile(
    r'(?:https?://)?(?:(?:www\.|m\.)?youtube\.com/(?:watch\?v=|v/|embed/|shorts/)|youtu\.be/)([a-zA-Z0-9_-]{11})',
    re.IGNORECASE
)


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from URL.
    
    Args:
        url: YouTube URL string
        
    Returns:
        Video ID if found, None otherwise
    """
    match = YOUTUBE_REGEX.search(url)
    if match:
        return match.group(1)
    return None


def is_valid_youtube_url(url: str) -> bool:
    """
    Check if URL is a valid YouTube video URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid YouTube URL, False otherwise
    """
    return extract_video_id(url) is not None


def extract_urls_from_text(text: str) -> List[str]:
    """
    Extract all YouTube URLs from a text message.
    
    Args:
        text: Message text
        
    Returns:
        List of YouTube URLs found
    """
    # Find all URLs in text
    url_pattern = re.compile(
        r'https?://[^\s<>"{}|\\^`\[\]]+|'
        r'(?:www\.|m\.)?youtube\.com/[^\s<>"{}|\\^`\[\]]+|'
        r'youtu\.be/[^\s<>"{}|\\^`\[\]]+'
    )
    
    potential_urls = url_pattern.findall(text)
    
    # Filter to only valid YouTube URLs
    youtube_urls = []
    for url in potential_urls:
        # Add https:// if missing
        if not url.startswith('http'):
            url = 'https://' + url
        if is_valid_youtube_url(url):
            youtube_urls.append(url)
    
    return youtube_urls


def normalize_youtube_url(url: str) -> Optional[str]:
    """
    Normalize YouTube URL to standard format.
    
    Args:
        url: YouTube URL
        
    Returns:
        Normalized URL (https://www.youtube.com/watch?v=VIDEO_ID)
    """
    video_id = extract_video_id(url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return None
