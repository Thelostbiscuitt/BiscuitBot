import logging
import httpx
import urllib.parse
import time # Using standard python time module

logger = logging.getLogger(__name__)

class ImageHandler:
    def __init__(self, api_key):
        # Pollinations.ai requires NO API KEY.
        # We accept the key in __init__ to keep the code compatible, but we ignore it.
        self.api_key = api_key 
        
    async def generate_image(self, prompt: str):
        """
        Generates an image using Pollinations.ai (Free, No Key Required).
        Returns: (Success: bool, Data: bytes_or_error_message)
        """
        try:
            # URL Encode the prompt to handle spaces and special characters
            safe_prompt = urllib.parse.quote(prompt)
            
            # Pollinations URL
            # nologo=true removes the watermark
            # seed ensures we get a unique image every time
            url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true&seed={int(time.time())}"
            
            logger.info(f"Pollinations URL: {url}")

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Pollinations returns the image bytes directly on GET
                response = await client.get(url)
                
                if response.status_code == 200:
                    # Return the image bytes
                    return True, response.content
                else:
                    return False, f"Pollinations Error {response.status_code}"

        except Exception as e:
            logger.error(f"Exception during image generation: {e}")
            return False, f"Exception: {str(e)}"
