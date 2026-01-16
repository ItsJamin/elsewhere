from . import cloud_bp
from flask import (
    current_app,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory,
)
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid

@cloud_bp.route("/", methods=["GET", "POST"])
def index():
    if not session.get("admin"):
        return redirect(url_for("auth.login"))

    cloud_folder = current_app.config.get("CLOUD_FOLDER")
    os.makedirs(cloud_folder, exist_ok=True)

    if request.method == "POST":
        files = request.files.getlist("files")
        saved = []
        for f in files:
            if f and f.filename:
                filename = secure_filename(f.filename)
                unique = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}_{filename}"
                dest = os.path.join(cloud_folder, unique)
                f.save(dest)
                saved.append(unique)
        if saved:
            flash(f"Uploaded {len(saved)} file(s).", "info")
        return redirect(url_for("cloud.index"))

    # list files in cloud folder (non-recursive)
    items = []
    try:
        for name in os.listdir(cloud_folder):
            path = os.path.join(cloud_folder, name)
            if os.path.isfile(path):
                stat = os.stat(path)
                items.append({"name": name, "mtime": stat.st_mtime, "size": stat.st_size})
    except Exception:
        items = []
    items.sort(key=lambda x: x["mtime"], reverse=True)

    return render_template("cloud.html", files=items)

@cloud_bp.route("/download/<path:filename>")
def download(filename):
    if not session.get("admin"):
        return redirect(url_for("auth.login"))
    cloud_folder = current_app.config.get("CLOUD_FOLDER")
    return send_from_directory(cloud_folder, filename, as_attachment=True)

@cloud_bp.route("/delete", methods=["POST"])
def delete_file():
    if not session.get("admin"):
        return redirect(url_for("auth.login"))
    filename = request.form.get("filename")
    if not filename:
        flash("No filename provided", "error")
        return redirect(url_for("cloud.index"))
    cloud_folder = current_app.config.get("CLOUD_FOLDER")
    path = os.path.join(cloud_folder, filename)
    try:
        if os.path.exists(path) and os.path.isfile(path):
            os.remove(path)
            flash("File deleted", "info")
        else:
            flash("File not found", "error")
    except Exception:
        flash("Failed to delete file", "error")
    return redirect(url_for("cloud.index"))
