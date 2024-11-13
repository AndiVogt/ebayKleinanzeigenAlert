import os
import sys
import schedule
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

def schedule_start(cron_schedule):
    """Schedule the start function based on the cron expression."""
    schedule.every().day.at(cron_schedule).do(get_all_post)
    while True:
        schedule.run_pending()
        sleep(1)

if __name__ == "__main__":
    mode = os.getenv("MODE", "listen")
    cron_schedule = os.getenv("CRON_SCHEDULE", "00:00")

    # Start Telegram listener in a separate thread
    if mode == "listen":
        telegram_thread = Thread(target=listen)
        telegram_thread.start()

    # Schedule periodic job using the CRON_SCHEDULE environment variable
    if mode == "start":
        schedule_thread = Thread(target=schedule_start, args=(cron_schedule,))
        schedule_thread.start()

    # Keep the main thread running
    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit(0)
