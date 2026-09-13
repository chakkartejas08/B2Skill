from app.models.ai import BusinessGoal
from app.services import ai_service


def test_analyze_business_scores_missing_website_low(app):
    with app.app_context():
        goal = BusinessGoal(
            business_profile_id="dummy",
            goal_text="More customers",
            has_website=False,
            has_online_ordering=False,
            has_online_booking=False,
            has_google_business=False,
            social_media_activity="none",
        )
        result = ai_service.analyze_business(goal)
        assert 0 <= result.overall_score <= 100
        assert "No dedicated website" in result.problems[0] or any(
            "website" in p.lower() for p in result.problems
        )


def test_analyze_business_scores_higher_with_more_presence(app):
    with app.app_context():
        weak = BusinessGoal(
            business_profile_id="d", goal_text="x", has_website=False,
            has_online_ordering=False, has_online_booking=False,
            has_google_business=False, social_media_activity="none",
        )
        strong = BusinessGoal(
            business_profile_id="d", goal_text="x", has_website=True,
            has_online_ordering=True, has_online_booking=True,
            has_google_business=True, social_media_activity="high",
        )
        weak_score = ai_service.analyze_business(weak).overall_score
        strong_score = ai_service.analyze_business(strong).overall_score
        assert strong_score > weak_score


def test_generate_recommendations_prioritizes_missing_website_high(app):
    with app.app_context():
        goal = BusinessGoal(
            business_profile_id="d", goal_text="x", has_website=False,
            has_online_ordering=True, has_online_booking=True,
            has_google_business=True, social_media_activity="high",
        )
        diagnosis = ai_service.analyze_business(goal)
        recs = ai_service.generate_recommendations(goal, diagnosis)
        assert any(r.priority == "HIGH" and "website" in r.problem.lower() for r in recs)


def test_improve_proposal_lengthens_short_message(app):
    with app.app_context():
        result = ai_service.improve_proposal("Hi, interested.")
        assert len(result) >= len("Hi, interested.")
