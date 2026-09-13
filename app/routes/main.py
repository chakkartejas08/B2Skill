from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main_bp = Blueprint("main", __name__, template_folder="../templates/main")


@main_bp.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("main/landing.html")


@main_bp.route("/how-it-works")
def how_it_works():
    return render_template("main/how_it_works.html")


@main_bp.route("/about")
def about():
    return render_template("main/about.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_student():
        return redirect(url_for("student.dashboard"))
    if current_user.is_business():
        return redirect(url_for("business.dashboard"))
    if current_user.is_admin():
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("main.landing"))
