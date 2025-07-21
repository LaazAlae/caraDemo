# src/core/security.py
import magic
from collections import defaultdict
import time

class SecurityValidator:
    def __init__(self):
        self.allowed_types = {
            'image/jpeg', 'image/png', 'image/gif',
            'audio/mpeg', 'audio/wav', 'video/mp4'
        }
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.rate_limits = defaultdict(list)
        
    async def validate_file(self, file: UploadFile, client_ip: str) -> bool:
        # Rate limiting
        self._check_rate_limit(client_ip)
        
        # File type validation
        content = await file.read()
        await file.seek(0)
        
        mime_type = magic.from_buffer(content, mime=True)
        if mime_type not in self.allowed_types:
            raise HTTPException(400, f"File type {mime_type} not allowed")
            
        # Size validation
        if len(content) > self.max_file_size:
            raise HTTPException(413, "File too large")
            
        return True
    
    def _check_rate_limit(self, client_ip: str):
        now = time.time()
        window = 3600  # 1 hour
        
        # Clean old entries
        self.rate_limits[client_ip] = [
            t for t in self.rate_limits[client_ip] 
            if now - t < window
        ]
        
        # Check limit
        if len(self.rate_limits[client_ip]) >= 50:  # 50 uploads per hour
            raise HTTPException(429, "Rate limit exceeded")
            
        self.rate_limits[client_ip].append(now)