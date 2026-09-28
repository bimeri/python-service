import io
import os
import re
from typing import List

import edge_tts
import pdfplumber
import pytesseract
from PIL import Image
from fastapi import UploadFile, File

from app.schemas.fileAudioDto import ChapterTTSRequest, VerseAudioResponse

OUTPUT_DIR = "audio"

VOICE_MAP = {
    "en": "en-US-ChristopherNeural",
    "en-US": "en-US-ChristopherNeural",
    "us": "en-US-AriaNeural",
    "en-GB": "en-GB-RyanNeural",
    "es": "es-ES-AlvaroNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",
    "it": "it-IT-DiegoNeural",
    "pt": "pt-BR-AntonioNeural",
    "ja": "ja-JP-KeitaNeural",
    "ko": "ko-KR-InJoonNeural",
    "zh": "zh-CN-YunxiNeural",
}

VERSION_VOICE_MAP = {
    # English Versions
    "KJV": "en-US-ChristopherNeural",
    "NIV": "en-US-ChristopherNeural",
    "NKJV": "en-US-ChristopherNeural",
    "ASV": "en-US-ChristopherNeural",
    "WEB": "en-US-ChristopherNeural",
    "AMP": "en-US-AriaNeural",
    # French Versions
    "MARTIN": "fr-FR-HenriNeural",
    "EPEE": "fr-FR-VivienneNeural",
    # Romanian Versions
    "ROM": "ro-RO-EmilNeural",
}


class AdminService:
    @staticmethod
    def get_book_code(book_name: str) -> str:
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', book_name).upper()
        match = re.match(r'^(\d+)([A-Z]+)', clean_name)
        if match:
            num, rest = match.groups()
            return f"{num}{rest[:3]}"
        return clean_name[:3]

    def get_chapter_title_text(self, book_name: str, chapter: int, version: str) -> str:
        v = version.upper()
        if v in ["MARTIN", "EPEE"]:
            return f"{book_name}, Chapitre {chapter}"
        elif v == "ROM":
            return f"{book_name}, Capitolul {chapter}"
        return f"{book_name}, Chapter {chapter}"

    def resolve_voice_and_rate(self, version: str) -> tuple[str, str]:
        v = version.upper().strip()
        voice = VERSION_VOICE_MAP.get(v, "en-US-ChristopherNeural")

        # Slow down rate for French/Romanian (-15%), keep English slightly relaxed (-5%)
        if v in ["MARTIN", "EPEE", "ROM"]:
            rate = "-15%"
        else:
            rate = "-5%"

        return voice, rate

    async def process_chapter_audio(self, payload: ChapterTTSRequest) -> List[VerseAudioResponse]:
        version_clean = payload.version.upper().strip()
        book_clean = payload.bookName.upper().strip()
        book_code = self.get_book_code(payload.bookName)
        chapter_str = str(payload.chapter)

        chapter_dir = os.path.join(OUTPUT_DIR, version_clean, book_clean, chapter_str)
        os.makedirs(chapter_dir, exist_ok=True)

        voice, rate = self.resolve_voice_and_rate(payload.version)
        results: List[VerseAudioResponse] = []

        # ----------------------------------------------------
        # 1. GENERATE CHAPTER TITLE AUDIO (verse = 0)
        # ----------------------------------------------------
        title_filename = "title.mp3"
        title_full_path = os.path.join(chapter_dir, title_filename)
        title_relative_url = f"/audio/{version_clean}/{book_clean}/{chapter_str}/{title_filename}"

        if not os.path.exists(title_full_path):
            title_text = self.get_chapter_title_text(payload.bookName, payload.chapter, payload.version)
            # Pass rate parameter to adjust speech speed
            communicate = edge_tts.Communicate(title_text, voice, rate=rate)
            await communicate.save(title_full_path)

        # Add Title as verse 0
        results.append(VerseAudioResponse(
            verse=0,
            audioUrl=title_relative_url
        ))

        # ----------------------------------------------------
        # 2. GENERATE VERSES AUDIO
        # ----------------------------------------------------
        for item in payload.verses:
            filename = f"{book_code}_{chapter_str}_{item.verse}.mp3"
            full_file_path = os.path.join(chapter_dir, filename)
            relative_url = f"/audio/{version_clean}/{book_clean}/{chapter_str}/{filename}"

            if not os.path.exists(full_file_path):
                communicate = edge_tts.Communicate(item.text, voice, rate=rate)
                await communicate.save(full_file_path)

            results.append(VerseAudioResponse(
                verse=item.verse,
                audioUrl=relative_url
            ))

        return results

    async def upload_file(self: UploadFile = File(...)):
        filename = self.filename.lower()
        content = await self.read()

        extracted_text = ""

        # ---- TEXT FILE ----
        if filename.endswith(".txt"):
            extracted_text = content.decode("utf-8", errors="ignore")

        # ---- IMAGE FILE ----
        elif filename.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
            image = Image.open(io.BytesIO(content))
            extracted_text = pytesseract.image_to_string(image)

        # ---- PDF FILE ----
        elif filename.endswith(".pdf"):
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    extracted_text += page.extract_text() or ""

        else:
            return {"error": "Unsupported file type"}

        # Process line by line
        lines = process_text(extracted_text)

        # Print line by line in the console
        for line in lines:
            print(line)

        return {
            "filename": self.filename,
            "lines": lines
        }


def process_text(text: str):
    """Process text line by line"""
    lines = text.strip().split('\n')
    return [line.strip() for line in lines if line.strip()]