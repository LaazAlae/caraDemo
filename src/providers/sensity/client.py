import asyncio
import random
from typing import Dict, Any
from .. import BaseDetectionProvider
from ...aggregation.schemas import DetectionResult, RiskLevel, ProviderStatus
from ...core.config import settings

class SensityProvider(BaseDetectionProvider):
    """Mock Sensity AI provider for demo purposes"""
    
    def __init__(self):
        super().__init__("Sensity_AI")
        self.api_token = settings.sensity_api_token
    
    def check_configuration(self) -> bool:
        """For demo, always return True to show mock results"""
        self.is_configured = True
        return self.is_configured
    
    async def detect(self, file_content: bytes, file_type: str, filename: str) -> DetectionResult:
        """Mock deepfake detection"""
        
        # Simulate API call delay
        await asyncio.sleep(random.uniform(1.0, 3.0))
        
        # Generate realistic mock results
        if file_type.startswith('image/'):
            # Mock image deepfake detection
            is_deepfake = random.choice([True, False, False, False])  # 25% chance
            confidence = random.uniform(60, 95) if is_deepfake else random.uniform(10, 40)
            
            metadata = {
                "analysis_type": "face_manipulation",
                "techniques_detected": ["face_swap", "expression_transfer"] if is_deepfake else [],
                "manipulation_confidence": confidence if is_deepfake else 0,
                "authenticity_score": 100 - confidence
            }
            
        elif file_type.startswith('audio/'):
            # Mock audio deepfake detection  
            is_deepfake = random.choice([True, False, False])  # 33% chance
            confidence = random.uniform(70, 90) if is_deepfake else random.uniform(15, 35)
            
            metadata = {
                "analysis_type": "voice_cloning",
                "techniques_detected": ["voice_conversion", "speech_synthesis"] if is_deepfake else [],
                "manipulation_confidence": confidence if is_deepfake else 0,
                "authenticity_score": 100 - confidence
            }
        else:
            return self._create_result(
                capability="deepfake_detection",
                status=ProviderStatus.ERROR,
                error_message="Sensity AI supports only image and audio files"
            )
        
        matches = 1 if is_deepfake else 0
        risk_level = self._determine_risk_level(confidence, matches)
        
        return self._create_result(
            capability="deepfake_detection",
            status=ProviderStatus.SUCCESS,
            confidence=confidence,
            risk_level=risk_level,
            matches_found=matches,
            metadata=metadata
        )

# Create provider instance
sensity_provider = SensityProvider()