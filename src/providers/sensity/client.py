import httpx
import asyncio

class SensityClient:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.sensity.ai"
        
    async def detect_deepfake(self, file_data: bytes, file_type: str) -> Dict:
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        async with httpx.AsyncClient() as client:
            files = {"file": file_data}
            data = {"explain": True}
            
            endpoint = "tasks/face_manipulation" if file_type.startswith('image') else "tasks/voice_analysis"
            
            response = await client.post(
                f"{self.base_url}/{endpoint}",
                headers=headers,
                files=files,
                data=data,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise HTTPException(500, f"Sensity API error: {response.text}")
            
            task_id = response.json()["id"]
            return await self._poll_results(task_id, endpoint)
    
    async def _poll_results(self, task_id: str, endpoint: str) -> Dict:
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        for attempt in range(30):  # 5 minutes max
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{endpoint}/{task_id}",
                    headers=headers
                )
                
                result = response.json()
                if result["status"] == "completed":
                    return result
                elif result["status"] == "failed":
                    raise HTTPException(500, f"Sensity analysis failed: {result}")
                
                await asyncio.sleep(10)
        
        raise HTTPException(408, "Analysis timeout")