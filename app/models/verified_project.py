from app.extensions import db
from app.models.mixins import TimestampMixin, gen_uuid


class VerifiedProject(db.Model, TimestampMixin):
    __tablename__ = "verified_projects"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=False, unique=True)
    student_profile_id = db.Column(db.String(36), db.ForeignKey("student_profiles.id"), nullable=False)

    project_title = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(120))
    technologies = db.Column(db.String(300))
    duration_days = db.Column(db.Integer)
    client_rating = db.Column(db.Numeric(2, 1))  # snapshot of the review rating at completion
