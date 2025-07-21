import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any
from ..aggregation.schemas import UnifiedAnalysisResult, DetectionResult, RiskLevel
from ..core.security import security_validator
from ..providers.tineye.client import tineye_provider
from ..providers.aws_rekognition.client import aws_rekognition_provider
from ..providers.sensity.client import sensity_provider
from ..providers.acrcloud.client import acrcloud_provider

class DetectionAggregator:
    def __init__(self):
        self.providers = [
            tineye_provider,
            aws_rekognition_provider, 
            sensity_provider,
            acrcloud_provider
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
        
        # Get successful results only
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
            if result.matches_found > 0:
                if result.capability == "reverse_search":
                    factors.append(f"Similar images found online ({result.matches_found} matches)")
                elif result.capability == "face_detection":
                    if result.metadata.get("celebrities_found", 0) > 0:
                        factors.append("Celebrity face detected in image")
                    else:
                        factors.append("Human faces detected in content")
                elif result.capability == "deepfake_detection":
                    techniques = result.metadata.get("techniques_detected", [])
                    if techniques:
                        factors.append(f"Potential deepfake techniques: {', '.join(techniques)}")
                elif result.capability == "audio_fingerprint":
                    music_matches = result.metadata.get("music", [])
                    if music_matches:
                        factors.append("Copyrighted music detected in audio")
        
        if not factors:
            factors.append("No significant risk factors detected")
        
        return factors
    
    def _generate_recommendations(self, results: List[DetectionResult], risk_level: RiskLevel) -> List[str]:
        """Generate actionable recommendations based on risk assessment"""
        recommendations = []
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.extend([
                "Immediate action required - potential unauthorized use detected",
                "Document all evidence for potential legal proceedings",
                "Contact platforms directly for content removal requests",
                "Consider issuing DMCA takedown notices where applicable"
            ])
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.extend([
                "Monitor for additional instances of unauthorized use",
                "Consider watermarking future content releases",
                "Review platform usage policies and terms of service",
                "Set up automated monitoring alerts"
            ])
        else:
            recommendations.extend([
                "Continue regular monitoring of your digital assets",
                "Implement preventive measures like digital watermarking",
                "Consider registering copyrights for valuable content",
                "Stay informed about emerging AI threats"
            ])
        
        return recommendations

# Create global aggregator instance
detection_aggregator = DetectionAggregator()