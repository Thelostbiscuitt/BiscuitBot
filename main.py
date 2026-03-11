#!/usr/bin/env python3
"""
Production-Ready Telegram Bot with Groq Llama 3.3 API Integration
Designed for Render deployment

Features:
- Llama 3.3 70B Versatile API integration (via Groq)
- Cost tracking
- Conversation history management
- Error logging
"""

import os
import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# IMPORTS FROM OTHER FILES
from llm_router import LLMRouter
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Main Telegram Bot class with LLM integration"""
    
    def __init__(self):
        self.config = Config()
        self.router = LLMRouter(self.config)
        self.conversations: Dict[int, List[Dict]] = {}
    
    def _format_response(self, response: str) -> str:
        """
        Post-process LLM response to ensure proper formatting and spacing.
        """
        # Ensure consistent line endings
        response = response.replace('\r\n', '\n').replace('\r', '\n')
        
        # Ensure double newlines between paragraphs
        response = '\n\n'.join(
            para.strip() for para in response.split('\n\n') if para.strip()
        )
        
        # Ensure single newlines within paragraphs are preserved
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
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        logger.info(f"User {user.id} started the bot")
        
        user_name = user.first_name if user.first_name else (user.username if user.username else "there")
        
        welcome_message = (
            f"👋 Hello {user_name}!\n\n"
            "Biscuit is online and ready to assist.\n\n"
            "What I can do:\n"
            "• General chat and conversation\n"
            "• Coding assistance\n"
            "• Deep analysis and explanations\n\n"
            "Commands:\n"
            "`/start` - Show menu\n"
            "`/clear` - Clear history\n"
            "`/stats` - View stats\n"
            "`/help` - Get help\n\n"
            "Powered by Llama 3.3 (Groq)"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🤖 *Bot Capabilities*\n\n"
            "*General Chat:* Just talk to me naturally\n"
            "*Coding Help:* Ask programming questions\n"
            "*Analysis:* Request deep analysis on topics\n\n"
            "*Technical Details:*\n"
            "• Powered by Llama 3.3 (Groq)\n"
            "• Conversation memory per user\n"
            "• Cost tracking\n"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear conversation history"""
        user_id = update.effective_user.id
        
        if user_id in self.conversations:
            del self.conversations[user_id]
            await update.message.reply_text("✅ Conversation history cleared!")
        else:
            await update.message.reply_text("No conversation history to clear.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show usage statistics"""
        stats = self.router.get_stats()
        user_id = update.effective_user.id
        conversation_length = len(self.conversations.get(user_id, []))
        
        # Use .get() for safer dictionary access
        stats_message = (
            "📊 *Usage Statistics*\n\n"
            f"*Total Requests:* {stats.get('total_requests', 0)}\n"
            f"*Llama Calls:* {stats.get('llm_calls', 0)}\n"
            f"*Total Cost:* ${stats.get('total_cost', 0.0):.4f}\n\n"
            f"*Your Conversation:* {conversation_length} messages"
        )
        
        await update.message.reply_text(stats_message, parse_mode='Markdown')
        async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        logger.info(f"User {user_id} sent: {message_text[:50]}...")
        
        # Get user's display name for personalization
        user_name = user.first_name if user.first_name else (user.username if user.username else None)
        
        # Initialize conversation history if needed
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        # Add user message to history
        self.conversations[user_id].append({
            "role": "user",
            "content": message_text
        })
        
        try:
            # Send typing indicator
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="typing"
            )
            
            # Get response from LLM router
            response = await self.router.get_response(
                user_id=user_id,
                message=message_text,
                conversation_history=self.conversations[user_id],
                user_name=user_name
            )
            
            # Post-process response for proper formatting
            formatted_response = self._format_response(response)
            
            # --- NEW SPLITTING LOGIC START ---
            # Telegram limit is 4096 chars. We split if it's longer.
            MAX_MESSAGE_LENGTH = 4096
            current_text = formatted_response

            while len(current_text) > 0:
                # Determine the chunk size
                chunk = current_text[:MAX_MESSAGE_LENGTH]
                
                # If there is more text remaining, try to split at a newline
                # to avoid cutting words or code blocks in half.
                if len(current_text) > MAX_MESSAGE_LENGTH:
                    # Find the last newline within the chunk
                    last_newline_index = chunk.rfind('\n')
                    
                    # If a newline is found reasonably far back (e.g., last 20% of the chunk), split there
                    if last_newline_index > MAX_MESSAGE_LENGTH * 0.8:
                        chunk = chunk[:last_newline_index + 1]
                        current_text = current_text[len(chunk):]
                    else:
                        # No good newline found, just split at the max length
                        current_text = current_text[MAX_MESSAGE_LENGTH:]
                else:
                    # This is the last chunk
                    current_text = ""

                # Send the chunk
                await update.message.reply_text(chunk, parse_mode='Markdown')
                
                # Sleep briefly to avoid rate limits if there are more chunks to send
                if len(current_text) > 0:
                    await asyncio.sleep(0.5)
            # --- NEW SPLITTING LOGIC END ---
            
            # Add the FULL assistant response to history (not just the chunk)
            self.conversations[user_id].append({
                "role": "assistant",
                "content": formatted_response
            })
            
            # Keep conversation history manageable (last 20 messages)
            if len(self.conversations[user_id]) > 20:
                self.conversations[user_id] = self.conversations[user_id][-20:]
            
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Sorry, I encountered an error processing your message. "
                "Please try again or contact the administrator."
            )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling update: {context.error}", exc_info=context.error)
        
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "An unexpected error occurred. The issue has been logged."
            )
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Telegram bot...")
        
        application = Application.builder().token(self.config.telegram_token).build()
        
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("clear", self.clear_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_error_handler(self.error_handler)
        
        logger.info("Bot is running...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()

