#!/usr/bin/env python3
"""
Production-Ready Telegram Bot with GLM API Integration
Designed for Railway deployment

Features:
- GLM 4.7 API integration
- Cost tracking
- Conversation history management
- Error logging
"""

import os
import logging
import json
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
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        logger.info(f"User {user.id} started the bot")
        
        welcome_message = (
            "👋 Hello Doom!\\n\\n"
            "Biscuit is online and ready to assist.\\n\\n"
            "🚀 Features\\n"
            "• GLM 4.7 API Integration\\n"
            "• Conversation Memory\\n"
            "• Usage & Cost Tracking\\n\\n"
            "🛠️ Capabilities:\\n"
            "• 💬 General Chat\\n"
            "• 💻 Coding Help\\n"
            "• 📊 Deep Analysis\\n\\n"
            "⌨️ Commands:\\n"
            "`/start` - Show this menu\\n"
            "`/clear` - Clear history\\n"
            "`/stats` - View statistics\\n"
            "`/help` - Get help\\n\\n"
            "━━━━━━━━━━━\\n"
            "💾 *System Status: GLM 4.7*"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🤖 *Bot Capabilities*\\n\\n"
            "*General Chat:* Just talk to me naturally\\n"
            "*Coding Help:* Ask programming questions\\n"
            "*Analysis:* Request deep analysis on topics\\n\\n"
            "*Technical Details:*\\n"
            "• Powered by GLM 4.7 API\\n"
            "• Conversation memory per user\\n"
            "• Cost tracking\\n"
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
        
        stats_message = (
            "📊 *Usage Statistics*\\n\\n"
            f"*Total Requests:* {stats['total_requests']}\\n"
            f"*GLM Calls:* {stats['glm_calls']}\\n"
            f"*Total Cost:* ${stats['total_cost']:.4f}\\n\\n"
            f"*Your Conversation:* {conversation_length} messages"
        )
        
        await update.message.reply_text(stats_message, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        logger.info(f"User {user_id} sent: {message_text[:50]}...")
        
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
                conversation_history=self.conversations[user_id]
            )
            
            # Add assistant response to history
            self.conversations[user_id].append({
                "role": "assistant",
                "content": response
            })
            
            # Keep conversation history manageable (last 20 messages)
            if len(self.conversations[user_id]) > 20:
                self.conversations[user_id] = self.conversations[user_id][-20:]
            
            # Send response
            await update.message.reply_text(response)
            
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
        
        # Create application
        application = Application.builder().token(self.config.telegram_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("clear", self.clear_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Add error handler
        application.add_error_handler(self.error_handler)
        
        # Start bot
        logger.info("Bot is running...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
