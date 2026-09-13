from app.extensions import db
from app.models.mixins import TimestampMixin, gen_uuid


class Review(db.Model, TimestampMixin):
    __tablename__ = "reviews"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=False)

    reviewer_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    reviewee_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    reviewee_role = db.Column(db.String(20), nullable=False)  # "student" or "business"

    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint(
            "project_id", "reviewer_id", "reviewee_id", name="uq_review_per_project_pair"
        ),
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"),
    )
