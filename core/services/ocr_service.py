import io
import pdfplumber
import pytesseract
from PIL import Image

class OCRService:
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