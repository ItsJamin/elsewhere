from flask import Blueprint, render_template, request, redirect, url_for, current_app, session, flash

auth_bp = Blueprint("auth", __name__, template_folder="templates/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Simple single-admin login using ADMIN_PASSWORD from config/env
    if request.method == "POST":
        password = request.form.get("password", "")
        admin_pw = current_app.config.get("ADMIN_PASSWORD")
        if admin_pw and password == admin_pw:
            session["admin"] = True
            return redirect(url_for("blog.list_posts"))
        else:
            flash("Invalid credentials", "error")
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("main.home"))
