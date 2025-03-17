from telegram.ext import ApplicationBuilder
from bot.handlers import register_handlers
from bot.config import botbundler_token
import logging
import time

logging.basicConfig(level=logging.INFO)
logging.info("✅ Bot is starting...")

# ✅ Create the application instance
application = ApplicationBuilder().token(botbundler_token).build()
register_handlers(application)

def main():
    application.run_webhook(
        listen="0.0.0.0",
        port=8000,
        url_path=botbundler_token,
        webhook_url=f"https://token-analyzer-production.up.railway.app/{botbundler_token}"
    )

if __name__ == "__main__":
    main()
    logging.info("✅ Bot is running on Railway, keeping process alive...")
    while True:
        time.sleep(10)  # Keeps the bot process running forever
