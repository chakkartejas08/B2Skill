from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.models.notification import Notification
from app.services import notification_service

notifications_bp = Blueprint("notifications", __name__, template_folder="../templates/main")


@notifications_bp.route("/")
@login_required
def index():
    notes = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).limit(50).all()
    return render_template("main/notifications.html", notifications=notes)


@notifications_bp.route("/mark-all-read", methods=["POST"])
@login_required
def mark_all_read():
    notification_service.mark_all_read(current_user.id)
    return redirect(url_for("notifications.index"))
