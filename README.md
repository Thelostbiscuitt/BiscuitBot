
# Biscuit AI Assistant & Library Manager

A production-ready Telegram bot powered by Llama 3.3 (via Groq) with integrated Notion library management. Features intelligent conversation handling, smart message pagination, and automated book tracking.

## Features

- **AI Chat:** Interact with Llama 3.3 70B for advanced reasoning and coding assistance.
- **Smart Pagination:** Automatically splits long responses into navigable sections to avoid character limits.
- **Notion Integration:** Upload books directly to chat to automatically save metadata to your Notion library.
- **Conversation Memory:** Maintains context during sessions.
- **Modular Architecture:** Clean separation of concerns (API, Logic, Configuration).

## Tech Stack

- **Runtime:** Python 3.9+
- **Bot Framework:** `python-telegram-bot`
- **AI Model:** Groq API (Llama 3.3)
- **Integration:** Notion API
- **Deployment:** Render (Background Worker)

## Quick Start

### 1. Clone and Install
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
pip install -r requirements.txt
```

### 2. Configuration
Rename `.env.example` to `.env` and configure your environment variables.

| Variable Name | Description |
| :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather |
| `GROQ_API_KEY` | API key for Groq services |
| `NOTION_API_KEY` | Internal Integration Token from Notion |
| `NOTION_DATABASE_ID` | ID of your Notion Database |

### 3. Run the Bot
```bash
python main.py
```

## Commands

| Command | Description |
| :--- | :--- |
| `/start` | Initialize the bot and display the menu |
| `/help` | Display help information |
| `/models` | List active AI model details |
| `/history` | Show recent conversation history |
| `/clear` | Clear current conversation history |
| `/cancel` | Cancel any active operation (e.g., book upload) |
| `/stats` | View usage statistics and cost tracking |

## Deployment

This project is configured for deployment on **Render** as a **Background Worker**.

1.  Connect your GitHub repository to Render.
2.  Select **Background Worker** as the service type.
3.  Set the **Start Command** to `python main.py`.
4.  Add the environment variables listed in the Configuration section.

## Usage Notes

- **Notion Setup:** Ensure your Notion Database is connected to your integration and contains the required properties (Name, Author, Date Added, Status).
- **Long Messages:** Responses exceeding the character limit are handled via inline buttons for seamless reading.
- **Book Upload:** Simply upload a PDF file to the chat to trigger the saving workflow.

## License

This project is for personal use.
```
