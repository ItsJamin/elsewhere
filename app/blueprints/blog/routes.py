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
import markdown
import bleach

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
    cur = conn.cursor()

    # Create table if missing (includes latitude/longitude columns)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            timestamp DATETIME,
            media TEXT,
            latitude REAL,
            longitude REAL,
            deleted INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()

    # Ensure columns exist (for upgrades from earlier schema)
    cur.execute("PRAGMA table_info(posts)")
    cols = [r[1] for r in cur.fetchall()]  # name is at index 1
    if "latitude" not in cols:
        try:
            cur.execute("ALTER TABLE posts ADD COLUMN latitude REAL")
            conn.commit()
        except Exception:
            pass
    if "longitude" not in cols:
        try:
            cur.execute("ALTER TABLE posts ADD COLUMN longitude REAL")
            conn.commit()
        except Exception:
            pass
    if "deleted" not in cols:
        try:
            cur.execute("ALTER TABLE posts ADD COLUMN deleted INTEGER DEFAULT 0")
            conn.commit()
        except Exception:
            pass

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
            "SELECT id, title, content, timestamp, media, latitude, longitude FROM posts WHERE deleted IS NULL OR deleted = 0 ORDER BY timestamp DESC"
        )
        rows = cur.fetchall()
        for r in rows:
            # convert stored markdown/plain-text to sanitized HTML for display
            raw_content = r["content"] or ""
            try:
                html = markdown.markdown(raw_content, extensions=["extra", "sane_lists"])
                allowed_tags = [
                    "a", "abbr", "acronym", "b", "blockquote", "code", "em", "i", "li",
                    "ol", "strong", "ul", "p", "br", "pre", "h1", "h2", "h3", "h4", "h5",
                    "h6", "img", "table", "thead", "tbody", "tr", "th", "td"
                ]
                allowed_attrs = {
                    "*": ["class"],
                    "a": ["href", "title", "rel", "target"],
                    "img": ["src", "alt", "title"],
                    "th": ["colspan", "rowspan"],
                    "td": ["colspan", "rowspan"],
                }
                clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)
                clean_html = bleach.linkify(clean_html)
            except Exception:
                # fallback: escape-newlines to <br/> if markdown conversion fails
                clean_html = (r["content"] or "").replace("\n", "<br/>")
            posts.append(
                {
                    "id": r["id"],
                    "title": r["title"],
                    "content": clean_html,
                    "timestamp": r["timestamp"],
                    "media": r["media"],
                    "latitude": r["latitude"],
                    "longitude": r["longitude"],
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
        lat_raw = request.form.get("latitude", "").strip()
        lon_raw = request.form.get("longitude", "").strip()

        def parse_coord(v):
            try:
                if v == "" or v is None:
                    return None
                return float(v)
            except Exception:
                return None

        latitude = parse_coord(lat_raw)
        longitude = parse_coord(lon_raw)

        files = request.files.getlist("media")

        saved_files = []
        upload_folder = current_app.config.get("UPLOAD_FOLDER")
        os.makedirs(upload_folder, exist_ok=True)

        for f in files:
            if f and f.filename:
                filename = secure_filename(f.filename)
                # Always save uploaded files; unsupported types will be offered as downloads.
                # Keep client-side rendering limited to known image/video/audio types.
                unique = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}_{filename}"
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
            ts = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            conn.execute(
                "INSERT INTO posts (title, content, timestamp, media, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)",
                (title, content, ts, media_field, latitude, longitude),
            )
            conn.commit()
            conn.close()
            flash("Post created", "info")
            return redirect(url_for("blog.list_posts"))
        except Exception:
            flash("Failed to create post", "error")
            try:
                conn.close()
            except Exception:
                pass

        # On error fallthrough to render form again

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

        # soft-delete: mark as deleted (retain files on disk)
        conn.execute("UPDATE posts SET deleted = 1 WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()

        flash("Post deleted", "info")
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        flash("Failed to delete post", "error")

    return redirect(url_for("blog.list_posts"))
