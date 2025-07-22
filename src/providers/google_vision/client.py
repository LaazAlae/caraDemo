import httpx
import base64
import asyncio
from typing import Dict, Any
from .. import BaseDetectionProvider
from ...aggregation.schemas import DetectionResult, RiskLevel, ProviderStatus
from ...core.config import settings

class GoogleVisionProvider(BaseDetectionProvider):
    def __init__(self):
        super().__init__("Google_Vision")
        self.api_key = settings.google_vision_api_key
        self.api_url = "https://vision.googleapis.com/v1/images:annotate"
        
    def check_configuration(self) -> bool:
        """Check if Google Vision is properly configured"""
        self.is_configured = bool(self.api_key and self.api_key != "paste_your_google_api_key_here")
        return self.is_configured
    
    async def detect(self, file_content: bytes, file_type: str, filename: str) -> DetectionResult:
        """Detect objects, faces, and text using Google Vision"""
        if not file_type.startswith('image/'):
            return self._create_result(
                capability="image_analysis",
                status=ProviderStatus.ERROR,
                error_message="Google Vision only supports image files"
            )
        
        # Convert image to base64
        image_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Prepare request
        request_data = {
            "requests": [
                {
                    "image": {"content": image_base64},
                    "features": [
                        {"type": "FACE_DETECTION", "maxResults": 10},
                        {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                        {"type": "TEXT_DETECTION", "maxResults": 5},
                        {"type": "SAFE_SEARCH_DETECTION"},
                        {"type": "IMAGE_PROPERTIES"}
                    ]
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}?key={self.api_key}",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    return self._create_result(
                        capability="image_analysis",
                        status=ProviderStatus.ERROR,
                        error_message=f"Google Vision API error: {response.status_code}"
                    )
                
                data = response.json()
                
                if "error" in data:
                    return self._create_result(
                        capability="image_analysis",
                        status=ProviderStatus.ERROR,
                        error_message=f"Google Vision error: {data['error']['message']}"
                    )
                
                if response.status_code != 200:
                    # DEBUG: Print the exact error
                    print(f"Google Vision Error: {response.status_code}")
                    print(f"Error details: {response.text}")
                    return self._create_result(
                        capability="image_analysis",
                        status=ProviderStatus.ERROR,
                        error_message=f"Google Vision API error: {response.status_code} - {response.text}"
                    )
                
                # Process results
                result = data["responses"][0]
                
                # Count faces
                faces = result.get("faceAnnotations", [])
                face_count = len(faces)
                
                # Count objects
                objects = result.get("localizedObjectAnnotations", [])
                object_count = len(objects)
                
                # Get text
                texts = result.get("textAnnotations", [])
                text_found = len(texts) > 0
                
                # Get safe search
                safe_search = result.get("safeSearchAnnotation", {})
                
                # Calculate confidence and risk
                confidence = 0.0
                matches_found = 0
                risk_factors = []
                
                if face_count > 0:
                    confidence += 30
                    matches_found += face_count
                    risk_factors.append(f"{face_count} human face(s) detected")
                
                if object_count > 0:
                    confidence += 20
                    top_objects = [obj["name"] for obj in objects[:3]]
                    risk_factors.append(f"Objects detected: {', '.join(top_objects)}")
                
                if text_found:
                    confidence += 20
                    risk_factors.append("Text content detected in image")
                
                # Check for potentially sensitive content
                adult_likelihood = safe_search.get("adult", "UNKNOWN")
                violence_likelihood = safe_search.get("violence", "UNKNOWN")
                
                if adult_likelihood in ["LIKELY", "VERY_LIKELY"]:
                    confidence += 40
                    risk_factors.append("Potentially sensitive content detected")
                
                if violence_likelihood in ["LIKELY", "VERY_LIKELY"]:
                    confidence += 30
                    risk_factors.append("Violent content detected")
                
                confidence = min(confidence, 100.0)
                risk_level = self._determine_risk_level(confidence, matches_found)
                
                # Prepare metadata
                metadata = {
                    "faces_detected": face_count,
                    "objects_detected": object_count,
                    "text_detected": text_found,
                    "top_objects": [obj["name"] for obj in objects[:5]],
                    "face_emotions": [
                        {
                            "joy": face.get("joyLikelihood", "UNKNOWN"),
                            "anger": face.get("angerLikelihood", "UNKNOWN"),
                            "surprise": face.get("surpriseLikelihood", "UNKNOWN")
                        }
                        for face in faces[:3]
                    ],
                    "safe_search": safe_search,
                    "risk_factors": risk_factors
                }
                
                return self._create_result(
                    capability="image_analysis",
                    status=ProviderStatus.SUCCESS,
                    confidence=confidence,
                    risk_level=risk_level,
                    matches_found=matches_found,
                    metadata=metadata
                )
                
            except httpx.TimeoutException:
                return self._create_result(
                    capability="image_analysis",
                    status=ProviderStatus.TIMEOUT,
                    error_message="Google Vision request timed out"
                )
            except Exception as e:
                return self._create_result(
                    capability="image_analysis",
                    status=ProviderStatus.ERROR,
                    error_message=f"Google Vision error: {str(e)}"
                )

# Create provider instance
google_vision_provider = GoogleVisionProvider()