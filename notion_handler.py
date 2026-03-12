import logging
from notion_client import Client

logger = logging.getLogger(__name__)

class NotionHandler:
    def __init__(self, api_key, database_id):
        if not api_key or not database_id:
            self.client = None
            return
        
        self.client = Client(auth=api_key)
        self.database_id = database_id

    def add_book(self, title, author):
        """Adds a book entry to the Notion database"""
        if not self.client:
            logger.error("Notion client not initialized.")
            return False

        try:
            self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    },
                    "Author": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": author
                                }
                            }
                        ]
                    },
                    "Date Added": {
                        "date": {
                            "start": "2023-01-01" # Placeholder or use datetime.now()
                        }
                    },
                    "Status": {
                        "select": {
                            "name": "To Read" # Make sure this option exists in Notion
                        }
                    }
                }
            )
            logger.info(f"Successfully added '{title}' to Notion.")
            return True
        except Exception as e:
            logger.error(f"Failed to add book to Notion: {e}")
            return False
