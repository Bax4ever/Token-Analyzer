from telegram.ext import ApplicationBuilder
from bot.handlers import register_handlers
from bot.config import botbundler_token
import logging
import os


WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Set this in Railway/Render

logging.basicConfig(level=logging.INFO)
logging.info("✅ Bot is starting with Webhooks...")

def main():
    """Start the bot using webhooks instead of polling."""
    application = ApplicationBuilder().token(botbundler_token).build()

    register_handlers(application)

    # Use webhooks instead of polling
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),  # Default to 8080
        webhook_url=f"{WEBHOOK_URL}"
    )

if __name__ == "__main__":
    main()
