from flask import Flask, request
import os
from .bot import application  # ✅ Import the bot instance

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running with Webhooks!"

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handles incoming Telegram webhook updates."""
    update = Update.de_json(request.get_json(), application.bot)

    if update:
        application.update_queue.put(update)  # ✅ Send update to bot
    
    return {"ok": True}, 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=8080)
