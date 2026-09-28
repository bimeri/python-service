from typing import List, Optional

from pydantic import BaseModel


class SingleVerseInput(BaseModel):
    verse: int
    text: str

class ChapterTTSRequest(BaseModel):
    version: str
    bookName: str
    chapter: int
    verses: List[SingleVerseInput]
    lang: Optional[str] = "en"

class VerseAudioResponse(BaseModel):
    verse: int
    audioUrl: str