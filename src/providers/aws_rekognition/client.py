import boto3
from botocore.exceptions import ClientError

class RekognitionClient:
    def __init__(self):
        self.client = boto3.client('rekognition')
        
    async def detect_faces(self, image_bytes: bytes) -> Dict:
        try:
            response = self.client.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['ALL']
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                await asyncio.sleep(2)
                return await self.detect_faces(image_bytes)
            raise HTTPException(500, f"AWS Rekognition error: {str(e)}")
    
    async def recognize_celebrities(self, image_bytes: bytes) -> Dict:
        try:
            response = self.client.recognize_celebrities(
                Image={'Bytes': image_bytes}
            )
            return response
        except ClientError as e:
            raise HTTPException(500, f"Celebrity recognition error: {str(e)}")