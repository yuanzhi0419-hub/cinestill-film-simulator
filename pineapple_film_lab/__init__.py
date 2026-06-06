from flask import Flask

from .config import DefaultConfig


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(DefaultConfig)
    if overrides:
        app.config.update(overrides)
    return app

