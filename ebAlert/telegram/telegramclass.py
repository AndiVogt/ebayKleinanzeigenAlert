import requests
from urllib.parse import urlencode
from ebAlert.core.config import settings
from ebAlert.ebayscrapping.ebayclass import EbayItem
from ebAlert.crud.base import crud_link, get_session
from ebAlert.crud.post import crud_post


class SendingClass:

    def send_message(self, chat_id, message):
        """Send a message to a specific Telegram chat."""
        message_encoded = urlencode({"text": message})
        sending_url = f"{settings.TELEGRAM_API_URL}sendMessage?chat_id={chat_id}&{message_encoded}"
        response = requests.get(sending_url)
        if response.status_code == 200:
            return response.json().get("ok")
        else:
            print(f"Failed to send message: {response.text}")
            return False

    def send_formated_message(self, item: EbayItem):
        """Send a formatted message about a new eBay post."""
        message = f"{item.title}\n\n{item.price} ({item.city})\n\n"
        url = f'<a href="{item.link}">{item.link}</a>'
        self.send_message(settings.CHAT_ID, message + url)

    def get_updates(self, offset=None):
        """Fetch updates (messages) from Telegram."""
        url = f"{settings.TELEGRAM_API_URL}getUpdates?timeout=100"
        if offset:
            url += f"&offset={offset}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("result", [])
        print(f"Failed to get updates: {response.text}")
        return []

    def handle_command(self, chat_id, command):
        """Handle different commands sent via Telegram."""
        with get_session() as db:
            if command.startswith("/add "):
                url = command.split("/add ", 1)[1].strip()
                if crud_link.get_by_key(key_mapping={"link": url}, db=db):
                    self.send_message(chat_id, "Link already exists.")
                else:
                    crud_link.create({"link": url}, db)
                    ebay_items = ebayclass.EbayItemFactory(url)
                    crud_post.add_items_to_db(db, ebay_items.item_list)
                    self.send_message(chat_id, "Link added successfully.")
            elif command.startswith("/remove "):
                link_id = command.split("/remove ", 1)[1].strip()
                if crud_link.remove(db=db, id=link_id):
                    self.send_message(chat_id, "Link removed successfully.")
                else:
                    self.send_message(chat_id, "Link not found.")
            elif command == "/show":
                links = crud_link.get_all(db)
                if links:
                    message = "List of URLs:\n"
                    for link_model in links:
                        message += f"{link_model.id}: {link_model.link}\n"
                    self.send_message(chat_id, message)
                else:
                    self.send_message(chat_id, "No links found.")
            elif command == "/start":
                self.send_message(chat_id, "Welcome! Use /add, /remove, or /show.")
            else:
                self.send_message(chat_id, "Unknown command. Use /add, /remove, /show.")

telegram = SendingClass()
