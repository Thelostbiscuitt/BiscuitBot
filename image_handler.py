import logging
import httpx

logger = logging.getLogger(__name__)

class ImageHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        # CORRECTED URL for z-image.ai
        self.base_url = "https://api.z-image.ai/v1/images/generations"
        
        # Common model name for Flux on this platform
        self.model = "flux" 

    async def generate_image(self, prompt: str):
        """
        Generates an image using z-image.ai API.
        """
        if not self.api_key:
            logger.error("Z.AI API Key not configured.")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.base_url, headers=headers, json=payload)
                
                # Logging for debugging
                logger.info(f"Z-Image Status Code: {response.status_code}")
                logger.info(f"Z-Image Response Body: {response.text}")
                
                if response.status_code != 200:
                    logger.error(f"Z-Image API Request Failed. Details: {response.text}")
                    return None
                
                data = response.json()
                
                if 'data' in data and len(data['data']) > 0:
                    return data['data'][0]['url']
                else:
                    logger.error(f"No image URL found in response. Data: {data}")
                    return None

        except Exception as e:
            logger.error(f"Exception during image generation: {e}")
            return None
