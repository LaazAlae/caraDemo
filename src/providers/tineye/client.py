import httpx
from typing import List, Dict

class TinEyeClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tineye.com/rest/"
        
    async def search_image(self, image_data: bytes) -> Dict:
        async with httpx.AsyncClient() as client:
            files = {"image": image_data}
            params = {
                "api_key": self.api_key,
                "offset": 0,
                "limit": 100,
                "sort": "score",
                "order": "desc"
            }
            
            response = await client.post(
                f"{self.base_url}search",
                files=files,
                params=params,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(500, f"TinEye API error: {response.text}")
                
            return response.json()