import logging
import httpx

logger = logging.getLogger(__name__)

class ImageHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        # CORRECTED URL: This is the standard Zero1/Z.AI endpoint
        self.base_url = "https://api.zero1.ai/v1/images/generations"
        self.model = "flux-v1.1-pro" 

    async def generate_image(self, prompt: str):
        """
        Generates an image using Z.AI (Zero1) API.
        Returns the image URL or None if failed.
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
                
                if response.status_code != 200:
                    logger.error(f"Z.AI API Error: {response.status_code} - {response.text}")
                    return None
                
                data = response.json()
                
                # Z.AI/Zero1 uses the standard OpenAI response format
                if 'data' in data and len(data['data']) > 0:
                    return data['data'][0]['url']
                else:
                    logger.error("No image data in Z.AI response.")
                    return None

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None
