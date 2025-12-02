"""
Utility functions for the MCP Tool-Calling Agent
"""
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import hashlib
import os
import re

logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing unsafe characters
    """
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Replace unsafe characters with underscores
    unsafe_chars = r'[<>:"/\\|?*]'
    filename = re.sub(unsafe_chars, '_', filename)
    
    # Remove any control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Truncate if too long (keep extension)
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

def generate_file_hash(file_path: str) -> str:
    """
    Generate MD5 hash of a file for deduplication
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error generating file hash: {str(e)}")
        return ""

def format_file_size(size_bytes: int) -> str:
    """
    Convert bytes to human-readable file size
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def clean_text(text: str) -> str:
    """
    Clean and normalize text content
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters except newlines and tabs
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Strip leading/trailing whitespace
    return text.strip()

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text using simple frequency analysis
    """
    if not text:
        return []
    
    # Convert to lowercase and split into words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
    }
    
    # Filter out stop words
    keywords = [word for word in words if word not in stop_words]
    
    # Count frequency
    word_freq = {}
    for word in keywords:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]

def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Basic JSON schema validation
    """
    errors = []
    
    # Check required fields
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check data types (basic validation)
    properties = schema.get('properties', {})
    for field, value in data.items():
        if field in properties:
            expected_type = properties[field].get('type')
            if expected_type:
                if expected_type == 'string' and not isinstance(value, str):
                    errors.append(f"Field '{field}' must be a string")
                elif expected_type == 'integer' and not isinstance(value, int):
                    errors.append(f"Field '{field}' must be an integer")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' must be a number")
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"Field '{field}' must be a boolean")
                elif expected_type == 'array' and not isinstance(value, list):
                    errors.append(f"Field '{field}' must be an array")
                elif expected_type == 'object' and not isinstance(value, dict):
                    errors.append(f"Field '{field}' must be an object")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def safe_json_parse(json_str: str) -> Optional[Union[Dict, List]]:
    """
    Safely parse JSON string with error handling
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {str(e)}")
        return None

def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def get_mime_type(filename: str) -> str:
    """
    Get MIME type based on file extension
    """
    extension = os.path.splitext(filename)[1].lower()
    
    mime_types = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.json': 'application/json',
        '.csv': 'text/csv',
        '.xml': 'application/xml',
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.mp3': 'audio/mpeg',
        '.mp4': 'video/mp4',
        '.zip': 'application/zip'
    }
    
    return mime_types.get(extension, 'application/octet-stream')

def create_error_response(error_message: str, error_code: str = None, details: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create standardized error response
    """
    response = {
        'success': False,
        'error': error_message,
        'timestamp': datetime.now().isoformat()
    }
    
    if error_code:
        response['error_code'] = error_code
    
    if details:
        response['details'] = details
    
    return response

def create_success_response(data: Dict[str, Any] = None, message: str = None) -> Dict[str, Any]:
    """
    Create standardized success response
    """
    response = {
        'success': True,
        'timestamp': datetime.now().isoformat()
    }
    
    if message:
        response['message'] = message
    
    if data:
        response.update(data)
    
    return response

class Timer:
    """
    Context manager for timing operations
    """
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        self.elapsed_time = (self.end_time - self.start_time).total_seconds()
    
    def get_elapsed_seconds(self) -> float:
        if self.elapsed_time is not None:
            return self.elapsed_time
        elif self.start_time is not None:
            return (datetime.now() - self.start_time).total_seconds()
        else:
            return 0.0