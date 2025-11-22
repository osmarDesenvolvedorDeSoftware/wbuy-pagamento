import sys
from flask import Flask, request, jsonify

from utils.save_payload import save_raw_payload

app = Flask(__name__)


@app.route("/wbuy")
def health():
    return "wbuy api online", 200


@app.route("/wbuy/ping")
def ping():
    return jsonify({"status": "ok"}), 200


@app.route("/wbuy/webhook", methods=["POST"])
def webhook():
    raw_payload = request.data or b""
    save_raw_payload(raw_payload)
    sys.stdout.buffer.write(raw_payload + b"\n")
    sys.stdout.flush()
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
