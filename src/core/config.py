from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Google Vision API (Primary - Easy setup)
    google_vision_api_key: str = ""
    
    # AWS (Secondary - More powerful but harder setup)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    
    # Application
    secret_key: str = "development-key-change-in-production"
    cors_origins: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    environment: str = "development"
    
    # File handling
    max_file_size: int = 52428800  # 50MB
    upload_path: str = "./uploads"
    allowed_extensions: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".mp3", ".wav", ".mp4"]
    
    # Rate limiting
    rate_limit_per_hour: int = 100
    rate_limit_per_minute: int = 20
    
    class Config:
        env_file = ".env"

settings = Settings()