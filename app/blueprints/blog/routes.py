from . import blog_bp
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
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid

ALLOWED_EXTENSIONS = set(
    [
        "png",
        "jpg",
        "jpeg",
        "gif",
        "mp4",
        "webm",
        "ogg",
        "mov",
        "wav",
        "mp3",
        "m4a",
        "aac",
        "oga",
    ]
)


def get_db_path():
    return current_app.config.get("DATABASE")


def ensure_db():
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            timestamp DATETIME,
            media TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def get_db_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@blog_bp.route("/")
def list_posts():
    posts = []
    try:
        ensure_db()
        conn = get_db_connection()
        cur = conn.execute(
            "SELECT id, title, content, timestamp, media FROM posts ORDER BY timestamp DESC"
        )
        rows = cur.fetchall()
        for r in rows:
            posts.append(
                {
                    "id": r["id"],
                    "title": r["title"],
                    "content": r["content"],
                    "timestamp": r["timestamp"],
                    "media": r["media"],
                }
            )
    except Exception:
        posts = []
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return render_template("list.html", posts=posts)


@blog_bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Serve uploaded files from the configured UPLOAD_FOLDER."""
    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    return send_from_directory(upload_folder, filename)


@blog_bp.route("/new", methods=["GET", "POST"])
def new_post():
    """Admin-only minimal create form with basic file upload handling."""
    if not session.get("admin"):
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        title = request.form.get("title", "").strip() or None
        content = request.form.get("content", "").strip() or ""
        files = request.files.getlist("media")

        saved_files = []
        upload_folder = current_app.config.get("UPLOAD_FOLDER")
        os.makedirs(upload_folder, exist_ok=True)

        for f in files:
            if f and f.filename:
                filename = secure_filename(f.filename)
                if not allowed_file(filename):
                    # skip unknown extensions
                    continue
                # make filename unique
                unique = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}_{filename}"
                dest_path = os.path.join(upload_folder, unique)
                f.save(dest_path)
                saved_files.append(unique)

        media_field = None
        if saved_files:
            # store filenames joined by '||' (simple delimiter)
            media_field = "||".join(saved_files)

        # insert post into DB
        try:
            ensure_db()
            conn = get_db_connection()
            ts = datetime.now().strftime('%d.%m.%Y %H:%M')
            conn.execute(
                "INSERT INTO posts (title, content, timestamp, media) VALUES (?, ?, ?, ?)",
                (title, content, ts, media_field),
            )
            conn.commit()
            conn.close()
            flash("Post created", "info")
            return redirect(url_for("blog.list_posts"))
        except Exception as e:
            flash("Failed to create post", "error")
            try:
                conn.close()
            except Exception:
                pass
    
    return render_template("create.html")

@blog_bp.route("/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    """Delete a post and any associated uploaded files. Admin only."""
    if not session.get("admin"):
        return redirect(url_for("auth.login"))

    try:
        ensure_db()
        conn = get_db_connection()
        cur = conn.execute("SELECT media FROM posts WHERE id = ?", (post_id,))
        row = cur.fetchone()
        media_field = row["media"] if row else None

        # delete DB row
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()

        # remove files from upload folder
        if media_field:
            upload_folder = current_app.config.get("UPLOAD_FOLDER")
            for fname in media_field.split("||"):
                try:
                    path = os.path.join(upload_folder, fname)
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass

        flash("Post deleted", "info")
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        flash("Failed to delete post", "error")

    return redirect(url_for("blog.list_posts"))
