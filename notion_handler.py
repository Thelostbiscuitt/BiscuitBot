import logging
import httpx
from notion_client import Client
from datetime import datetime

logger = logging.getLogger(__name__)

class NotionHandler:
    def __init__(self, api_key, database_id):
        if not api_key or not database_id:
            self.client = None
            self.api_key = None
            self.database_id = None
            return
        
        self.client = Client(auth=api_key)
        self.api_key = api_key
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
                            "start": datetime.now().isoformat()
                        }
                    },
                    "Status": {
                        "status": {
                            "name": "To Read"
                        }
                    }
                }
            )
            logger.info(f"Successfully added '{title}' to Notion.")
            return True
        except Exception as e:
            logger.error(f"Failed to add book to Notion: {e}")
            return False

    async def get_books(self):
        """Retrieves all books from the Notion database using direct HTTP Request"""
        if not self.api_key or not self.database_id:
            logger.error("Notion credentials not found.")
            return []

        try:
            url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }

            # Use httpx directly to avoid the 'query' method error
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json={})
                
                logger.info(f"Notion Query Status Code: {response.status_code}")

                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Notion API Error: {response.status_code} - {error_text}")
                    return []

                data = response.json()
                books = []
                
                for result in data.get("results", []):
                    try:
                        # Extract Title safely
                        title_data = result["properties"]["Name"]["title"]
                        if title_data:
                            title = title_data[0]["text"]["content"]
                        else:
                            title = "Untitled"
                        
                        # Extract Author safely
                        author_data = result["properties"]["Author"]["rich_text"]
                        if author_data:
                            author = author_data[0]["text"]["content"]
                        else:
                            author = "Unknown Author"

                        books.append({"title": title, "author": author})
                    except Exception as e:
                        logger.warning(f"Could not parse a row: {e}")
                        continue
                
                logger.info(f"Retrieved {len(books)} books from Notion.")
                return books

        except Exception as e:
            logger.error(f"Failed to retrieve books from Notion: {e}")
            return []
