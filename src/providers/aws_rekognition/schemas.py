from pydantic import BaseModel
from typing import List, Optional

class Celebrity(BaseModel):
    name: str
    confidence: float
    urls: List[str]

class Face(BaseModel):
    confidence: float
    age_range: dict
    gender: dict

class RekognitionResponse(BaseModel):
    celebrities: List[Celebrity]
    faces: List[Face]