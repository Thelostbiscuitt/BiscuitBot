#!/usr/bin/env python3
"""
Production-Ready Telegram Bot with Groq Llama 3.3 + Notion + Image Gen + PDF Text Extraction
Features: Pagination, Notion Book Upload/Retrieve, Image Generation, Full Command Support, PDF Reading, Smart Search.
"""

import os
import logging
import json
import asyncio
import fitz  # PyMuPDF for reading PDF text
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
    """Main Telegram Bot class with LLM, Pagination, Notion, Image Gen, and PDF Reading"""
    
    def __init__(self):
        self.config = Config()
        self.router = LLMRouter(self.config)
        
        # Initialize Notion Handler
        self.notion = NotionHandler(self.config.notion_api_key, self.config.notion_database_id)
        
        # Initialize Image Handler
        self.image_handler = ImageHandler(self.config.zai_api_key)
        
        self.conversations: Dict[int, List[Dict]] = {}
        self.paginated_messages: Dict[int, Dict] = {}
        self.book_upload_state: Dict[int, Dict] = {}
        
        # NEW: Store extracted book text in memory for RAG (Reading)
        # Structure: { "Book Title": "Full extracted text..." }
        self.book_library_content: Dict[str, str] = {}
    
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
            "I am **Biscuit**, your AI assistant.\n\n"
            "**Available Commands:**\n"
            "`/start` - Initialize bot\n"
            "`/help` - Display help\n"
            "`/image <prompt>` - Generate an image\n"
            "`/models` - List active model\n"
            "`/history` - Show conversation history\n"
            "`/clear` - Clear history\n"
            "`/cancel` - Cancel any operation\n\n"
            "**Features:**\n"
            "• Upload PDFs (I will read them!)\n"
            "• Ask questions about book content\n"
            "• Chat with Llama 3.3"
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display help information"""
        help_text = (
            "📚 **Help Guide**\n\n"
            "**Commands:**\n"
            "• `/image <prompt>` - Generate an AI image.\n"
            "• `/start` - Restart the session.\n"
            "• `/clear` - Wipe your conversation memory.\n\n"
            "**Reading Books:**\n"
            "Upload a PDF. I will extract the text.\n"
            "Ask: 'What does [Book Name] say about [Topic]?' or 'Find [Topic] in my books' and I will search the text for you."
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def image_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate an image"""
        if not self.config.zai_api_key:
            await update.message.reply_text("⚠️ Image generation is not configured (Missing API Key).")
            return

        if not context.args:
            await update.message.reply_text("Please provide a prompt.\n\nUsage: `/image A futuristic city at sunset`", parse_mode='Markdown')
            return
        
        prompt = " ".join(context.args)
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
        await update.message.reply_text(f"🎨 Generating image for: *{prompt}*...", parse_mode='Markdown')
        
        success, result = await self.image_handler.generate_image(prompt)
        
        if success:
            try:
                await update.message.reply_photo(photo=result, caption=f"✨ {prompt}")
            except Exception as e:
                logger.error(f"Failed to send photo: {e}")
                await update.message.reply_text("Image generated, but failed to send.")
        else:
            await update.message.reply_text(f"❌ Failed: {result}")

    async def models_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List models"""
        model_info = (
            "🤖 **Active Model Configuration**\n\n"
            "• **LLM Name:** Llama 3.3 70B Versatile\n"
            "• **LLM Provider:** Groq\n"
            "• **Image Gen:** Stability AI (SD3)\n\n"
            "Optimized for high speed and complex reasoning."
        )
        await update.message.reply_text(model_info, parse_mode='Markdown')

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show conversation history"""
        user_id = update.effective_user.id
        history = self.conversations.get(user_id, [])
        
        if not history:
            await update.message.reply_text("No conversation history found.")
            return
        
        recent_history = history[-10:]
        output = "🗂 **Recent History** (Last 10 messages):\n\n"
        
        for i, msg in enumerate(recent_history):
            role = msg['role'].upper()
            content = msg['content']
            display_content = content[:100] + "..." if len(content) > 100 else content
            output += f"*{role}:* {display_content}\n\n"
        
        chunks = self._split_text(output)
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode='Markdown')

    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear conversation history"""
        user_id = update.effective_user.id
        
        if user_id in self.conversations:
            del self.conversations[user_id]
        if user_id in self.paginated_messages:
            del self.paginated_messages[user_id]
            
        await update.message.reply_text("✅ Conversation history cleared.")
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the current book upload conversation."""
        user_id = update.effective_user.id
        
        if user_id in self.book_upload_state:
            del self.book_upload_state[user_id]
            await update.message.reply_text("❌ Book upload cancelled.")
        else:
            await update.message.reply_text("No active operation to cancel.")
            
        return ConversationHandler.END

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show usage statistics"""
        stats = self.router.get_stats()
        user_id = update.effective_user.id
        conversation_length = len(self.conversations.get(user_id, []))
        
        stats_message = (
            "📊 *Usage Stats*\n\n"
            f"Requests: {stats.get('total_requests', 0)}\n"
            f"LLM Calls: {stats.get('llm_calls', 0)}\n"
            f"Cost: ${stats.get('total_cost', 0.0):.4f}\n\n"
            f"Current Conv Length: {conversation_length} msgs"
        )
        await update.message.reply_text(stats_message, parse_mode='Markdown')

    # ================= BOOK UPLOAD LOGIC WITH TEXT EXTRACTION =================

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle PDF upload - Step 1: Download, Extract Text, Ask for Title"""
        user_id = update.effective_user.id
        document: Document = update.message.document
        
        if not self.notion.client:
            await update.message.reply_text("⚠️ Notion is not configured.")
            return

        try:
            await update.message.reply_text(f"📄 Received `{document.file_name}`. Extracting text... please wait...", parse_mode='Markdown')
            
            # 1. Download the file
            new_file = await document.get_file()
            file_bytes = await new_file.download_as_bytearray()
            
            # 2. Extract Text using PyMuPDF (fitz)
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            extracted_text = ""
            for page in doc:
                extracted_text += page.get_text()
            
            doc.close()
            
            logger.info(f"Extracted {len(extracted_text)} characters from PDF.")
            
            # Store extracted text in memory
            self.book_upload_state[user_id] = {
                'file_name': document.file_name,
                'file_id': document.file_id,
                'extracted_text': extracted_text
            }
            
            await update.message.reply_text(
                f"✅ Text extracted ({len(extracted_text)} chars).\n\n"
                "What is the **Title** of this book?",
                parse_mode='Markdown'
            )
            return WAITING_TITLE

        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            await update.message.reply_text("❌ Failed to read the PDF. It might be an image-based PDF (scanned).")
            return

    async def book_title_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Step 2: Receive Title, Ask for Author"""
        user_id = update.effective_user.id
        title = update.message.text
        
        if user_id not in self.book_upload_state:
            await update.message.reply_text("Something went wrong. Please upload the file again.")
            return ConversationHandler.END
        
        self.book_upload_state[user_id]['title'] = title
        
        await update.message.reply_text(
            f"Got it! Title: *{title}*\n\n"
            "Who is the **Author**?",
            parse_mode='Markdown'
        )
        return WAITING_AUTHOR

    async def book_author_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Step 3: Receive Author, Save to Notion, Store Text in Memory"""
        user_id = update.effective_user.id
        author = update.message.text
        
        if user_id not in self.book_upload_state:
            return ConversationHandler.END
        
        title = self.book_upload_state[user_id].get('title', 'Unknown')
        
        # Save metadata to Notion
        success = self.notion.add_book(title, author)
        
        if success:
            # IMPORTANT: Save the extracted text to the library so the bot can read it
            extracted_text = self.book_upload_state[user_id]['extracted_text']
            self.book_library_content[title] = extracted_text
            
            await update.message.reply_text(
                f"✅ **Saved to Notion and Added to Brain!**\n\n"
                f"📖 *{title}*\n"
                f"✍️ by {author}\n\n"
                f"You can now ask me questions about this book's content.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Failed to save to Notion. Check logs.")
        
        del self.book_upload_state[user_id]
        return ConversationHandler.END

    # ================= CHAT LOGIC WITH SMART TEXT SEARCH =================

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages with Smart RAG (Keyword Search in Extracted Text)"""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        logger.info(f"User {user_id} sent: {message_text[:50]}...")
        
        user_name = user.first_name if user.first_name else (user.username if user.username else None)
        
        # --- SMART BOOK SEARCH ---
        relevant_snippet = ""
        
        # 1. Check if the user is asking about books generally
        if "book" in message_text.lower() or "notion" in message_text.lower() or "library" in message_text.lower():
            
            # 2. Strategy: Check if a specific book is mentioned
            specific_book_found = False
            matched_book_title = ""
            
            for title in self.book_library_content.keys():
                if title.lower() in message_text.lower() or message_text.lower() in title.lower():
                    specific_book_found = True
                    matched_book_title = title
                    break
            
            # 3. If no specific book is mentioned, search ALL books for keywords
            search_keywords = [w for w in message_text.split() if len(w) > 3]
            best_snippet = ""
            highest_score = 0

            if not specific_book_found:
                # Search across the entire library
                for title, content in self.book_library_content.items():
                    # Split content into paragraphs
                    paragraphs = content.split('\n\n')
                    for para in paragraphs:
                        score = 0
                        # Score based on keyword matches in this paragraph
                        for word in search_keywords:
                            if word.lower() in para.lower():
                                score += 1
                        
                        # If this paragraph has keywords and is a good length, consider it
                        if score > 0 and len(para) > 50 and len(para) < 1500:
                            if score > highest_score:
                                highest_score = score
                                best_snippet = f"From the book '{title}':\n\n{para}"
            else:
                # Search specifically the matched book
                content = self.book_library_content[matched_book_title]
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    score = 0
                    for word in search_keywords:
                        if word.lower() in para.lower():
                            score += 1
                    if score > 0 and len(para) > 50 and len(para) < 1500:
                        if score > highest_score:
                            highest_score = score
                            best_snippet = f"From the book '{matched_book_title}':\n\n{para}"

            if best_snippet:
                relevant_snippet = best_snippet

        if relevant_snippet:
            # Inject the found text into the prompt
            message_text = (
                f"Based on the following text from your books:\n\n"
                f"{relevant_snippet}\n\n"
                f"User Question: {message_text}\n\n"
                f"Please answer the question using ONLY the provided text. If the answer is not there, say 'I couldn't find that specific detail in the book.'"
            )
        
        # ---------------------------------------

        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({"role": "user", "content": message_text})
        
        try:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            response = await self.router.get_response(
                user_id=user_id,
                message=message_text,
                conversation_history=self.conversations[user_id],
                user_name=user_name
            )
            
            formatted_response = self._format_response(response)
            
            self.conversations[user_id].append({"role": "assistant", "content": formatted_response})
            if len(self.conversations[user_id]) > 20:
                self.conversations[user_id] = self.conversations[user_id][-20:]

            chunks = self._split_text(formatted_response)
            
            if len(chunks) == 1:
                try:
                    await update.message.reply_text(chunks[0], parse_mode='Markdown')
                except BadRequest:
                    await update.message.reply_text(chunks[0])
            else:
                self.paginated_messages[user_id] = {
                    'chunks': chunks,
                    'page': 0
                }
                
                keyboard = [[InlineKeyboardButton("Read More > (1/{})".format(len(chunks)), callback_data=f"next_{user_id}_1")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                try:
                    await update.message.reply_text(chunks[0], parse_mode='Markdown', reply_markup=reply_markup)
                except BadRequest:
                    await update.message.reply_text(chunks[0], reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await update.message.reply_text("❌ Sorry, something went wrong.")

    async def pagination_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle pagination clicks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        try:
            action, uid_str, page_str = query.data.split('_')
            target_user_id = int(uid_str)
            target_page = int(page_str)
        except ValueError:
            return

        if user_id != target_user_id:
            return

        if user_id not in self.paginated_messages:
            await query.edit_message_text("This message has expired.")
            return

        data = self.paginated_messages[user_id]
        chunks = data['chunks']
        total_pages = len(chunks)
        data['page'] = target_page
        
        keyboard = []
        buttons = []
        
        if target_page > 0:
            buttons.append(InlineKeyboardButton("< Prev", callback_data=f"prev_{user_id}_{target_page - 1}"))
        
        if target_page < total_pages - 1:
            buttons.append(InlineKeyboardButton(f"Next > ({target_page + 1}/{total_pages})", callback_data=f"next_{user_id}_{target_page + 1}"))
        else:
            if total_pages > 1:
                 buttons.append(InlineKeyboardButton("<< Start", callback_data=f"prev_{user_id}_0"))
        
        if buttons:
            keyboard.append(buttons)
            
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        try:
            await query.edit_message_text(
                text=chunks[target_page],
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except BadRequest:
            try:
                await query.edit_message_text(
                    text=chunks[target_page],
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error editing message: {e}")

    def run(self):
        """Start the bot"""
        logger.info("Starting bot with LLM, Notion, Image Gen, and PDF Text Extraction (Smart Search)...")
        
        application = Application.builder().token(self.config.telegram_token).build()
        
        # Book Upload Conversation Handler
        book_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Document.PDF, self.handle_document)],
            states={
                WAITING_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.book_title_received)],
                WAITING_AUTHOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.book_author_received)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
        )
        
        # Register Handlers
        application.add_handler(book_conv_handler)
        
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("image", self.image_command))
        application.add_handler(CommandHandler("models", self.models_command))
        application.add_handler(CommandHandler("history", self.history_command))
        application.add_handler(CommandHandler("clear", self.clear_command))
        application.add_handler(CommandHandler("cancel", self.cancel_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        
        application.add_handler(CallbackQueryHandler(self.pagination_callback, pattern="^(next|prev)_"))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Bot is running...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
