from app.extensions import db
from app.models.mixins import TimestampMixin, gen_uuid


class ReportStatus(str):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class Report(db.Model, TimestampMixin):
    __tablename__ = "reports"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    reporter_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    reported_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=True)

    reason_category = db.Column(db.String(50), nullable=False)  # behavior, fraud, fake_profile, project_issue, payment_issue
    details = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), default=ReportStatus.OPEN, nullable=False)
    admin_notes = db.Column(db.Text)
