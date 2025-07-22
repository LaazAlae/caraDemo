import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any
from ..aggregation.schemas import UnifiedAnalysisResult, DetectionResult, RiskLevel
from ..core.security import security_validator
from ..providers.google_vision.client import google_vision_provider
from ..providers.aws_rekognition.client import aws_rekognition_provider
from ..providers.tineye.client import tineye_provider
from ..providers.sensity.client import sensity_provider
from ..providers.acrcloud.client import acrcloud_provider

class DetectionAggregator:
    def __init__(self):
        self.providers = [
            google_vision_provider,      # Basic detection
            aws_rekognition_provider,   # CELEBRITY DETECTION ✨
            tineye_provider,            # Coming Soon
            sensity_provider,           # Coming Soon  
            acrcloud_provider          # Coming Soon
        ]
    
    async def analyze_file(
        self,
        file_id: str,
        filename: str,
        content: bytes,
        content_type: str
    ) -> UnifiedAnalysisResult:
        """Aggregate detection results from all providers"""
        
        # Validate file
        file_hash = security_validator.generate_file_hash(content)
        file_size = len(content)
        
        # Run all providers concurrently
        start_time = datetime.now()
        provider_tasks = [
            provider.safe_detect(content, content_type, filename)
            for provider in self.providers
        ]
        
        results = await asyncio.gather(*provider_tasks, return_exceptions=True)
        
        # Filter out exceptions and convert to DetectionResult objects
        valid_results = []
        for result in results:
            if isinstance(result, DetectionResult):
                valid_results.append(result)
            elif isinstance(result, Exception):
                # Log the exception but continue
                print(f"Provider error: {result}")
        
        # Calculate overall metrics
        total_processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        overall_risk_level, overall_confidence = self._calculate_overall_risk(valid_results)
        total_matches = sum(r.matches_found for r in valid_results if r.matches_found > 0)
        
        # Generate risk factors and recommendations
        risk_factors = self._generate_risk_factors(valid_results)
        recommendations = self._generate_recommendations(valid_results, overall_risk_level)
        
        return UnifiedAnalysisResult(
            file_id=file_id,
            original_filename=filename,
            file_hash=file_hash,
            file_type=content_type,
            file_size=file_size,
            overall_risk_level=overall_risk_level,
            overall_confidence=overall_confidence,
            total_matches=total_matches,
            total_processing_time_ms=total_processing_time,
            results=valid_results,
            risk_factors=risk_factors,
            recommendations=recommendations,
            created_at=start_time
        )
    
    def _calculate_overall_risk(self, results: List[DetectionResult]) -> tuple[RiskLevel, float]:
        """Calculate overall risk level and confidence from provider results"""
        if not results:
            return RiskLevel.LOW, 0.0
        
        # Get successful results only (ignore "Coming Soon" providers)
        successful_results = [r for r in results if r.status.value == "success"]
        
        if not successful_results:
            return RiskLevel.LOW, 0.0
        
        # Calculate weighted confidence
        total_confidence = 0.0
        total_weight = 0.0
        risk_scores = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        max_risk_score = 0
        
        for result in successful_results:
            # Weight based on provider reliability and matches found
            weight = 1.0
            if result.matches_found > 0:
                weight += 0.5
            if result.confidence > 80:
                weight += 0.3
            
            total_confidence += result.confidence * weight
            total_weight += weight
            
            # Track highest risk level
            risk_score = risk_scores.get(result.risk_level.value, 0)
            max_risk_score = max(max_risk_score, risk_score)
        
        # Calculate overall confidence
        overall_confidence = total_confidence / total_weight if total_weight > 0 else 0.0
        
        # Determine overall risk level
        if max_risk_score >= 3:
            overall_risk = RiskLevel.CRITICAL
        elif max_risk_score >= 2:
            overall_risk = RiskLevel.HIGH
        elif max_risk_score >= 1:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW
        
        return overall_risk, min(overall_confidence, 100.0)
    
    def _generate_risk_factors(self, results: List[DetectionResult]) -> List[str]:
        """Generate human-readable risk factors based on results"""
        factors = []
        
        for result in results:
            if result.status.value == "success" and result.matches_found > 0:
                if result.capability == "image_analysis":
                    # Extract real factors from Google Vision
                    risk_factors = result.metadata.get("risk_factors", [])
                    factors.extend(risk_factors)
                elif result.capability == "face_detection":
                    # Show detailed celebrity information from AWS
                    celebrities = result.metadata.get("celebrities", [])
                    if celebrities:
                        for celeb in celebrities:
                            name = celeb.get("name", "Unknown")
                            confidence = celeb.get("confidence", 0)
                            factors.append(f"🎯 Celebrity detected: {name} ({confidence:.1f}% confidence)")
                    else:
                        faces_count = result.metadata.get("total_faces", 0)
                        if faces_count > 0:
                            factors.append(f"👤 {faces_count} human face(s) detected")
        
        if not factors:
            factors.append("Content analyzed - standard digital media detected")
        
        return factors
    
    def _generate_recommendations(self, results: List[DetectionResult], risk_level: RiskLevel) -> List[str]:
        """Generate actionable recommendations based on risk assessment"""
        recommendations = []
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.extend([
                "Review content for potential policy violations",
                "Consider implementing additional content safeguards",
                "Monitor for unauthorized usage across platforms",
                "Document analysis results for compliance records"
            ])
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.extend([
                "Standard monitoring recommended for this content type",
                "Consider watermarking for future content protection",
                "Regular analysis recommended for similar content",
                "Implement basic usage tracking"
            ])
        else:
            recommendations.extend([
                "Content appears standard - continue normal monitoring",
                "Consider periodic re-analysis for valuable content",
                "Implement preventive digital watermarking",
                "Stay updated on emerging AI detection technologies"
            ])
        
        return recommendations

# Create global aggregator instance
detection_aggregator = DetectionAggregator()