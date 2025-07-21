from pydantic import BaseModel
from typing import List

class MusicMatch(BaseModel):
    title: str
    artist: str
    album: str
    score: float