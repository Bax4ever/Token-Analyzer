from flask import Flask, request, jsonify
import logging
import asyncio
from main import application  # ✅ Import the bot instance

app = Flask(__name__)

# ✅ Setup logging
logging.basicConfig(level=logging.INFO)

@app.route('/webhook', methods=['POST'])
async def webhook():
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

    # ✅ Properly enqueue the update in the Telegram bot application
    try:
        await application.update_queue.put(update)  # ✅ Ensure it's awaited
    except Exception as e:
        logging.error(f"Error adding update to queue: {e}")
        return jsonify({"status": "error", "message": "Failed to enqueue update"}), 500

    return jsonify({"status": "ok"}), 200  # ✅ Always return JSON response

@app.route('/')
def home():
    return jsonify({"message": "Webhook is working!"}), 200  # ✅ JSON response for health check

def run_flask():
    """Runs Flask server in an async-friendly manner"""
    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:8443"]  # ✅ Set port correctly
    asyncio.run(serve(app, config))

if __name__ == "__main__":
    logging.info("✅ Starting Flask webhook server...")
    run_flask()
