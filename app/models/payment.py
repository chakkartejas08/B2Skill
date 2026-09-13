from app.extensions import db
from app.models.mixins import TimestampMixin, gen_uuid


class TransactionStatus(str):
    PENDING = "pending"
    HELD_IN_ESCROW = "held_in_escrow"
    RELEASED = "released"
    REFUNDED = "refunded"
    FAILED = "failed"


class Transaction(db.Model, TimestampMixin):
    """
    Records the full commission breakdown for a funded project.
    Monetary values always use Numeric/Decimal — never Float.
    """

    __tablename__ = "transactions"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=False)
    business_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    student_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    gross_amount = db.Column(db.Numeric(10, 2), nullable=False)
    commission_percent = db.Column(db.Numeric(5, 2), nullable=False)
    commission_amount = db.Column(db.Numeric(10, 2), nullable=False)
    student_payout_amount = db.Column(db.Numeric(10, 2), nullable=False)

    status = db.Column(db.String(20), default=TransactionStatus.PENDING, nullable=False)

    payments = db.relationship("Payment", backref="transaction", cascade="all, delete-orphan")


class Payment(db.Model, TimestampMixin):
    """
    A single payment-provider event tied to a Transaction (e.g. the business's
    charge, or the eventual payout to the student). Kept separate from
    Transaction so multiple provider events can be tracked over time.
    """

    __tablename__ = "payments"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    transaction_id = db.Column(db.String(36), db.ForeignKey("transactions.id"), nullable=False)

    direction = db.Column(db.String(20), nullable=False)  # "charge" (business->platform) or "payout" (platform->student)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    provider = db.Column(db.String(30), nullable=False)  # "mock", "razorpay", "stripe", ...
    provider_reference = db.Column(db.String(200))  # external payment/payout ID
    status = db.Column(db.String(20), default="pending", nullable=False)
