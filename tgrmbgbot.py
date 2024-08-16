import os
import logging
import requests
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from requests.exceptions import RequestException
from dotenv import load_dotenv


load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your remove.bg API Key
REMOVE_BG_API_KEY = os.getenv('rmbg_key')

# Your Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv('tg_token')

# Retry function for making requests
def make_request_with_retry(url, method='get', max_retries=5, **kwargs):
    for attempt in range(max_retries):
        try:
            if method == 'get':
                response = requests.get(url, **kwargs)
            elif method == 'post':
                response = requests.post(url, **kwargs)
            else:
                raise ValueError("Unsupported method")
            return response
        except RequestException as e:
            logger.warning(f"Request failed ({e}), retrying..... ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
    raise RequestException("Maximum retries reached")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Assalamu Alaikum! Send me a photo and I will remove its background. Jajakallah Khair for using this bot.')

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive('input_photo.png')

    await update.message.reply_text('Photo received successfully. Removing background.......')

    with open('input_photo.png', 'rb') as image_file:
        response = make_request_with_retry(
            'https://api.remove.bg/v1.0/removebg',
            method='post',
            files={'image_file': image_file},
            data={'size': 'auto'},
            headers={'X-Api-Key': REMOVE_BG_API_KEY}
        )

    if response.status_code == requests.codes.ok:
        with open('no_bg_photo.png', 'wb') as out_file:
            out_file.write(response.content)
        await update.message.reply_photo(photo=open('no_bg_photo.png', 'rb'))
    else:
            await update.message.reply_text('Error: Could not remove the photo background.')

def main() -> None:
    # Create the Application and pass it to your bot's token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register the /start command handler
    application.add_handler(CommandHandler('start', start))

    # Register a handler for photos
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()