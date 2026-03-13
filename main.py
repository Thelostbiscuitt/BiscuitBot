#!/usr/bin/env python3
"""
Production-Ready Telegram Bot with GLM-4.7 + Notion + Image Gen
Features: Pagination, Notion Book Upload/Retrieve, Image Generation, Full Command Support.
"""

import os
import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Document
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from llm_router import LLMRouter
from config import Config
from notion_handler import NotionHandler
from image_handler import ImageHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation States for Book Upload
WAITING_TITLE = 1
WAITING_AUTHOR = 2

class TelegramBot:
    """Main Telegram Bot class with LLM, Pagination, Notion, and Image Gen"""
    
    def __init__(self):
        self.config = Config()
        self.router = LLMRouter(self.config)
        
        # Initialize Notion Handler
        self.notion = NotionHandler(self.config.notion_api_key, self.config.notion_database_id)
        
        # Initialize Image Handler
        self.image_handler = ImageHandler(self.config.zai_api_key)
        
        self.conversations: Dict[int, List[Dict]] = {}
        self.paginated_messages: Dict[int, Dict] = {}
        
        # State for uploading books: { user_id: { 'file_name': 'book.pdf' } }
        self.book_upload_state: Dict[int, Dict] = {}
    
    def _format_response(self, response: str) -> str:
        """Post-process LLM response for formatting."""
        response = response.replace('\r\n', '\n').replace('\r', '\n')
        response = '\n\n'.join(
            para.strip() for para in response.split('\n\n') if para.strip()
        )
        
        lines = response.split('\n')
        formatted_lines = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                formatted_lines.append(line)
                if not in_code_block and i < len(lines) - 1:
                    formatted_lines.append('')
                continue
            
            if line.strip().startswith('#') and i > 0:
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')
            
            formatted_lines.append(line)
        
        response = '\n'.join(formatted_lines)
        response = response.rstrip()
        return response

    def _split_text(self, text: str, limit: int = 3500) -> List[str]:
        """Splits text into chunks."""
        if len(text) <= limit:
            return [text]
            
        chunks = []
        current_chunk = ""
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 1 > limit:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n"
            else:
                current_chunk += paragraph + "\n"
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        final_chunks = []
        for chunk in chunks:
            while len(chunk) > limit:
                split_point = chunk.rfind(' ', 0, limit)
                if split_point == -1: split_point = limit
                final_chunks.append(chunk[:split_point])
                chunk = chunk[split_point:].lstrip()
            final_chunks.append(chunk)
            
        return final_chunks

    # ================= COMMANDS =================

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Initialize bot and show menu"""
        user = update.effective_user
        user_name = user.first_name if user.first_name else "there"
        
        welcome_message = (
            f"👋 Hello {user_name}!\n\n"
            "I am **Biscuit**,
