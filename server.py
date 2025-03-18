import logging
import asyncio
from flask import Flask, request, jsonify
import os
from main import application  # ✅ Ensure correct import

app = Flask(__name__)

@app.route("/")
def home():
    return "Webhook is working!"

@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        data = request.get_json()
        logging.info(f"Received Webhook Data: {data}")

        if not data:
            return jsonify({"status": "error", "message": "Empty request body"}), 400

        await application.update_queue.put(data)  # ✅ Ensure async processing

        return jsonify({"status": "success", "message": "Update processed"})
    except Exception as e:
        logging.error(f"Webhook Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    import hypercorn.asyncio
    from hypercorn.config import Config

    config = Config()
    config.bind = [f"0.0.0.0:{os.getenv('PORT', '8443')}"]  # ✅ Auto-detect Railway port

    asyncio.run(hypercorn.asyncio.serve(app, config))
