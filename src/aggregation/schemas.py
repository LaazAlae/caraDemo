from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ProviderStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    NOT_CONFIGURED = "not_configured"

class DetectionResult(BaseModel):
    provider: str
    capability: str
    status: ProviderStatus
    confidence: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    matches_found: int = 0
    processing_time_ms: int = 0
    metadata: Dict[str, Any] = {}
    error_message: Optional[str] = None

class FileAnalysis(BaseModel):
    file_id: str
    original_filename: str
    file_hash: str
    file_type: str
    file_size: int
    created_at: datetime = datetime.now()

class UnifiedAnalysisResult(BaseModel):
    # File information
    file_id: str
    original_filename: str
    file_hash: str
    file_type: str
    file_size: int
    
    # Overall assessment
    overall_risk_level: RiskLevel
    overall_confidence: float
    total_matches: int
    total_processing_time_ms: int
    
    # Provider results
    results: List[DetectionResult]
    
    # Risk assessment
    risk_factors: List[str]
    recommendations: List[str]
    
    # Timestamps
    created_at: datetime = datetime.now()
    
    # Convenience properties
    @property
    def reverse_search(self) -> Optional[DetectionResult]:
        return next((r for r in self.results if r.capability == "reverse_search"), None)
    
    @property
    def face_detection(self) -> Optional[DetectionResult]:
        return next((r for r in self.results if r.capability == "face_detection"), None)
    
    @property
    def deepfake_detection(self) -> Optional[DetectionResult]:
        return next((r for r in self.results if r.capability == "deepfake_detection"), None)
    
    @property
    def audio_fingerprint(self) -> Optional[DetectionResult]:
        return next((r for r in self.results if r.capability == "audio_fingerprint"), None)