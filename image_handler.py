import logging
import httpx
from io import BytesIO

logger = logging.getLogger(__name__)

class ImageHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        # UPDATED: Added '/hf-inference/' to the path for the new Router
        self.base_url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
        
    async def generate_image(self, prompt: str):
        """
        Generates an image using Hugging Face Router API.
        Returns: (Success: bool, Data: bytes_or_error_message)
        """
        if not self.api_key:
            return False, "Hugging Face API Key not configured."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": prompt
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.base_url, headers=headers, json=payload)
                
                logger.info(f"HF Router Status Code: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text
                    return False, f"API Error {response.status_code}: {error_text[:200]}"
                
                # Hugging Face returns the image bytes directly
                image_bytes = await response.read()
                
                return True, image_bytes

        except Exception as e:
            logger.error(f"Exception during image generation: {e}")
            return False, f"Exception: {str(e)}"
