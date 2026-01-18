import os

class Config:
    # Secrets
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change")

    APPLICATION_ROOT = os.environ.get("APPLICATION_ROOT", "/")

    # Uploads
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.normpath(os.path.join(_BASE_DIR, "..", "instance", "uploads"))
    CLOUD_FOLDER = os.path.normpath(os.path.join(_BASE_DIR, "..", "instance", "cloud"))
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 50 * 1024 * 1024))  # default 50 MB

    # Database (simple SQLite file in instance/)
    DATABASE = os.path.normpath(os.path.join(_BASE_DIR, "..", "instance", "blog.db"))

    # Session
    SESSION_TYPE = "filesystem"
