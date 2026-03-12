"""
Configuration management for Telegram Bot
Loads API keys from environment variables
"""

import os
import logging
from dotenv import load_dotenv

# Set up logging to see warnings if keys are missing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file (for local testing)
# On Render, these variables are injected automatically
load_dotenv()


class Config:
    """Configuration class for bot settings"""
    
    def __init__(self):
        # --- CRITICAL: Telegram Bot Token ---
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        # --- CRITICAL: Groq API Key (for Llama 3.3) ---
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        # --- OPTIONAL: Notion Integration (Book Uploads) ---
        self.notion_api_key = os.getenv('NOTION_API_KEY')
        self.notion_database_id = os.getenv('NOTION_DATABASE_ID')
        
        if not self.notion_api_key or not self.notion_database_id:
            logger.warning(
                "NOTION_API_KEY or NOTION_DATABASE_ID not found. "
                "Book upload feature will be disabled."
            )
        
        # --- Bot Settings ---
        
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
        
        self.max_conversation_length = int(os.getenv('MAX_CONVERSATION_LENGTH', '20'))
        self.max_tokens = int(os.getenv('MAX_TOKENS', '2000'))
        self.temperature = float(os.getenv('TEMPERATURE', '0.7'))
    
    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized to use the bot"""
        if self.authorized_users is None:
            return True
        return user_id in self.authorized_users
