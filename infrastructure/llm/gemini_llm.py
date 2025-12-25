from google import genai
from config.settings import GEMINI_API_KEY

class GeminiLLM:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    async def generate(self, prompt: str) -> str:
        """
        Generates a STRICT JSON response from Gemini.
        This method is REQUIRED by ChatService.
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2
                }
            )

            # Gemini guarantees JSON due to response_mime_type
            return response.text

        except Exception as e:
            # Let ChatService handle fallback
            raise RuntimeError(f"Gemini generation failed: {e}")