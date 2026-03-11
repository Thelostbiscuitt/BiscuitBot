"""
LLM Router for Llama 3.3 70B Versatile (via Groq API)
Handles API calls with automatic cost tracking
"""

import logging
import json
import httpx
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class LLMRouter:
    """
    Llama 3.3 API integration (via Groq) with cost tracking
    """
    
    def __init__(self, config):
        self.config = config
        self.stats = {
            'total_requests': 0,
            'llm_calls': 0,
            'total_cost': 0.0,
            'llm_failures': 0
        }
        
        # Pricing (per 1M tokens - approximate for Groq Llama 3.3)
        # Note: Groq pricing changes, check https://console.groq.com/docs/rate-limits
        self.pricing = {
            'llama': {'input': 0.59, 'output': 0.79}  
        }
    
    async def get_response(
        self,
        user_id: int,
        message: str,
        conversation_history: List[Dict],
        user_name: Optional[str] = None
    ) -> str:
        """
        Get response from Llama API
        
        Args:
            user_id: Telegram user ID
            message: User's message
            conversation_history: Previous messages
            user_name: User's display name for personalization
            
        Returns:
            LLM response text
        """
        self.stats['total_requests'] += 1
        
        try:
            # Updated to call Groq/Llama instead of GLM
            response = await self._call_llama(message, conversation_history, user_name)
            self.stats['llm_calls'] += 1
            return response
            
        except Exception as e:
            logger.error(f"LLM failed: {e}")
            self.stats['llm_failures'] += 1
            raise Exception("LLM API failed. Please try again later.")
    
    async def _call_llama(
        self,
        message: str,
        conversation_history: List[Dict],
        user_name: Optional[str] = None
    ) -> str:
        """
        Call Llama 3.3 API (via Groq)
        
        Uses standard Bearer token authentication
        """
        # Using Groq's OpenAI-compatible endpoint
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Prepare messages with system prompt
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
        
        # Add personalization if user name is provided
        if user_name:
            system_prompt += f"\n\nYou are speaking with {user_name}. Address them by name when appropriate to create a more personalized conversation experience."
        
        # Add system prompt at the beginning
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        messages.extend(conversation_history[-10:] if len(conversation_history) > 10 else conversation_history)
        
        # Updated Model ID
        model_id = "llama-3.3-70b-versatile"
        
        headers = {
            "Authorization": f"Bearer {self.config.groq_api_key}", 
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            logger.info(f"LLM API Status: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"LLM API Error: {error_text}")
                raise Exception(f"LLM API returned status {response.status_code}: {error_text}")
            
            data = response.json()
            
            # Extract response
            content = data['choices'][0]['message']['content']
            
            # Track costs
            usage = data.get('usage', {})
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            
            cost = self._calculate_cost('llama', input_tokens, output_tokens)
            self.stats['total_cost'] += cost
            
            logger.info(
                f"LLM: {input_tokens} in, {output_tokens} out, "
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
    
    def get
