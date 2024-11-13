import os
import sys
import schedule
from datetime import datetime
from time import sleep
from threading import Thread
from ebAlert.telegram.telegramclass import telegram_bot
from ebAlert import create_logger
from ebAlert.crud.base import get_session
from ebAlert.crud.post import crud_post
from ebAlert.ebayscrapping import ebayclass

log = create_logger(__name__)

def get_all_post():
    """Fetch new posts and send Telegram notifications."""
    with get_session() as db:
        links = crud_link.get_all(db=db)
        if links:
            for link_model in links:
                print(f"Processing link - id: {link_model.id} - link: {link_model.link}")
                post_factory = ebayclass.EbayItemFactory(link_model.link)
                items = crud_post.add_items_to_db(db=db, items=post_factory.item_list)
                for item in items:
                    telegram_bot.send_formated_message(item)

def listen():
    """Continuously listen for Telegram commands."""
    print(">> Listening for Telegram commands")
    offset = None
    while True:
        updates = telegram_bot.get_updates(offset)
        for update in updates:
            offset = update['update_id'] + 1
            if 'message' in update and 'text' in update['message']:
                chat_id = update['message']['chat']['id']
                command = update['message']['text']
                telegram_bot.handle_command(chat_id, command)
        sleep(2)

def within_quiet_hours(quiet_start, quiet_end):
    """Check if the current time is within the quiet hours."""
    now = datetime.now().time()
    start = datetime.strptime(quiet_start, "%H:%M").time()
    end = datetime.strptime(quiet_end, "%H:%M").time()
    
    if start < end:
        return start <= now <= end
    else:
        # Handles overnight quiet hours (e.g., 23:00 to 07:00)
        return now >= start or now <= end

def schedule_start(interval_minutes, quiet_start, quiet_end):
    """Schedule the get_all_post function based on the interval."""
    while True:
        if not within_quiet_hours(quiet_start, quiet_end):
            get_all_post()
        sleep(interval_minutes * 60)

if __name__ == "__main__":
    # Environment variables for configuration
    interval_minutes = int(os.getenv("INTERVAL_MINUTES", 5))
    quiet_hours_start = os.getenv("QUIET_HOURS_START", "23:00")
    quiet_hours_end = os.getenv("QUIET_HOURS_END", "07:00")

    # Start the Telegram listener in a separate thread
    telegram_thread = Thread(target=listen)
    telegram_thread.start()

    # Start the scheduled task in a separate thread
    schedule_thread = Thread(target=schedule_start, args=(interval_minutes, quiet_hours_start, quiet_hours_end))
    schedule_thread.start()

    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit(0)
