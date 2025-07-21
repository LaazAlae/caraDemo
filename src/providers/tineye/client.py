import httpx
import hashlib
import hmac
import urllib.parse
from typing import Dict, Any
from .. import BaseDetectionProvider
from ...aggregation.schemas import DetectionResult, RiskLevel, ProviderStatus
from ...core.config import settings

class TinEyeProvider(BaseDetectionProvider):
    def __init__(self):
        super().__init__("TinEye")
        self.api_url = "https://api.tineye.com/rest/search/"
        self.api_key = settings.tineye_api_key
        
    def check_configuration(self) -> bool:
        """Check if TinEye is properly configured"""
        self.is_configured = bool(self.api_key and self.api_key != "your_tineye_api_key_here")
        return self.is_configured
    
    async def detect(self, file_content: bytes, file_type: str, filename: str) -> DetectionResult:
        """Search for image matches using TinEye"""
        if not file_type.startswith('image/'):
            return self._create_result(
                capability="reverse_search",
                status=ProviderStatus.ERROR,
                error_message="TinEye only supports image files"
            )
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"image": (filename, file_content, file_type)}
            params = {
                "api_key": self.api_key,
                "offset": 0,
                "limit": 100,
                "sort": "score",
                "order": "desc"
            }
            
            try:
                response = await client.post(
                    self.api_url,
                    files=files,
                    params=params
                )
                
                if response.status_code != 200:
                    return self._create_result(
                        capability="reverse_search",
                        status=ProviderStatus.ERROR,
                        error_message=f"TinEye API error: {response.status_code}"
                    )
                
                data = response.json()
                
                if data.get("status") != "ok":
                    return self._create_result(
                        capability="reverse_search",
                        status=ProviderStatus.ERROR,
                        error_message=f"TinEye error: {data.get('error', 'Unknown error')}"
                    )
                
                # Extract results
                results = data.get("results", {})
                matches = results.get("matches", [])
                total_matches = len(matches)
                
                # Calculate confidence based on number of matches and scores
                confidence = 0.0
                if total_matches > 0:
                    # Use average score of top matches
                    top_scores = [match.get("score", 0) for match in matches[:5]]
                    confidence = sum(top_scores) / len(top_scores) * 100
                
                risk_level = self._determine_risk_level(confidence, total_matches)
                
                return self._create_result(
                    capability="reverse_search",
                    status=ProviderStatus.SUCCESS,
                    confidence=confidence,
                    risk_level=risk_level,
                    matches_found=total_matches,
                    metadata={
                        "matches": matches[:10],  # Only return top 10 matches
                        "query_hash": results.get("query", {}).get("hash", ""),
                        "total_time": data.get("query_time", 0)
                    }
                )
                
            except httpx.TimeoutException:
                return self._create_result(
                    capability="reverse_search",
                    status=ProviderStatus.TIMEOUT,
                    error_message="TinEye request timed out"
                )

# Create provider instance
tineye_provider = TinEyeProvider()