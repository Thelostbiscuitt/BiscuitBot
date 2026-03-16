# Biscuit AI Assistant

A production-ready Telegram bot powered by GLM-4.7 (ZhipuAI), featuring intelligent conversation management, Notion integration, and automated image generation.

## Features

- **Intelligent Chat:** Powered by GLM-4.7 with Web Search capabilities for real-time information.
- **Notion Library:** Upload PDF metadata directly to your Notion database.
- **Context Retrieval:** Ask about your books to retrieve and analyze your saved library.
- **Image Generation:** Create images via Stability AI / Hugging Face integration.
- **Smart Pagination:** Automatically splits long responses into navigable chunks.
- **Cost Tracking:** Monitor token usage and estimated costs via `/stats`.

## Tech Stack

- **Runtime:** Python 3.9+
- **Framework:** `python-telegram-bot`
- **LLM:** GLM-4.7 (ZhipuAI)
- **Database:** Notion API
- **Image Gen:** Stability AI / Hugging Face
- **HTTP Client:** `httpx`

## Project Structure

```text
.
├── main.py              # Entry point: Bot logic and handlers
├── config.py            # Configuration: Loads environment variables
├── llm_router.py        # API Layer: GLM-4.7 logic & Web Search
├── notion_handler.py     # Integration: Upload/Retrieve Notion books
├── image_handler.py      # Integration: Image generation
└── requirements.txt     # Dependencies
```

## Getting Started

### 1. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
pip install -r requirements.txt
```

### 2. Configuration

Rename `.env.example` to `.env` and configure your environment variables.

| Variable Name | Description | Required |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Bot Token from @BotFather | Yes |
| `GLM_API_KEY` | API Key for ZhipuAI (GLM-4.7) | Yes |
| `NOTION_API_KEY` | Notion Integration Secret | Yes |
| `NOTION_DATABASE_ID` | ID of your Notion Database | Yes |
| `ZAI_API_KEY` | API Key for Image Generation | Yes |

### 3. Run Locally

```bash
python main.py
```

## Deployment

This project is configured for deployment on **Render** as a **Background Worker** (recommended for bots).

1.  Create a new **Background Worker** on Render.
2.  Connect your GitHub repository.
3.  **Build Command:** `pip install -r requirements.txt`
4.  **Start Command:** `python main.py`
5.  **Environment:** Add the variables listed above in the Render dashboard.
6.  **Deploy.**

## Commands

| Command | Description |
| :--- | :--- |
| `/start` | Initialize the bot and view the main menu. |
| `/help` | Display the help guide. |
| `/image <prompt>` | Generate an AI image. |
| `/models` | View the active AI model (GLM-4.7). |
| `/history` | View a summary of your recent chat. |
| `/clear` | Wipe your conversation memory. |
| `/cancel` | Cancel any ongoing operation (e.g., book upload). |
| `/stats` | View usage statistics and costs. |

## Usage Notes

*   **Web Search:** The bot has access to real-time data. It is configured with strict guardrails to avoid hallucinations (e.g., it will explicitly state if it cannot find a price rather than guessing).
*   **Notion:** To save a book, upload a PDF file. To retrieve the list, simply mention "books" or "notion" in your message.
*   **Pagination:** Long AI responses are handled automatically with "Read More" buttons for a cleaner chat experience.

## License

This project is for personal/educational use.
