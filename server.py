from flask import Flask, request, jsonify
from main import application  # Import the bot instance

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming Telegram updates via webhook."""
    
    if request.content_type != "application/json":
        return jsonify({"status": "error", "message": "Invalid Content-Type"}), 415  # Unsupported Media Type

    update = request.get_json()
    
    if not update:
        return jsonify({"status": "error", "message": "Empty request body"}), 400  # Bad Request

    application.update_queue.put(update)  # ✅ Pass update to bot

    return jsonify({"status": "ok"}), 200  # ✅ Always return JSON

@app.route('/')
def home():
    return jsonify({"message": "Webhook is working!"}), 200  # ✅ JSON home check

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

