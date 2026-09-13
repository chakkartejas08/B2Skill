from app.extensions import db
from app.models.mixins import TimestampMixin, gen_uuid


class NotificationType(str):
    NEW_APPLICATION = "new_application"
    APPLICATION_ACCEPTED = "application_accepted"
    APPLICATION_REJECTED = "application_rejected"
    NEW_MESSAGE = "new_message"
    PROJECT_ACCEPTED = "project_accepted"
    DEADLINE_APPROACHING = "deadline_approaching"
    WORK_SUBMITTED = "work_submitted"
    REVISION_REQUESTED = "revision_requested"
    PROJECT_COMPLETED = "project_completed"
    REVIEW_RECEIVED = "review_received"
    PAYMENT_UPDATE = "payment_update"


class Notification(db.Model, TimestampMixin):
    __tablename__ = "notifications"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)

    type = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.String(400))
    link_url = db.Column(db.String(300))

    is_read = db.Column(db.Boolean, default=False, nullable=False)
