import logging
import httpx

logger = logging.getLogger(__name__)

class ImageHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        # CHANGED: Pointing to Creem's API based on the Attribution page
        self.base_url = "https://api.creem.io/v1/images/generations"
        
    async def generate_image(self, prompt: str):
        """
        Generates an image using Z-Image (Creem) API.
        Returns: (Success: bool, Data: url_or_error_message)
        """
        if not self.api_key:
            return False, "Z.AI API Key not configured."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # CHANGED: Using the specific model name "Z-Image-Turbo" mentioned in your text
        payload = {
            "model": "Z-Image-Turbo",
            "prompt": prompt,
            "n": 1,
            # Adding size parameter to ensure standard behavior
            "size": "1024x1024" 
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.base_url, headers=headers, json=payload)
                
                logger.info(f"Creem API Status Code: {response.status_code}")
                logger.info(f"Creem API Response Body: {response.text}")
                
                if response.status_code != 200:
                    error_detail = response.text
                    return False, f"API Error {response.status_code}: {error_detail}"
                
                data = response.json()
                
                if 'data' in data and len(data['data']) > 0:
                    return True, data['data'][0]['url']
                else:
                    return False, f"API Success but no image data. Response: {data}"

        except Exception as e:
            logger.error(f"Exception during image generation: {e}")
            return False, f"Exception: {str(e)}"
