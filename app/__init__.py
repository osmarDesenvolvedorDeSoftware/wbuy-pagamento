from flask import Flask
from dotenv import load_dotenv

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)

    from .server import register_routes

    register_routes(app)
    return app


app = create_app()
