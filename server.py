from main import application  # ✅ Correct import from main.py
from flask import Flask, request
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/webhook', methods=['POST', 'GET'])  # ✅ Allow GET for testing
def webhook():
    if request.method == 'GET':
        return "Webhook is working!", 200  # ✅ Test this in your browser

    update = request.get_json()
    logging.info(f"📩 Received Update: {update}")
    application.update_queue.put_nowait(update)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
