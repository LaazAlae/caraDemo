from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import logging
from ..aggregation.schemas import DetectionResult, RiskLevel, ProviderStatus

logger = logging.getLogger(__name__)

class BaseDetectionProvider(ABC):
    """Base class for all detection providers"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.is_configured = False
    
    @abstractmethod
    async def detect(self, file_content: bytes, file_type: str, filename: str) -> DetectionResult:
        """Main detection method that each provider must implement"""
        pass
    
    @abstractmethod
    def check_configuration(self) -> bool:
        """Check if provider is properly configured"""
        pass
    
    def _create_result(
        self,
        capability: str,
        status: ProviderStatus = ProviderStatus.SUCCESS,
        confidence: float = 0.0,
        risk_level: RiskLevel = RiskLevel.LOW,
        matches_found: int = 0,
        processing_time_ms: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> DetectionResult:
        """Helper method to create standardized detection results"""
        return DetectionResult(
            provider=self.provider_name,
            capability=capability,
            status=status,
            confidence=confidence,
            risk_level=risk_level,
            matches_found=matches_found,
            processing_time_ms=processing_time_ms,
            metadata=metadata or {},
            error_message=error_message
        )
    
    def _determine_risk_level(self, confidence: float, matches: int) -> RiskLevel:
        """Determine risk level based on confidence and matches"""
        if matches == 0:
            return RiskLevel.LOW
        elif confidence >= 90 and matches >= 5:
            return RiskLevel.CRITICAL
        elif confidence >= 75 and matches >= 3:
            return RiskLevel.HIGH
        elif confidence >= 50 or matches >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def safe_detect(self, file_content: bytes, file_type: str, filename: str) -> DetectionResult:
        """Wrapper method that handles exceptions and timing"""
        if not self.check_configuration():
            return self._create_result(
                capability=self.provider_name.lower(),
                status=ProviderStatus.NOT_CONFIGURED,
                error_message=f"{self.provider_name} is not configured"
            )
        
        start_time = time.time()
        
        try:
            result = await self.detect(file_content, file_type, filename)
            result.processing_time_ms = int((time.time() - start_time) * 1000)
            return result
        
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"Error in {self.provider_name}: {str(e)}")
            
            return self._create_result(
                capability=self.provider_name.lower(),
                status=ProviderStatus.ERROR,
                processing_time_ms=processing_time,
                error_message=str(e)
            )