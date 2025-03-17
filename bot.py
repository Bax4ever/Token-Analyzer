from telegram.ext import ApplicationBuilder

from bot.handlers import register_handlers
from bot.config import botbundler_token
import logging

logging.basicConfig(level=logging.INFO)
logging.info("✅ Bot is starting...")


def main():
    application = ApplicationBuilder().token(botbundler_token).build()
    register_handlers(application)
    application.run_polling()

if __name__ == "__main__":
    main()
