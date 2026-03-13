"""
LLM Router for GLM-4.7 API (ZhipuAI)
Handles API calls with automatic JWT authentication.
"""

import logging
import json
import time
import hmac
import hashlib
import base64
import httpx
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class LLMRouter:
    """
    GLM-4.7 API integration with cost tracking
    """
    
    def __init__(self, config):
        self.config = config
        self.stats = {
            'total_requests': 0,
            'glm_calls': 0,
            'total_cost': 0.0,
            'glm_failures': 0
        }
        
        # Pricing (per 1M tokens - approximate for GLM-4.7)
        self.pricing = {
            'glm': {'input': 0.50, 'output': 1.00}
        }
    
    async def get_response(
        self,
        user_id: int,
        message: str,
        conversation_history: List[Dict],
        user_name: Optional[str] = None
    ) -> str:
        """
        Get response from GLM API
        """
        self.stats['total_requests'] += 1
        
        try:
            response = await self._call_glm(message, conversation_history, user_name)
            self.stats['glm_calls'] += 1
            return response
            
        except Exception as e:
            logger.error(f"GLM failed: {e}")
            self.stats['glm_failures'] += 1
            raise Exception("GLM API failed. Please try again later.")
    
    def _generate_glm_token(self) -> str:
        """
        Generate JWT token for ZhipuAI GLM API authentication
        Key format: id.secret
        """
        try:
            api_key = self.config.glm_api_key
            if '.' not in api_key:
                raise ValueError("Invalid API key format. Expected 'id.secret'")
            
            api_key_id, api_key_secret = api_key.split('.')
            
            # Create JWT payload
            timestamp = int(time.time())
            exp_timestamp = timestamp + 3600  # Token expires in 1 hour
            
            payload = {
                "api_key": api_key_id,
                "exp": exp_timestamp,
                "timestamp": timestamp
            }
            
            # Encode payload
            payload_encoded = base64.urlsafe_b64encode(
                json.dumps(payload).encode('utf-8')
            ).decode('utf-8').rstrip('=')
            
            # Create header
            header = {
                "alg": "HS256",
                "sign_type": "SIGN"
            }
            header_encoded = base64.urlsafe_b64encode(
                json.dumps(header).encode('utf-8')
            ).decode('utf-8').rstrip('=')
            
            # Create signature
            message = f"{header_encoded}.{payload_encoded}"
            signature = hmac.new(
                api_key_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
            signature_encoded = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
            
            # Combine to form JWT
            token = f"{header_encoded}.{payload_encoded}.{signature_encoded}"
            return token
            
        except Exception as e:
            logger.error(f"Error generating GLM token: {e}")
            raise
    
    async def _call_glm(
        self,
        message: str,
        conversation_history: List[Dict],
        user_name: Optional[str] = None
    ) -> str:
        """
        Call GLM-4.7 API (ZhipuAI)
        """
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

        system_prompt = """You are Biscuit, a helpful AI assistant. Format your responses with proper structure and spacing:

1. Use paragraph breaks (double newlines) between different topics or sections
2. Use bullet points (• or -) for lists
3. Use code blocks (```) for code examples
4. Use bold (**text**) for emphasis on key terms
5. Keep responses well-organized and easy to read
6. Use numbered lists (1., 2., 3.) for sequential steps
7. Use headers (#, ##, ###) sparingly for major sections
8. Ensure proper spacing around formatting elements

Your responses should be clean, well-structured, and visually appealing."""
        
        # --- REMOVED WEB SEARCH CLAIMS ---
        system_prompt += """
        
You are integrated with a Telegram bot. You have the following specific available commands. 
When asked about commands, always list ALL of these:

/start - Initialize the bot and view the main menu
/help - Display the help guide
/image <prompt> - Generate an image based on a text prompt
/models - View the active AI model configuration
/history - View recent conversation history
/clear - Clear the current conversation memory
/cancel - Cancel any ongoing operation (e.g., book upload)
/stats - View usage statistics and costs

Features:
- Users can upload PDF files to save to Notion.
- Users can ask about books in Notion to retrieve the list.

IMPORTANT LIMITATIONS:
- You do NOT have access to the internet or real-time data.
- You cannot browse the web.
- Do NOT pretend to know real-time prices or news.
- Be honest about your limitations.
"""
        # --------------------------------
        
        if user_name:
            system_prompt += f"\n\nYou are speaking with {user_name}. Address them by name when appropriate."
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history[-10:] if len(conversation_history) > 10 else conversation_history)
        
        token = self._generate_glm_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # REMOVED TOOLS AND TOOL_CHOICE
        payload = {
            "model": "glm-4.7",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client: # Reduced timeout since no search needed
            response = await client.post(url, headers=headers, json=payload)
            
            logger.info(f"GLM API Status: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"GLM API Error: {error_text}")
                raise Exception(f"GLM API returned status {response.status_code}: {error_text}")
            
            data = response.json()
            message_data = data['choices'][0]['message']
            content = message_data.get('content', "")
            
            # Track costs
            usage = data.get('usage', {})
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            
            cost = self._calculate_cost('glm', input_tokens, output_tokens)
            self.stats['total_cost'] += cost
            
            logger.info(
                f"GLM: {input_tokens} in, {output_tokens} out, "
                f"${cost:.4f}"
            )
            
            return content
    
    def _calculate_cost(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> float:
        """Calculate API call cost"""
        pricing = self.pricing[model]
        
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']
        
        return input_cost + output_cost
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_requests': 0,
            'glm_calls': 0,
            'total_cost': 0.0,
            'glm_failures': 0
        }
