import os
import re
from urllib.parse import urlparse

def is_valid_url(url: str) -> bool:
    """
    Check if the provided URL is valid.
    """
    try:
        parsed = urlparse(url)
        return parsed.scheme in ['http', 'https'] and bool(parsed.netloc)
    except Exception:
        return False

def cleanup_file(filepath: str) -> None:
    """
    Safely remove a file if it exists.
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except OSError as e:
        print(f"Error cleaning up file {filepath}: {e}")

def get_file_size(filepath: str) -> int:
    """
    Get the size of a file in bytes.
    """
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove invalid characters.
    """
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def is_image_url(url: str) -> bool:
    """
    Check if URL points to an image based on file extension.
    """
    image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
    parsed = urlparse(url)
    path = parsed.path.lower()
    return any(path.endswith(ext) for ext in image_exts)