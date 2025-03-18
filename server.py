from flask import Flask, request, jsonify
from bot.bot import application  # Import the bot instance

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming Telegram updates via webhook."""
    update = request.get_json()

    if update:
        application.update_queue.put(update)  # ✅ Pass update to bot

    return jsonify({"status": "ok"}), 200  # ✅ Always return JSON

@app.route('/')
def home():
    return jsonify({"message": "Webhook is working!"}), 200  # ✅ JSON home check

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
