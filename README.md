# Biscuit AI Assistant

A production-ready Telegram bot that combines advanced LLM capabilities, Notion integration, and image generation. It features a "read-then-query" engine that extracts text from uploaded PDFs, allowing users to interact with their personal library via natural language.

# Features

- **AI Chat:** Powered by high-speed LLMs for context-aware conversation, coding assistance, and analysis.
- **Intelligent Notion Integration:**
    - **PDF Ingestion:** Upload a PDF, and the bot automatically extracts and indexes the text.
    - **Content Querying:** Ask questions about the content of your uploaded books, and the bot retrieves relevant paragraphs to answer accurately.
    - **Library Management:** Save metadata (Title, Author) directly to your Notion database.
- **Image Generation:** Create visuals directly within the chat using integrated generation APIs.
- **Conversation Management:** Smart pagination for long responses, memory management, and chat history.

# Tech Stack

- **Runtime:** Python 3.9+
- **Bot Framework:** `python-telegram-bot`
- **LLM Provider:** Groq (Llama 3.3 70B)
- **Image Provider:** Stability AI
- **Integration:** Notion API
- **PDF Processing:** PyMuPDF (fitz)
- **Deployment:** Render (Background Worker)

# Getting Started

# 1. Prerequisites

- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather)).
- An API Key for Groq (for chat).
- An API Key for Stability AI (for images).
- A Notion Integration Token and Database ID (for library management).

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
pip install -r requirements.txt
```

# 3. Configuration

The bot relies on environment variables for security. Create a `.env` file locally or configure them in your deployment dashboard.

| Variable Name | Description |
| :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Your bot token from Telegram. |
| `GROQ_API_KEY` | API key for the LLM provider. |
| `STABILITY_API_KEY` | API key for image generation. |
| `NOTION_API_KEY` | Internal Integration Token for Notion. |
| `NOTION_DATABASE_ID` | ID of your Notion Database. |

# 4. Running the Bot

To run the bot locally:

```bash
python main.py
```

# Usage

# Commands

- `/start` - Initialize the bot and view the main menu.
- `/image <prompt>` - Generate an image based on a text prompt.
- `/models` - View active model configurations.
- `/history` - View recent conversation history.
- `/clear` - Clear the current conversation memory.
- `/stats` - View usage statistics and costs.

# Interactions

- **Chat:** Simply send a message to start a conversation. Long responses are paginated automatically.
- **Uploading Books:**
    1.  Upload a PDF file to the chat.
    2.  The bot will extract the text and ask for the Title and Author.
    3.  The metadata is saved to Notion, and the text is stored in memory.
- **Querying Books:** Ask questions like *"What does [Book Name] say about [Topic]?"* or *"Find color sets involving red."* The bot will search the extracted text and answer based on the book's content.

# Deployment

This project is configured for deployment on **Render** as a **Background Worker**.

1.  Connect your GitHub repository to Render.
2.  Select **Background Worker** as the service type.
3.  **Build Command:** `pip install -r requirements.txt`
4.  **Start Command:** `python main.py`
5.  **Environment Variables:** Add the variables listed in the Configuration section.
6.  Deploy.

# Project Structure

The project is modular, separating concerns for easier maintenance.

```text
.
├── main.py              # Application entry point and bot logic.
├── config.py            # Configuration and environment variable loading.
├── llm_router.py        # Handles API communication with the LLM.
├── notion_handler.py     # Manages Notion database interactions.
├── image_handler.py     # Manages image generation API requests.
├── requirements.txt     # Project dependencies.
└── README.md            # This file.
```

# License

This project is for personal use.
```
