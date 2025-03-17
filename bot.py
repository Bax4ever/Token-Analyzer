from telegram.ext import ApplicationBuilder

from bot.handlers import register_handlers
from bot.config import botbundler_token
import logging
import time

logging.basicConfig(level=logging.INFO)
logging.info("✅ Bot is starting...")


def main():
    application = ApplicationBuilder().token(botbundler_token).build()
    register_handlers(application)
    application.run_polling()


if __name__ == "__main__":
    main()
    logging.info("✅ Bot is running on Railway, keeping process alive...")
    while True:
        time.sleep(10)  # Keeps the bot process running forever
