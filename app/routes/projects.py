from datetime import date, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.forms import ProjectForm, ApplicationForm, ReviewForm
from app.models.ai import AIRecommendation
from app.models.project import Project, Application, ProjectStatus, ApplicationStatus
from app.models.review import Review
from app.models.verified_project import VerifiedProject
from app.models.user import StudentProfile
from app.services import ai_service, matching_service, payment_service, notification_service
from app.models.notification import NotificationType
from app.utils.decorators import role_required

projects_bp = Blueprint("projects", __name__, template_folder="../templates/business")


@projects_bp.route("/")
def browse():
    query = Project.query.filter_by(status=ProjectStatus.PUBLISHED)

    category = request.args.get("category")
    skill = request.args.get("skill")
    min_budget = request.args.get("min_budget", type=float)
    max_budget = request.args.get("max_budget", type=float)

    if category:
        query = query.filter(Project.category.ilike(f"%{category}%"))
    if skill:
        query = query.filter(Project.required_skills.ilike(f"%{skill}%"))
    if min_budget is not None:
        query = query.filter(Project.budget_amount >= min_budget)
    if max_budget is not None:
        query = query.filter(Project.budget_amount <= max_budget)

    projects = query.order_by(Project.created_at.desc()).all()

    match_scores = {}
    if current_user.is_authenticated and current_user.is_student():
        profile = current_user.student_profile
        for p in projects:
            match_scores[p.id] = matching_service.compute_match(profile, p)["score"]

    return render_template("business/browse_projects.html", projects=projects, match_scores=match_scores)


@projects_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("business")
def create():
    profile = current_user.business_profile
    form = ProjectForm()

    recommendation_id = request.args.get("from_recommendation")
    recommendation = None
    if recommendation_id and request.method == "GET":
        recommendation = AIRecommendation.query.get(recommendation_id)
        if recommendation and recommendation.diagnosis.goal.business_profile_id == profile.id:
            draft = ai_service.generate_project(recommendation)
            form.title.data = draft.title
            form.description.data = (
                draft.description
                + "\n\nRequirements:\n- "
                + "\n- ".join(draft.requirements)
                + "\n\nDeliverables:\n- "
                + "\n- ".join(draft.deliverables)
            )
            form.category.data = draft.category
            form.required_skills.data = draft.required_skills
            form.budget_amount.data = draft.suggested_budget
            form.deadline.data = date.today() + timedelta(days=draft.suggested_deadline_days)

    if form.validate_on_submit():
        project = Project(
            business_profile_id=profile.id,
            recommendation_id=recommendation_id if recommendation_id else None,
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            required_skills=form.required_skills.data,
            budget_amount=form.budget_amount.data,
            deadline=form.deadline.data,
            status=ProjectStatus.PUBLISHED,
            ai_generated=bool(recommendation_id),
        )
        db.session.add(project)

        if recommendation_id:
            rec = AIRecommendation.query.get(recommendation_id)
            if rec:
                rec.converted_to_project = True

        db.session.commit()
        flash("Project published to the marketplace.", "success")
        return redirect(url_for("projects.detail", project_id=project.id))

    return render_template(
        "business/create_project.html", form=form, recommendation=recommendation
    )


@projects_bp.route("/<project_id>")
def detail(project_id):
    project = Project.query.get_or_404(project_id)

    match = None
    my_application = None
    if current_user.is_authenticated and current_user.is_student():
        profile = current_user.student_profile
        match = matching_service.compute_match(profile, project)
        my_application = Application.query.filter_by(
            project_id=project.id, student_profile_id=profile.id
        ).first()

    application_form = ApplicationForm()
    review_form = ReviewForm()

    return render_template(
        "business/project_detail.html",
        project=project,
        match=match,
        my_application=my_application,
        application_form=application_form,
        review_form=review_form,
    )


@projects_bp.route("/<project_id>/apply", methods=["POST"])
@login_required
@role_required("student")
def apply(project_id):
    project = Project.query.get_or_404(project_id)
    profile = current_user.student_profile

    if project.status != ProjectStatus.PUBLISHED:
        flash("This project is no longer accepting applications.", "error")
        return redirect(url_for("projects.detail", project_id=project_id))

    existing = Application.query.filter_by(project_id=project_id, student_profile_id=profile.id).first()
    if existing:
        flash("You've already applied to this project.", "info")
        return redirect(url_for("projects.detail", project_id=project_id))

    form = ApplicationForm()
    if form.validate_on_submit():
        match_score = matching_service.compute_match(profile, project)["score"]
        application = Application(
            project_id=project_id,
            student_profile_id=profile.id,
            cover_message=form.cover_message.data,
            relevant_experience=form.relevant_experience.data,
            proposed_timeline_days=form.proposed_timeline_days.data,
            proposed_price=form.proposed_price.data,
            match_score=match_score,
        )
        db.session.add(application)
        db.session.commit()

        notification_service.notify(
            user_id=project.business.user_id,
            type=NotificationType.NEW_APPLICATION,
            title="New application received",
            body=f"{current_user.full_name} applied to '{project.title}'.",
            link_url=url_for("projects.detail", project_id=project_id),
        )
        flash("Application submitted.", "success")
    else:
        flash("Please fill in your cover message.", "error")

    return redirect(url_for("projects.detail", project_id=project_id))


@projects_bp.route("/<project_id>/applications")
@login_required
@role_required("business")
def applications(project_id):
    project = Project.query.get_or_404(project_id)
    if project.business_profile_id != current_user.business_profile.id:
        flash("Not authorized.", "error")
        return redirect(url_for("business.dashboard"))

    apps = sorted(project.applications, key=lambda a: (a.match_score or 0), reverse=True)
    return render_template("business/applications_list.html", project=project, applications=apps)


@projects_bp.route("/<project_id>/applications/<application_id>/<action>", methods=["POST"])
@login_required
@role_required("business")
def update_application(project_id, application_id, action):
    project = Project.query.get_or_404(project_id)
    application = Application.query.get_or_404(application_id)

    if project.business_profile_id != current_user.business_profile.id:
        flash("Not authorized.", "error")
        return redirect(url_for("business.dashboard"))

    if action == "shortlist":
        application.status = ApplicationStatus.SHORTLISTED
    elif action == "reject":
        application.status = ApplicationStatus.REJECTED
        notification_service.notify(
            user_id=application.student.user_id,
            type=NotificationType.APPLICATION_REJECTED,
            title="Application update",
            body=f"Your application for '{project.title}' was not selected this time.",
            link_url=url_for("projects.detail", project_id=project_id),
        )
    elif action == "accept":
        application.status = ApplicationStatus.ACCEPTED
        project.selected_student_profile_id = application.student_profile_id
        project.status = ProjectStatus.STUDENT_SELECTED

        for other in project.applications:
            if other.id != application.id and other.status == ApplicationStatus.PENDING:
                other.status = ApplicationStatus.REJECTED

        txn = payment_service.create_project_transaction(
            project=project,
            business_user_id=current_user.id,
            student_user_id=application.student.user_id,
        )
        payment_service.charge_business(txn)
        project.status = ProjectStatus.IN_PROGRESS

        notification_service.notify(
            user_id=application.student.user_id,
            type=NotificationType.APPLICATION_ACCEPTED,
            title="You've been selected!",
            body=f"You were selected for '{project.title}'. The project is now in progress.",
            link_url=url_for("projects.detail", project_id=project_id),
        )
    else:
        flash("Unknown action.", "error")
        return redirect(url_for("projects.applications", project_id=project_id))

    db.session.commit()
    flash("Application updated.", "success")
    return redirect(url_for("projects.applications", project_id=project_id))


@projects_bp.route("/<project_id>/submit", methods=["POST"])
@login_required
@role_required("student")
def submit_work(project_id):
    project = Project.query.get_or_404(project_id)
    profile = current_user.student_profile

    if project.selected_student_profile_id != profile.id:
        flash("Not authorized.", "error")
        return redirect(url_for("projects.detail", project_id=project_id))

    project.status = ProjectStatus.SUBMITTED
    db.session.commit()

    notification_service.notify(
        user_id=project.business.user_id,
        type=NotificationType.WORK_SUBMITTED,
        title="Work submitted for review",
        body=f"Work for '{project.title}' has been submitted.",
        link_url=url_for("projects.detail", project_id=project_id),
    )
    flash("Work submitted for business review.", "success")
    return redirect(url_for("projects.detail", project_id=project_id))


@projects_bp.route("/<project_id>/request-revision", methods=["POST"])
@login_required
@role_required("business")
def request_revision(project_id):
    project = Project.query.get_or_404(project_id)
    if project.business_profile_id != current_user.business_profile.id:
        flash("Not authorized.", "error")
        return redirect(url_for("business.dashboard"))

    project.status = ProjectStatus.REVISION_REQUESTED
    db.session.commit()

    if project.selected_student_profile_id:
        notification_service.notify(
            user_id=project.selected_student.user_id,
            type=NotificationType.REVISION_REQUESTED,
            title="Revision requested",
            body=f"The business requested a revision on '{project.title}'.",
            link_url=url_for("projects.detail", project_id=project_id),
        )

    flash("Revision requested.", "info")
    return redirect(url_for("projects.detail", project_id=project_id))


@projects_bp.route("/<project_id>/approve", methods=["POST"])
@login_required
@role_required("business")
def approve_completion(project_id):
    project = Project.query.get_or_404(project_id)
    if project.business_profile_id != current_user.business_profile.id:
        flash("Not authorized.", "error")
        return redirect(url_for("business.dashboard"))

    from app.models.payment import Transaction

    txn = Transaction.query.filter_by(project_id=project.id).first()
    if txn:
        payment_service.release_payout_to_student(txn)

    project.status = ProjectStatus.COMPLETED
    db.session.commit()

    student_profile = StudentProfile.query.get(project.selected_student_profile_id)
    if student_profile and not VerifiedProject.query.filter_by(project_id=project.id).first():
        duration_days = (project.updated_at.date() - project.created_at.date()).days or 1
        db.session.add(
            VerifiedProject(
                project_id=project.id,
                student_profile_id=student_profile.id,
                project_title=project.title,
                role=project.category or "Contributor",
                technologies=project.required_skills,
                duration_days=duration_days,
            )
        )
        db.session.commit()

        notification_service.notify(
            user_id=student_profile.user_id,
            type=NotificationType.PROJECT_COMPLETED,
            title="Project completed & paid out",
            body=f"'{project.title}' is complete. Your payout has been released.",
            link_url=url_for("projects.detail", project_id=project_id),
        )

    flash("Project marked complete. Payout released to the student.", "success")
    return redirect(url_for("projects.detail", project_id=project_id))


@projects_bp.route("/<project_id>/review", methods=["POST"])
@login_required
def submit_review(project_id):
    project = Project.query.get_or_404(project_id)
    if project.status != ProjectStatus.COMPLETED:
        flash("Reviews can only be left after project completion.", "error")
        return redirect(url_for("projects.detail", project_id=project_id))

    is_business = current_user.is_business() and project.business_profile_id == current_user.business_profile.id
    is_student = (
        current_user.is_student()
        and project.selected_student_profile_id == current_user.student_profile.id
    )
    if not (is_business or is_student):
        flash("Not authorized to review this project.", "error")
        return redirect(url_for("projects.detail", project_id=project_id))

    form = ReviewForm()
    if not form.validate_on_submit():
        flash("Please provide a rating.", "error")
        return redirect(url_for("projects.detail", project_id=project_id))

    reviewee_id = (
        project.selected_student.user_id if is_business else project.business.user_id
    )
    reviewee_role = "student" if is_business else "business"

    already = Review.query.filter_by(
        project_id=project.id, reviewer_id=current_user.id, reviewee_id=reviewee_id
    ).first()
    if already:
        flash("You've already reviewed this project.", "info")
        return redirect(url_for("projects.detail", project_id=project_id))

    db.session.add(
        Review(
            project_id=project.id,
            reviewer_id=current_user.id,
            reviewee_id=reviewee_id,
            reviewee_role=reviewee_role,
            rating=int(form.rating.data),
            comment=form.comment.data,
        )
    )
    db.session.commit()

    notification_service.notify(
        user_id=reviewee_id,
        type=NotificationType.REVIEW_RECEIVED,
        title="You received a new review",
        body=f"A new review was left for '{project.title}'.",
        link_url=url_for("projects.detail", project_id=project_id),
    )
    flash("Review submitted. Thank you!", "success")
    return redirect(url_for("projects.detail", project_id=project_id))
