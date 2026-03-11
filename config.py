"""
Configuration management for Telegram Bot
Loads API keys from environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local testing)
# On Render, these variables are injected automatically
load_dotenv()


class Config:
    """Configuration class for bot settings"""
    
    def __init__(self):
        # Telegram Bot Token
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        # Groq API Key (for Llama 3.3 70B Versatile)
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        # Optional: Authorized user IDs (for access control)
        authorized_users = os.getenv('AUTHORIZED_USERS', '')
        if authorized_users:
            self.authorized_users = [
                int(uid.strip()) 
                for uid in authorized_users.split(',') 
                if uid.strip()
            ]
        else:
            self.authorized_users = None  # Allow all users
        
        # Bot settings
        self.max_conversation_length = int(os.getenv('MAX_CONVERSATION_LENGTH', '20'))
        self.max_tokens = int(os.getenv('MAX_TOKENS', '2000'))
        self.temperature = float(os.getenv('TEMPERATURE', '0.7'))
    
    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized to use the bot"""
        if self.authorized_users is None:
            return True
        return user_id in self.authorized_users
