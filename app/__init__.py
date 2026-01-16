from flask import Flask, render_template
import os
from .blueprints.main import main_bp

def create_app(config_name="development"):
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration (see app/config.py)
    app.config.from_object('app.config.Config')
    # Ensure Flask uses the configured secret for session signing
    app.secret_key = app.config['SECRET_KEY']

    # Allow an optional config file pointed to by APP_CONFIG_FILE
    app.config.from_envvar('APP_CONFIG_FILE', silent=True)

    # Ensure instance, upload and cloud folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    # create CLOUD_FOLDER if configured
    try:
        os.makedirs(app.config.get('CLOUD_FOLDER'), exist_ok=True)
    except Exception:
        pass

    # Register blueprints
    app.register_blueprint(main_bp)

    # Optional blueprints (added later)
    try:
        from .blueprints.auth import auth_bp
        app.register_blueprint(auth_bp)
    except Exception:
        pass

    try:
        from .blueprints.blog import blog_bp
        app.register_blueprint(blog_bp)
    except Exception:
        pass

    try:
        from .blueprints.cloud import cloud_bp
        app.register_blueprint(cloud_bp)
    except Exception:
        pass

    # Register simple error handlers for common status codes
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    return app
