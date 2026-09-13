from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.forms import PlatformSettingForm
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus
from app.models.payment import Transaction, TransactionStatus
from app.models.report import Report, ReportStatus
from app.models.platform_setting import PlatformSetting
from app.utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    total_students = User.query.filter_by(role=UserRole.STUDENT.value).count()
    total_businesses = User.query.filter_by(role=UserRole.BUSINESS.value).count()
    active_projects = Project.query.filter(
        Project.status.in_(
            [ProjectStatus.PUBLISHED, ProjectStatus.STUDENT_SELECTED, ProjectStatus.IN_PROGRESS,
             ProjectStatus.SUBMITTED, ProjectStatus.REVISION_REQUESTED]
        )
    ).count()
    completed_projects = Project.query.filter_by(status=ProjectStatus.COMPLETED).count()

    transactions = Transaction.query.filter_by(status=TransactionStatus.RELEASED).all()
    platform_revenue = sum((t.commission_amount for t in transactions), start=0)

    pending_reports = Report.query.filter_by(status=ReportStatus.OPEN).count()

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        total_businesses=total_businesses,
        active_projects=active_projects,
        completed_projects=completed_projects,
        platform_revenue=platform_revenue,
        total_transactions=Transaction.query.count(),
        pending_reports=pending_reports,
    )


@admin_bp.route("/users")
@login_required
@role_required("admin")
def users():
    role_filter = request.args.get("role")
    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    all_users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users, role_filter=role_filter)


@admin_bp.route("/users/<user_id>/toggle-suspend", methods=["POST"])
@login_required
@role_required("admin")
def toggle_suspend(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't suspend your own account.", "error")
        return redirect(url_for("admin.users"))

    user.is_suspended = not user.is_suspended
    db.session.commit()
    flash(f"{user.full_name} is now {'suspended' if user.is_suspended else 'active'}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/projects")
@login_required
@role_required("admin")
def projects():
    all_projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("admin/projects.html", projects=all_projects)


@admin_bp.route("/transactions")
@login_required
@role_required("admin")
def transactions():
    txns = Transaction.query.order_by(Transaction.created_at.desc()).all()
    return render_template("admin/transactions.html", transactions=txns)


@admin_bp.route("/reports")
@login_required
@role_required("admin")
def reports():
    all_reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template("admin/reports.html", reports=all_reports)


@admin_bp.route("/reports/<report_id>/<new_status>", methods=["POST"])
@login_required
@role_required("admin")
def update_report(report_id, new_status):
    report = Report.query.get_or_404(report_id)
    valid = {ReportStatus.OPEN, ReportStatus.UNDER_REVIEW, ReportStatus.RESOLVED, ReportStatus.REJECTED}
    if new_status not in valid:
        flash("Invalid status.", "error")
        return redirect(url_for("admin.reports"))
    report.status = new_status
    db.session.commit()
    flash("Report status updated.", "success")
    return redirect(url_for("admin.reports"))


@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
@role_required("admin")
def settings():
    form = PlatformSettingForm()
    if form.validate_on_submit():
        PlatformSetting.set_commission_percent(form.commission_percent.data)
        flash("Platform commission updated.", "success")
        return redirect(url_for("admin.settings"))

    form.commission_percent.data = PlatformSetting.get_commission_percent()
    return render_template("admin/settings.html", form=form)
