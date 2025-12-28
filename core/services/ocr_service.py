import io
import os
import platform
import pdfplumber
import pytesseract
from PIL import Image

# Configure Tesseract for cross-platform compatibility
if platform.system() == "Windows":
    # Windows: Use local installation path
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:
    # Linux/Cloud: Use system PATH
    pytesseract.pytesseract.tesseract_cmd = 'tesseract'

class OCRService:
    async def extract(self, file_bytes: bytes, filename: str) -> str:
        """
        Unified OCR entry point.
        Automatically detects file type.
        """
        filename = filename.lower()

        if filename.endswith(".pdf"):
            return await self.extract_from_pdf(file_bytes)

        if filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
            return await self.extract_from_image(file_bytes)

        raise ValueError("Unsupported file type for OCR")

    async def extract_from_pdf(self, file_bytes: bytes) -> str:
        """
        Extract text from text-based PDFs.
        """
        text = ""
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()

    async def extract_from_image(self, file_bytes: bytes) -> str:
        """
        Extract text from image files (jpg, png, scanned PDFs).
        """
        image = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(image).strip()