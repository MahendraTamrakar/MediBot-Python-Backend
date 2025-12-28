import os
import platform
import pytesseract
from PIL import Image
import pdfplumber
from core.agents.base_agent import BaseAgent

# Configure Tesseract for cross-platform compatibility
if platform.system() == "Windows":
    # Windows: Use local installation path
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:
    # Linux/Cloud: Use system PATH
    pytesseract.pytesseract.tesseract_cmd = 'tesseract'

class OCRAgent(BaseAgent):
    async def run(self, file_path: str) -> str:
        try:
            if file_path.lower().endswith(".pdf"):
                return self._from_pdf(file_path)
            return pytesseract.image_to_string(Image.open(file_path))
        except Exception:
            return ""

    def _from_pdf(self, path):
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text