"""
LLM Router for GLM 4.7 API
Handles GLM API calls with automatic cost tracking
"""

import logging
import json
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
    
    async def _call_glm(
        self, 
        message: str, 
        conversation_history: List[Dict]
    ) -> str:
        """
        Call GLM 4.7 API (ZhipuAI)
        
        Note: GLM API format may differ - adjust as needed
        """
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        
        # Prepare messages
        messages = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
        
        headers = {
            "Authorization": f"Bearer {self.config.glm_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "glm-4",  # or "glm-4-air" for faster responses
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
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
