from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.forms import StudentProfileForm
from app.models.skill import Skill, StudentSkill
from app.models.portfolio import PortfolioProject
from app.models.project import Project, Application, ProjectStatus
from app.models.verified_project import VerifiedProject
from app.utils.decorators import role_required
from app.utils.files import save_upload

student_bp = Blueprint("student", __name__, template_folder="../templates/student")


@student_bp.route("/dashboard")
@login_required
@role_required("student")
def dashboard():
    profile = current_user.student_profile
    applications = (
        Application.query.filter_by(student_profile_id=profile.id)
        .order_by(Application.created_at.desc())
        .limit(5)
        .all()
    )
    active_projects = Project.query.filter(
        Project.selected_student_profile_id == profile.id,
        Project.status.in_([ProjectStatus.STUDENT_SELECTED, ProjectStatus.IN_PROGRESS,
                             ProjectStatus.SUBMITTED, ProjectStatus.REVISION_REQUESTED]),
    ).all()
    verified_projects = VerifiedProject.query.filter_by(student_profile_id=profile.id).all()

    return render_template(
        "student/dashboard.html",
        profile=profile,
        applications=applications,
        active_projects=active_projects,
        verified_projects=verified_projects,
    )


@student_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("student")
def edit_profile():
    profile = current_user.student_profile
    form = StudentProfileForm(obj=profile)

    if form.validate_on_submit():
        profile.college = form.college.data
        profile.bio = form.bio.data
        profile.location = form.location.data
        profile.availability = form.availability.data
        profile.preferred_categories = form.preferred_categories.data

        if form.photo.data:
            try:
                profile.photo_path = save_upload(form.photo.data, "profile_photos")
            except ValueError as e:
                flash(str(e), "error")
                return render_template("student/edit_profile.html", form=form, profile=profile)

        # crude completeness score for the trust system
        fields_filled = sum(
            bool(v) for v in [profile.college, profile.bio, profile.location, profile.photo_path]
        )
        profile.profile_completeness = 25 + fields_filled * 18

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("student.dashboard"))

    return render_template("student/edit_profile.html", form=form, profile=profile)


@student_bp.route("/skills", methods=["GET", "POST"])
@login_required
@role_required("student")
def skills():
    profile = current_user.student_profile

    if request.method == "POST":
        skill_name = (request.form.get("skill_name") or "").strip()
        level = request.form.get("level", type=int) or 50
        if skill_name:
            skill = Skill.query.filter(Skill.name.ilike(skill_name)).first()
            if not skill:
                skill = Skill(name=skill_name, category="General")
                db.session.add(skill)
                db.session.flush()

            existing_link = StudentSkill.query.filter_by(
                student_profile_id=profile.id, skill_id=skill.id
            ).first()
            if existing_link:
                existing_link.level = level
            else:
                db.session.add(
                    StudentSkill(student_profile_id=profile.id, skill_id=skill.id, level=level)
                )
            db.session.commit()
            flash(f"Added {skill_name}.", "success")
        return redirect(url_for("student.skills"))

    all_skills = profile.skills
    return render_template("student/skills.html", profile=profile, skills=all_skills)


@student_bp.route("/skills/<skill_id>/delete", methods=["POST"])
@login_required
@role_required("student")
def delete_skill(skill_id):
    profile = current_user.student_profile
    link = StudentSkill.query.filter_by(id=skill_id, student_profile_id=profile.id).first_or_404()
    db.session.delete(link)
    db.session.commit()
    flash("Skill removed.", "info")
    return redirect(url_for("student.skills"))


@student_bp.route("/portfolio", methods=["GET", "POST"])
@login_required
@role_required("student")
def portfolio():
    profile = current_user.student_profile

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        technologies = (request.form.get("technologies") or "").strip()
        external_url = (request.form.get("external_url") or "").strip()

        if not title:
            flash("Title is required.", "error")
            return redirect(url_for("student.portfolio"))

        image_path = None
        image_file = request.files.get("image")
        if image_file and image_file.filename:
            try:
                image_path = save_upload(image_file, "portfolio")
            except ValueError as e:
                flash(str(e), "error")
                return redirect(url_for("student.portfolio"))

        db.session.add(
            PortfolioProject(
                student_profile_id=profile.id,
                title=title,
                description=description,
                technologies=technologies,
                external_url=external_url,
                image_path=image_path,
            )
        )
        db.session.commit()
        flash("Portfolio project added.", "success")
        return redirect(url_for("student.portfolio"))

    return render_template("student/portfolio.html", profile=profile, projects=profile.portfolio_projects)


@student_bp.route("/portfolio/<project_id>/delete", methods=["POST"])
@login_required
@role_required("student")
def delete_portfolio_item(project_id):
    profile = current_user.student_profile
    item = PortfolioProject.query.filter_by(id=project_id, student_profile_id=profile.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Portfolio item removed.", "info")
    return redirect(url_for("student.portfolio"))


@student_bp.route("/applications")
@login_required
@role_required("student")
def applications():
    profile = current_user.student_profile
    apps = Application.query.filter_by(student_profile_id=profile.id).order_by(
        Application.created_at.desc()
    ).all()
    return render_template("student/applications.html", applications=apps)
