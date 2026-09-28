from typing import List

from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel

from app.schemas.fileAudioDto import VerseAudioResponse, ChapterTTSRequest
from app.services.adminService import AdminService

adminRoutes = APIRouter(prefix="/api", tags=["text-to-speech"])

def getAdminService() -> AdminService:
  return AdminService()


class TTSRequest(BaseModel):
  text: str
  lang: str = "en"

@adminRoutes.post("/chapter-tts", response_model=List[VerseAudioResponse], summary="Generate or retrieve audio for chapter verses")
async def process_chapter_tts(
    payload: ChapterTTSRequest,
    service: AdminService = Depends(getAdminService)
):
    return await service.process_chapter_audio(payload)

@adminRoutes.post("/upload", summary="file processing")
async def upload_file(file: UploadFile = File(...), service: AdminService = Depends(getAdminService)):

  return await service.upload_file(file)

