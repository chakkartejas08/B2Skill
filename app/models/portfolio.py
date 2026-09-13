from app.extensions import db
from app.models.mixins import TimestampMixin, gen_uuid


class PortfolioProject(db.Model, TimestampMixin):
    __tablename__ = "portfolio_projects"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_profile_id = db.Column(db.String(36), db.ForeignKey("student_profiles.id"), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    technologies = db.Column(db.String(300))  # comma separated
    image_path = db.Column(db.String(400))
    external_url = db.Column(db.String(300))
