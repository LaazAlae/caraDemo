import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import asyncio
from typing import Dict, Any
from .. import BaseDetectionProvider
from ...aggregation.schemas import DetectionResult, RiskLevel, ProviderStatus
from ...core.config import settings

class AWSRekognitionProvider(BaseDetectionProvider):
    def __init__(self):
        super().__init__("AWS_Rekognition")
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize AWS Rekognition client"""
        try:
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                self.client = boto3.client(
                    'rekognition',
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name='us-east-1'
                )
        except Exception as e:
            self.client = None
    
    def check_configuration(self) -> bool:
        """Check if AWS Rekognition is properly configured"""
        self.is_configured = (
            self.client is not None and 
            settings.aws_access_key_id != "your_aws_access_key_here" and
            bool(settings.aws_access_key_id)
        )
        return self.is_configured
    
    async def detect(self, file_content: bytes, file_type: str, filename: str) -> DetectionResult:
        """Detect faces and celebrities using AWS Rekognition"""
        if not file_type.startswith('image/'):
            return self._create_result(
                capability="face_detection",
                status=ProviderStatus.ERROR,
                error_message="AWS Rekognition only supports image files"
            )
        
        try:
            # Fixed the async call
            celebrity_response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.client.recognize_celebrities(Image={'Bytes': file_content})
            )
            
            face_response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.detect_faces(Image={'Bytes': file_content}, Attributes=['ALL'])
            )
            
            # Process results
            celebrities = celebrity_response.get('CelebrityFaces', [])
            faces = face_response.get('FaceDetails', [])
            
            total_matches = len(celebrities)
            confidence = 0.0
            
            if celebrities:
                confidence = sum(celeb.get('MatchConfidence', 0) for celeb in celebrities) / len(celebrities)
            elif faces:
                confidence = 60.0
            
            risk_level = self._determine_risk_level(confidence, total_matches)
            
            metadata = {
                "celebrities_found": len(celebrities),
                "total_faces": len(faces),
                "celebrities": [
                    {
                        "name": celeb.get('Name', ''),
                        "confidence": celeb.get('MatchConfidence', 0)
                    }
                    for celeb in celebrities[:5]
                ]
            }
            
            return self._create_result(
                capability="face_detection",
                status=ProviderStatus.SUCCESS,
                confidence=confidence,
                risk_level=risk_level,
                matches_found=total_matches,
                metadata=metadata
            )
            
        except Exception as e:
            return self._create_result(
                capability="face_detection",
                status=ProviderStatus.ERROR,
                error_message=f"AWS error: {str(e)}"
            )

# Create provider instance
aws_rekognition_provider = AWSRekognitionProvider()