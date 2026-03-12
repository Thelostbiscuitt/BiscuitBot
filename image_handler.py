import logging
import httpx

logger = logging.getLogger(__name__)

class ImageHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        # Stable Diffusion 3 Turbo Endpoint
        self.url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
        
    async def generate_image(self, prompt: str):
        """
        Generates an image using Stability AI (SD3).
        Returns: (Success: bool, Data: bytes_or_error_message)
        """
        if not self.api_key:
            return False, "Stability AI API Key not configured."

        headers = {
            "authorization": f"Bearer {self.api_key}",
            "accept": "image/*"
            # Note: We do NOT set 'content-type' here. 
            # httpx will automatically set it to 'multipart/form-data' because we use the 'files' parameter.
        }

        # We use the 'files' parameter to force httpx to use 'multipart/form-data' encoding.
        # (None is used for the filename since we are sending text fields, not actual files).
        files = {
            "prompt": (None, prompt),
            "output_format": (None, "jpeg")
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.url, headers=headers, files=files)
                
                logger.info(f"Stability AI Status: {response.status_code}")

                if response.status_code != 200:
                    # .text is a property in httpx, not a method
                    error_text = response.text
                    return False, f"Stability AI Error {response.status_code}: {error_text}"
                
                # Read the image bytes
                image_bytes = await response.read()
                
                return True, image_bytes

        except Exception as e:
            logger.error(f"Exception during image generation: {e}")
            return False, f"Exception: {str(e)}"
