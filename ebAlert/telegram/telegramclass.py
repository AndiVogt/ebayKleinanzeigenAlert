import requests
from urllib.parse import urlencode
from ebAlert.core.config import settings
from ebAlert.ebayscrapping.ebayclass import EbayItem
from ebAlert.crud.base import crud_link, get_session
from ebAlert.crud.post import crud_post

class SendingClass:
    def send_message(self, chat_id, message):
        message_encoded = urlencode({"text": message})
        sending_url = f"{settings.TELEGRAM_API_URL}sendMessage?chat_id={chat_id}&{message_encoded}"
        response = requests.get(sending_url)
        if response.status_code == 200:
            return response.json().get("ok")
        else:
            print(f"Failed to send message: {response.text}")
            return False

    def send_formated_message(self, item: EbayItem):
        message = f"{item.title}\n\n{item.price} ({item.city})\n\n"
        url = f'<a href="{item.link}">{item.link}</a>'
        self.send_message(settings.CHAT_ID, message + url)

    def get_updates(self, offset=None):
        url = f"{settings.TELEGRAM_API_URL}getUpdates?timeout=100"
        if offset:
            url += f"&offset={offset}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("result", [])
        print(f"Failed to get updates: {response.text}")
        return []

telegram_bot = SendingClass()
