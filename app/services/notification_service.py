from app.extensions import db
from app.models.notification import Notification


def notify(user_id: str, type: str, title: str, body: str = None, link_url: str = None):
    """Creates and persists a notification for a user. Commits immediately."""
    n = Notification(user_id=user_id, type=type, title=title, body=body, link_url=link_url)
    db.session.add(n)
    db.session.commit()
    return n


def unread_count(user_id: str) -> int:
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def mark_all_read(user_id: str):
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
