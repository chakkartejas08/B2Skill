from app.extensions import db
from app.models.mixins import TimestampMixin, gen_uuid


class BusinessGoal(db.Model, TimestampMixin):
    __tablename__ = "business_goals"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    business_profile_id = db.Column(db.String(36), db.ForeignKey("business_profiles.id"), nullable=False)

    goal_text = db.Column(db.Text, nullable=False)

    has_website = db.Column(db.Boolean, default=False)
    has_online_ordering = db.Column(db.Boolean, default=False)
    has_online_booking = db.Column(db.Boolean, default=False)
    has_google_business = db.Column(db.Boolean, default=False)
    social_media_activity = db.Column(db.String(30))  # none, low, medium, high
    target_customers = db.Column(db.String(300))

    diagnoses = db.relationship("AIDiagnosis", backref="goal", cascade="all, delete-orphan")


class AIDiagnosis(db.Model, TimestampMixin):
    __tablename__ = "ai_diagnoses"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    business_goal_id = db.Column(db.String(36), db.ForeignKey("business_goals.id"), nullable=False)

    overall_score = db.Column(db.Integer, nullable=False)  # 0-100 Digital Health Score

    score_website = db.Column(db.Integer, default=0)
    score_online_presence = db.Column(db.Integer, default=0)
    score_social_media = db.Column(db.Integer, default=0)
    score_customer_accessibility = db.Column(db.Integer, default=0)
    score_digital_marketing = db.Column(db.Integer, default=0)
    score_online_conversion = db.Column(db.Integer, default=0)

    problems_detected = db.Column(db.Text)  # JSON-encoded list of strings
    ai_provider_used = db.Column(db.String(30))  # mock / live provider name

    recommendations = db.relationship(
        "AIRecommendation", backref="diagnosis", cascade="all, delete-orphan"
    )


class AIRecommendation(db.Model, TimestampMixin):
    __tablename__ = "ai_recommendations"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    diagnosis_id = db.Column(db.String(36), db.ForeignKey("ai_diagnoses.id"), nullable=False)

    priority = db.Column(db.String(10), nullable=False)  # HIGH, MEDIUM, LOW
    problem = db.Column(db.String(300), nullable=False)
    why_it_matters = db.Column(db.Text)
    suggested_solution = db.Column(db.Text)
    estimated_complexity = db.Column(db.String(20))  # low, medium, high
    suggested_budget_min = db.Column(db.Numeric(10, 2))
    suggested_budget_max = db.Column(db.Numeric(10, 2))
    required_skills = db.Column(db.String(400))  # comma separated

    converted_to_project = db.Column(db.Boolean, default=False)
