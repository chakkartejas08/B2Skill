import json

from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_required, current_user

from app.extensions import db
from app.forms import BusinessProfileForm, BusinessGoalForm
from app.models.ai import BusinessGoal, AIDiagnosis, AIRecommendation
from app.models.project import Project, ProjectStatus
from app.models.user import StudentProfile
from app.services import ai_service
from app.utils.decorators import role_required

business_bp = Blueprint("business", __name__, template_folder="../templates/business")


@business_bp.route("/dashboard")
@login_required
@role_required("business")
def dashboard():
    profile = current_user.business_profile
    latest_goal = (
        BusinessGoal.query.filter_by(business_profile_id=profile.id)
        .order_by(BusinessGoal.created_at.desc())
        .first()
    )
    latest_diagnosis = None
    if latest_goal:
        latest_diagnosis = (
            AIDiagnosis.query.filter_by(business_goal_id=latest_goal.id)
            .order_by(AIDiagnosis.created_at.desc())
            .first()
        )

    projects = Project.query.filter_by(business_profile_id=profile.id).order_by(
        Project.created_at.desc()
    ).limit(5).all()

    return render_template(
        "business/dashboard.html",
        profile=profile,
        diagnosis=latest_diagnosis,
        projects=projects,
    )


@business_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("business")
def edit_profile():
    profile = current_user.business_profile
    form = BusinessProfileForm(obj=profile)

    if form.validate_on_submit():
        profile.business_name = form.business_name.data
        profile.business_type = form.business_type.data
        profile.location = form.location.data
        profile.description = form.description.data
        profile.website_url = form.website_url.data
        profile.social_url = form.social_url.data

        fields_filled = sum(
            bool(v) for v in [profile.business_type, profile.location, profile.description]
        )
        profile.profile_completeness = 25 + fields_filled * 25

        db.session.commit()
        flash("Business profile updated.", "success")
        return redirect(url_for("business.dashboard"))

    return render_template("business/edit_profile.html", form=form, profile=profile)


@business_bp.route("/health-check", methods=["GET", "POST"])
@login_required
@role_required("business")
def health_check():
    profile = current_user.business_profile
    form = BusinessGoalForm()

    if form.validate_on_submit():
        goal = BusinessGoal(
            business_profile_id=profile.id,
            goal_text=form.goal_text.data,
            has_website=form.has_website.data,
            has_online_ordering=form.has_online_ordering.data,
            has_online_booking=form.has_online_booking.data,
            has_google_business=form.has_google_business.data,
            social_media_activity=form.social_media_activity.data,
            target_customers=form.target_customers.data,
        )
        db.session.add(goal)
        db.session.flush()

        result = ai_service.analyze_business(goal)

        diagnosis = AIDiagnosis(
            business_goal_id=goal.id,
            overall_score=result.overall_score,
            score_website=result.category_scores["website"],
            score_online_presence=result.category_scores["online_presence"],
            score_social_media=result.category_scores["social_media"],
            score_customer_accessibility=result.category_scores["customer_accessibility"],
            score_digital_marketing=result.category_scores["digital_marketing"],
            score_online_conversion=result.category_scores["online_conversion"],
            problems_detected=json.dumps(result.problems),
            ai_provider_used=result.provider_used,
        )
        db.session.add(diagnosis)
        db.session.flush()

        recs = ai_service.generate_recommendations(goal, result)
        for r in recs:
            db.session.add(
                AIRecommendation(
                    diagnosis_id=diagnosis.id,
                    priority=r.priority,
                    problem=r.problem,
                    why_it_matters=r.why_it_matters,
                    suggested_solution=r.suggested_solution,
                    estimated_complexity=r.estimated_complexity,
                    suggested_budget_min=r.suggested_budget_min,
                    suggested_budget_max=r.suggested_budget_max,
                    required_skills=r.required_skills,
                )
            )
        db.session.commit()

        return redirect(url_for("business.diagnosis_result", diagnosis_id=diagnosis.id))

    return render_template("business/health_check.html", form=form)


@business_bp.route("/health-check/<diagnosis_id>")
@login_required
@role_required("business")
def diagnosis_result(diagnosis_id):
    profile = current_user.business_profile
    diagnosis = AIDiagnosis.query.get_or_404(diagnosis_id)
    if diagnosis.goal.business_profile_id != profile.id:
        flash("Not found.", "error")
        return redirect(url_for("business.dashboard"))

    problems = json.loads(diagnosis.problems_detected or "[]")
    recommendations = sorted(
        diagnosis.recommendations,
        key=lambda r: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(r.priority, 3),
    )

    return render_template(
        "business/diagnosis_result.html",
        diagnosis=diagnosis,
        problems=problems,
        recommendations=recommendations,
    )


@business_bp.route("/find-students")
@login_required
@role_required("business")
def find_students():
    students = StudentProfile.query.limit(30).all()
    return render_template("business/find_students.html", students=students)
