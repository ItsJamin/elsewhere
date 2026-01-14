from flask import Flask
from .blueprints.main import main_bp

def create_app(config_name="development"):
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(main_bp)

    return app
