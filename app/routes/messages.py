from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_, and_

from app.extensions import db
from app.forms import MessageForm
from app.models.messaging import Conversation, Message
from app.models.user import User
from app.services import notification_service
from app.models.notification import NotificationType

messages_bp = Blueprint("messages", __name__, template_folder="../templates/main")


@messages_bp.route("/")
@login_required
def inbox():
    conversations = Conversation.query.filter(
        or_(
            Conversation.participant_one_id == current_user.id,
            Conversation.participant_two_id == current_user.id,
        )
    ).order_by(Conversation.updated_at.desc()).all()
    return render_template("main/inbox.html", conversations=conversations)


@messages_bp.route("/start/<other_user_id>", methods=["GET", "POST"])
@login_required
def start_or_view(other_user_id):
    if other_user_id == current_user.id:
        flash("You can't message yourself.", "error")
        return redirect(url_for("messages.inbox"))

    other_user = User.query.get_or_404(other_user_id)

    conversation = Conversation.query.filter(
        or_(
            and_(
                Conversation.participant_one_id == current_user.id,
                Conversation.participant_two_id == other_user_id,
            ),
            and_(
                Conversation.participant_one_id == other_user_id,
                Conversation.participant_two_id == current_user.id,
            ),
        )
    ).first()

    if not conversation:
        project_id = request.args.get("project_id")
        conversation = Conversation(
            participant_one_id=current_user.id,
            participant_two_id=other_user_id,
            project_id=project_id,
        )
        db.session.add(conversation)
        db.session.commit()

    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(conversation_id=conversation.id, sender_id=current_user.id, body=form.body.data)
        db.session.add(msg)
        db.session.commit()

        notification_service.notify(
            user_id=other_user_id,
            type=NotificationType.NEW_MESSAGE,
            title=f"New message from {current_user.full_name}",
            body=form.body.data[:120],
            link_url=url_for("messages.start_or_view", other_user_id=current_user.id),
        )
        return redirect(url_for("messages.start_or_view", other_user_id=other_user_id))

    # mark incoming messages read
    Message.query.filter_by(conversation_id=conversation.id, is_read=False).filter(
        Message.sender_id != current_user.id
    ).update({"is_read": True})
    db.session.commit()

    return render_template(
        "main/conversation.html", conversation=conversation, other_user=other_user, form=form
    )
