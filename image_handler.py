import logging
import httpx

logger = logging.getLogger(__name__)

class ImageHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.z-image.ai/v1/images/generations"
        
    async def generate_image(self, prompt: str):
        """
        Generates an image using z-image.ai API.
        Returns: (Success: bool, Data: url_or_error_message)
        """
        if not self.api_key:
            return False, "Z.AI API Key not configured."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Simplified payload: Let the API decide the default model/size
        payload = {
            "prompt": prompt,
            "n": 1
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.base_url, headers=headers, json=payload)
                
                logger.info(f"Z-Image Status Code: {response.status_code}")
                logger.info(f"Z-Image Response Body: {response.text}")
                
                if response.status_code != 200:
                    # Return the specific error message
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
