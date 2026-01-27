"""
LLM Router for GLM 4.7 API
Handles GLM API calls with automatic cost tracking
"""

import logging
import json
import time
import hmac
import hashlib
import base64
from typing import List, Dict, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMRouter:
    """
    GLM 4.7 API integration with cost tracking
    """
    
    def __init__(self, config):
        self.config = config
        self.stats = {
            'total_requests': 0,
            'glm_calls': 0,
            'total_cost': 0.0,
            'glm_failures': 0
        }
        
        # Pricing (per 1M tokens - approximate)
        self.pricing = {
            'glm': {'input': 0.50, 'output': 1.00}  # Approximate
        }
    
    async def get_response(
        self,
        user_id: int,
        message: str,
        conversation_history: List[Dict]
    ) -> str:
        """
        Get response from GLM API
        
        Args:
            user_id: Telegram user ID
            message: User's message
            conversation_history: Previous messages
            
        Returns:
            LLM response text
        """
        self.stats['total_requests'] += 1
        
        # Call GLM API
        try:
            response = await self._call_glm(message, conversation_history)
            self.stats['glm_calls'] += 1
            return response
            
        except Exception as e:
            logger.error(f"GLM failed: {e}")
            self.stats['glm_failures'] += 1
            raise Exception("GLM API failed. Please try again later.")
    
    def _generate_glm_token(self) -> str:
        """
        Generate JWT token for ZhipuAI GLM API authentication
        
        The API key format is: id.secret
        We need to create a JWT token signed with the secret
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
        conversation_history: List[Dict]
    ) -> str:
        """
        Call GLM 4.7 API (ZhipuAI)
        
        Uses JWT token authentication
        """
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        
        # Prepare messages
        messages = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
        
        # Generate JWT token for authentication
        token = self._generate_glm_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "glm-4-flash",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            # Log response details for debugging
            logger.info(f"GLM API Status: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"GLM API Error: {error_text}")
                raise Exception(f"GLM API returned status {response.status_code}: {error_text}")
            
            data = response.json()
            
            # Extract response (adjust based on actual API format)
            content = data['choices'][0]['message']['content']
            
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
