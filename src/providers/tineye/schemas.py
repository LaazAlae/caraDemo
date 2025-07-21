from pydantic import BaseModel
from typing import List, Optional

class TinEyeMatch(BaseModel):
    image_url: str
    domain: str
    score: float
    width: int
    height: int

class TinEyeResponse(BaseModel):
    status: str
    matches: List[TinEyeMatch]
    total_matches: int