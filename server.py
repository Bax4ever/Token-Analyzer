from flask import Flask, request, jsonify
import logging
from main import application  # ✅ Import the bot instance

app = Flask(__name__)

# ✅ Setup logging
logging.basicConfig(level=logging.INFO)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming Telegram updates via webhook."""
    
    # ✅ Log the request content type
    logging.info(f"Incoming request Content-Type: {request.content_type}")

    if request.content_type != "application/json":
        return jsonify({"status": "error", "message": "Invalid Content-Type"}), 415  # Unsupported Media Type

    update = request.get_json()

    # ✅ Log the received update
    logging.info(f"Received update: {update}")

    if not update:
        return jsonify({"status": "error", "message": "Empty request body"}), 400  # Bad Request

    # ✅ Process the update with the bot
    application.update_queue.put(update)

    return jsonify({"status": "ok"}), 200  # ✅ Always return JSON response

@app.route('/')
def home():
    return jsonify({"message": "Webhook is working!"}), 200  # ✅ JSON response for health check

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
