from flask import jsonify, request

from .wbuy.webhook import handle_webhook


def register_routes(app):
    @app.route("/wbuy", methods=["GET"])
    def healthcheck():
        return "wbuy api online", 200

    @app.route("/wbuy/webhook", methods=["POST"])
    def webhook_receiver():
        response = handle_webhook(request)
        return jsonify(response), 200
