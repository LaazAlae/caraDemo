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
                    region_name='us-east-1'  # Rekognition is available in several regions
                )
            else:
                # Try to use default AWS credentials
                self.client = boto3.client('rekognition', region_name='us-east-1')
        except Exception as e:
            self.client = None
    
    def check_configuration(self) -> bool:
        """Check if AWS Rekognition is properly configured"""
        self.is_configured = self.client is not None
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
            # Run both celebrity recognition and face detection
            celebrity_response = await self._run_sync(
                self.client.recognize_celebrities,
                Image={'Bytes': file_content}
            )
            
            face_response = await self._run_sync(
                self.client.detect_faces,
                Image={'Bytes': file_content},
                Attributes=['ALL']
            )
            
            # Process results
            celebrities = celebrity_response.get('CelebrityFaces', [])
            faces = face_response.get('FaceDetails', [])
            unrecognized_faces = celebrity_response.get('UnrecognizedFaces', [])
            
            total_matches = len(celebrities)
            total_faces = len(faces)
            
            # Calculate confidence
            confidence = 0.0
            if celebrities:
                # Average confidence of celebrity matches
                confidence = sum(celeb.get('MatchConfidence', 0) for celeb in celebrities) / len(celebrities)
            elif faces:
                # If no celebrities but faces detected, moderate confidence
                confidence = 60.0
            
            risk_level = self._determine_risk_level(confidence, total_matches)
            
            # Prepare metadata
            metadata = {
                "celebrities_found": len(celebrities),
                "total_faces": total_faces,
                "unrecognized_faces": len(unrecognized_faces),
                "celebrities": [
                    {
                        "name": celeb.get('Name', ''),
                        "confidence": celeb.get('MatchConfidence', 0),
                        "urls": celeb.get('Urls', [])
                    }
                    for celeb in celebrities[:5]  # Top 5 matches
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
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidImageFormatException':
                return self._create_result(
                    capability="face_detection",
                    status=ProviderStatus.ERROR,
                    error_message="Invalid image format for AWS Rekognition"
                )
            elif error_code == 'ImageTooLargeException':
                return self._create_result(
                    capability="face_detection",
                    status=ProviderStatus.ERROR,
                    error_message="Image too large for AWS Rekognition"
                )
            else:
                return self._create_result(
                    capability="face_detection",
                    status=ProviderStatus.ERROR,
                    error_message=f"AWS error: {error_code}"
                )
        
        except NoCredentialsError:
            return self._create_result(
                capability="face_detection",
                status=ProviderStatus.ERROR,
                error_message="AWS credentials not configured"
            )
    
    async def _run_sync(self, func, *args, **kwargs):
        """Run synchronous AWS calls in async context"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)

# Create provider instance
aws_rekognition_provider = AWSRekognitionProvider()