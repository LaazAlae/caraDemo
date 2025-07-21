import magic
import hashlib
import time
from collections import defaultdict
from fastapi import HTTPException, UploadFile
from typing import Dict, List
from .config import settings

class SecurityValidator:
    def __init__(self):
        self.allowed_mime_types = {
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'audio/mpeg', 'audio/wav', 'audio/ogg',
            'video/mp4', 'video/webm'
        }
        self.rate_limits = defaultdict(list)
        
    def validate_file_type(self, content: bytes) -> str:
        """Validate file type using magic numbers"""
        mime_type = magic.from_buffer(content, mime=True)
        
        if mime_type not in self.allowed_mime_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {mime_type} is not allowed"
            )
        
        return mime_type
    
    def validate_file_size(self, content: bytes) -> bool:
        """Validate file size"""
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
            )
        return True
    
    def generate_file_hash(self, content: bytes) -> str:
        """Generate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    def validate_filename(self, filename: str) -> str:
        """Sanitize and validate filename"""
        if not filename:
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        # Remove path traversal attempts
        safe_filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Check extension
        extension = '.' + safe_filename.split('.')[-1].lower() if '.' in safe_filename else ''
        if extension not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File extension {extension} is not allowed"
            )
        
        return safe_filename
    
    def check_rate_limit(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit"""
        now = time.time()
        window_minute = 60  # 1 minute
        window_hour = 3600  # 1 hour
        
        # Clean old entries
        self.rate_limits[client_ip] = [
            timestamp for timestamp in self.rate_limits[client_ip]
            if now - timestamp < window_hour
        ]
        
        # Check hourly limit
        if len(self.rate_limits[client_ip]) >= settings.rate_limit_per_hour:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded - too many requests per hour"
            )
        
        # Check minute limit
        recent_requests = [
            timestamp for timestamp in self.rate_limits[client_ip]
            if now - timestamp < window_minute
        ]
        
        if len(recent_requests) >= settings.rate_limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded - too many requests per minute"
            )
        
        # Add current request
        self.rate_limits[client_ip].append(now)
        return True

security_validator = SecurityValidator()