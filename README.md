

Here is a clean, professional `README.md` file. It explains the project structure and setup instructions without revealing any of your actual tokens, keys, or sensitive code logic.

You can create a file named `README.md` in your GitHub repository root and paste this content:

```markdown
# Biscuit AI Assistant

A production-ready Telegram bot powered by Groq's Llama 3.3 70B Versatile model. This bot features conversation memory, cost tracking, and Markdown-formatted responses.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram)

## Features

- **Intelligent Conversations:** Powered by Llama 3.3 70B via Groq for fast, low-latency responses.
- **Conversation Memory:** Remembers context within a session (up to 20 messages).
- **Usage Tracking:** Monitor token usage and estimated costs via `/stats`.
- **Rich Formatting:** Supports Markdown for code blocks, lists, and bold text.
- **Access Control:** Optional restriction to specific user IDs.

## Project Structure

The project is organized into modular components for easy maintenance and deployment.

```text
.
├── main.py              # Entry point: Telegram bot handlers and polling logic.
├── config.py            # Configuration: Loads environment variables and settings.
├── llm_router.py        # API Layer: Handles communication with the Groq API.
├── requirements.txt     # Dependencies: List of required Python packages.
└── README.md            # This file.
```

## Setup & Deployment

### Prerequisites

- Python 3.9+
- A Telegram Bot Token (obtain via [@BotFather](https://t.me/BotFather))
- A Groq API Key (obtain via [Groq Console](https://console.groq.com/))

### Environment Variables

The bot relies on the following environment variables. Ensure these are configured in your deployment platform (e.g., Render, Railway) or a local `.env` file.

| Variable Name | Description | Required |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | The API token for your Telegram bot. | Yes |
| `GROQ_API_KEY` | The API key for accessing Groq services. | Yes |
| `AUTHORIZED_USERS` | Comma-separated list of Telegram User IDs allowed to use the bot (Leave empty for public access). | No |

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   Create a `.env` file locally (or set variables in your hosting dashboard):
   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   GROQ_API_KEY=your_groq_key_here
   ```

4. **Run the Bot**
   ```bash
   python main.py
   ```

## Deployment on Render

This project is configured for **Render** as a Background Worker.

1.  Create a new **Background Worker** on Render.
2.  Connect your GitHub repository.
3.  **Build Command:** `pip install -r requirements.txt`
4.  **Start Command:** `python main.py`
5.  Add the environment variables listed above in the Render Dashboard.

## Commands

- `/start` - Initialize the bot and view the welcome menu.
- `/help` - View help information and capabilities.
- `/clear` - Clear your current conversation history.
- `/stats` - View your usage statistics (token count and cost).

## License

This project is for personal/educational use.
```
