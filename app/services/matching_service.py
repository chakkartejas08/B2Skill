"""
Matching service — computes an explainable match score (0-100) between a
student and a project.

Only legitimate, project-relevant signals are used: skills, skill level,
verified project history, ratings, availability, and category fit. This
service NEVER makes a hiring decision — it only informs the business and
student. Final selection is always a human decision made in the routes/UI.
"""
from app.models.skill import StudentSkill
from app.models.review import Review


def _parse_csv(value):
    if not value:
        return []
    return [v.strip().lower() for v in value.split(",") if v.strip()]


def compute_match(student_profile, project) -> dict:
    required_skills = _parse_csv(project.required_skills)

    student_skill_rows = StudentSkill.query.filter_by(student_profile_id=student_profile.id).all()
    student_skill_map = {row.skill.name.lower(): row.level for row in student_skill_rows if row.skill}

    # --- Skill match (up to 55 points) ---
    if required_skills:
        matched = [s for s in required_skills if s in student_skill_map]
        skill_coverage = len(matched) / len(required_skills)
        avg_level = (
            sum(student_skill_map[s] for s in matched) / len(matched) if matched else 0
        )
        skill_points = round(skill_coverage * 40 + (avg_level / 100) * 15)
    else:
        matched = []
        skill_points = 20  # neutral score if project didn't specify skills

    # --- Verified project history in same category (up to 15 points) ---
    history_count = len(
        [vp for vp in student_profile.verified_projects]
    )
    history_points = min(history_count * 5, 15)

    # --- Rating (up to 15 points) ---
    reviews = Review.query.filter_by(reviewee_id=student_profile.user_id, reviewee_role="student").all()
    if reviews:
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        rating_points = round((avg_rating / 5) * 15)
    else:
        rating_points = 8  # neutral for new students, avoids penalizing lack of history

    # --- Availability (up to 10 points) ---
    availability_points = 10 if (student_profile.availability == "available") else 3

    # --- Category familiarity (up to 5 points) ---
    preferred = _parse_csv(student_profile.preferred_categories)
    category_points = 5 if (project.category or "").lower() in preferred else 0

    total = skill_points + history_points + rating_points + availability_points + category_points
    total = max(0, min(100, total))

    missing_skills = [s for s in required_skills if s not in student_skill_map]

    if total >= 80:
        explanation = "Strong match — the student has most or all required skills and a solid track record."
    elif total >= 55:
        explanation = "Reasonable match — the student covers several required skills but has some gaps."
    else:
        explanation = "Limited match — the student is missing several required skills for this project."

    return {
        "score": total,
        "matched_skills": matched,
        "missing_skills": missing_skills,
        "explanation": explanation,
    }
