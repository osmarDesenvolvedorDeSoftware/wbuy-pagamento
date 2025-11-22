from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/wbuy")
def health():
    return "wbuy api online", 200

@app.route("/wbuy/webhook/order", methods=["POST"])
def webhook_order():
    data = request.json
    print("Webhook recebido:", data)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
