from flask import Blueprint, redirect, url_for

main_bp = Blueprint("main", __name__, template_folder="templates/main/")

@main_bp.route("/")
def home():
    # Redirect root to the blog listing
    return redirect(url_for("blog.list_posts"))
