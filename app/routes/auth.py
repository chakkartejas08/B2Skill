from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.forms import RegisterForm, LoginForm
from app.models.user import User, StudentProfile, BusinessProfile, UserRole

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if existing:
            flash("An account with that email already exists. Try logging in instead.", "error")
            return render_template("auth/register.html", form=form)

        if form.role.data == "business" and not (form.business_name.data or "").strip():
            flash("Business name is required for a business account.", "error")
            return render_template("auth/register.html", form=form)

        user = User(
            email=form.email.data.lower().strip(),
            full_name=form.full_name.data.strip(),
            phone=(form.phone.data or "").strip(),
            role=form.role.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # get user.id before creating profile

        if form.role.data == "student":
            db.session.add(StudentProfile(user_id=user.id))
        else:
            db.session.add(
                BusinessProfile(user_id=user.id, business_name=form.business_name.data.strip())
            )

        db.session.commit()

        login_user(user)
        flash(f"Welcome to B2Skill AI, {user.full_name.split()[0]}!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Incorrect email or password.", "error")
            return render_template("auth/login.html", form=form)

        if user.is_suspended or not user.is_active_account:
            flash("This account has been suspended. Contact support for help.", "error")
            return render_template("auth/login.html", form=form)

        login_user(user, remember=form.remember_me.data)
        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()

        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.dashboard"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("main.landing"))
