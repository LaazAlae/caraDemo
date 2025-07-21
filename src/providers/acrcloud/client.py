import asyncio
import random
from typing import Dict, Any
from ..base import BaseDetectionProvider
from ...aggregation.schemas import DetectionResult, RiskLevel, ProviderStatus
from ...core.config import settings

class ACRCloudProvider(BaseDetectionProvider):
    """Mock ACRCloud provider for demo purposes"""
    
    def __init__(self):
        super().__init__("ACRCloud")
        self.access_key = settings.acrcloud_access_key
        self.secret_key = settings.acrcloud_secret_key
    
    def check_configuration(self) -> bool:
        """For demo, always return True to show mock results"""
        self.is_configured = True
        return self.is_configured
    
    async def detect(self, file_content: bytes, file_type: str, filename: str) -> DetectionResult:
        """Mock audio fingerprinting"""
        
        if not file_type.startswith('audio/'):
            return self._create_result(
                capability="audio_fingerprint",
                status=ProviderStatus.ERROR,
                error_message="ACRCloud only supports audio files"
            )
        
        # Simulate API call delay
        await asyncio.sleep(random.uniform(2.0, 5.0))
        
        # Generate realistic mock results
        has_match = random.choice([True, False, False])  # 33% chance of finding a match
        
        if has_match:
            # Mock famous song match
            songs = [
                {"title": "Shape of You", "artist": "Ed Sheeran", "album": "÷ (Divide)"},
                {"title": "Blinding Lights", "artist": "The Weeknd", "album": "After Hours"},
                {"title": "Watermelon Sugar", "artist": "Harry Styles", "album": "Fine Line"},
                {"title": "Good 4 U", "artist": "Olivia Rodrigo", "album": "SOUR"},
                {"title": "Stay", "artist": "The Kid LAROI & Justin Bieber", "album": "F*CK LOVE 3: OVER YOU"}
            ]
            
            match = random.choice(songs)
            confidence = random.uniform(80, 98)
            
            metadata = {
                "music": [{
                    "title": match["title"],
                    "artists": [{"name": match["artist"]}],
                    "album": {"name": match["album"]},
                    "score": confidence,
                    "play_offset_ms": random.randint(10000, 120000),
                    "duration_ms": random.randint(180000, 300000)
                }],
                "matched_segments": [
                    {
                        "start_time": 0,
                        "end_time": min(len(file_content) // 1000, 30),  # Mock duration
                        "confidence": confidence
                    }
                ]
            }
            
            matches_found = 1
        else:
            confidence = random.uniform(5, 25)
            metadata = {
                "music": [],
                "custom_files": [],
                "message": "No matches found in database"
            }
            matches_found = 0
        
        risk_level = self._determine_risk_level(confidence, matches_found)
        
        return self._create_result(
            capability="audio_fingerprint",
            status=ProviderStatus.SUCCESS,
            confidence=confidence,
            risk_level=risk_level,
            matches_found=matches_found,
            metadata=metadata
        )

# Create provider instance
acrcloud_provider = ACRCloudProvider()