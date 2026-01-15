
import json
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
            return response.text
        except Exception as e:
            import logging
            logging.error(f"Gemini generation failed: {e}")
            # Check for quota exhaustion (429)
            if hasattr(e, 'args') and e.args and '429' in str(e.args[0]):
                return json.dumps({
                    "error": "quota_exceeded",
                    "message": "Gemini API quota exceeded. Please check your plan or try again later."
                })
            # Let ChatService handle other errors
            raise RuntimeError(f"Gemini generation failed: {e}")

    async def stream(self, prompt: str):
        """
        Stream text response from Gemini, yielding tokens as they arrive.
        Returns an async generator that yields text chunks.
        """
        try:
            response = self.client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "temperature": 0.7
                }
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            import logging
            logging.error(f"Gemini streaming failed: {e}")
            yield f"Error generating response: {str(e)}"

    async def embed(self, text: str) -> list[float]:
        """
        Generate embeddings for the given text using Gemini's embedding model.
        """
        try:
            response = self.client.models.embed_content(
                model="models/text-embedding-004",
                contents=text
            )
            return response.embeddings[0].values
        except Exception as e:
            # Return empty embedding on failure to allow graceful degradation
            import logging
            logging.warning(f"Gemini embedding failed: {e}")
            return []