from pydantic import BaseModel
from typing import List

class DeepfakeAnalysis(BaseModel):
    is_manipulated: bool
    confidence: float
    techniques: List[str]
