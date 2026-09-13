from app.extensions import db
from app.models.mixins import TimestampMixin, gen_uuid


class Conversation(db.Model, TimestampMixin):
    __tablename__ = "conversations"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=True)

    participant_one_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    participant_two_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    participant_one = db.relationship("User", foreign_keys=[participant_one_id])
    participant_two = db.relationship("User", foreign_keys=[participant_two_id])

    messages = db.relationship(
        "Message", backref="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )

    def other_participant_id(self, current_user_id):
        return (
            self.participant_two_id
            if current_user_id == self.participant_one_id
            else self.participant_one_id
        )

    def last_message(self):
        return self.messages[-1] if self.messages else None


class Message(db.Model, TimestampMixin):
    __tablename__ = "messages"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    conversation_id = db.Column(db.String(36), db.ForeignKey("conversations.id"), nullable=False)
    sender_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
