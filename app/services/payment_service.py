"""
Payment service abstraction.

Isolates all payment-provider logic so a real provider (Razorpay, Stripe,
etc.) can be plugged in later without touching route code. No raw card data
is ever handled or stored by this application — real integrations should use
the provider's hosted checkout / tokenization flow.

All monetary math uses Decimal — never float — per the project's financial
accuracy requirements.
"""
from decimal import Decimal, ROUND_HALF_UP

from flask import current_app

from app.extensions import db
from app.models.payment import Transaction, Payment, TransactionStatus
from app.models.platform_setting import PlatformSetting


def _quantize(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_commission(gross_amount, commission_percent=None) -> dict:
    """
    gross_amount: Decimal or numeric string/int — the amount the business funds.
    Returns a dict with commission_amount and student_payout_amount as Decimal,
    both quantized to 2 decimal places. Uses the admin-configurable platform
    commission percentage unless one is explicitly passed in.
    """
    gross = Decimal(str(gross_amount))
    percent = (
        Decimal(str(commission_percent))
        if commission_percent is not None
        else PlatformSetting.get_commission_percent()
    )

    commission_amount = _quantize(gross * percent / Decimal("100"))
    student_payout = _quantize(gross - commission_amount)

    return {
        "gross_amount": _quantize(gross),
        "commission_percent": percent,
        "commission_amount": commission_amount,
        "student_payout_amount": student_payout,
    }


def create_project_transaction(project, business_user_id, student_user_id) -> Transaction:
    """
    Creates (but does not yet mark paid) the Transaction record for a
    project being funded. Call `charge_business()` next to simulate/process
    the actual payment.
    """
    breakdown = calculate_commission(project.budget_amount)

    txn = Transaction(
        project_id=project.id,
        business_id=business_user_id,
        student_id=student_user_id,
        gross_amount=breakdown["gross_amount"],
        commission_percent=breakdown["commission_percent"],
        commission_amount=breakdown["commission_amount"],
        student_payout_amount=breakdown["student_payout_amount"],
        status=TransactionStatus.PENDING,
    )
    db.session.add(txn)
    db.session.flush()
    return txn


def charge_business(transaction: Transaction) -> Payment:
    """
    Charges the business for the project's gross amount. In mock mode this
    always succeeds instantly and funds are considered held in escrow until
    the business approves completed work.
    """
    provider = current_app.config.get("PAYMENT_PROVIDER", "mock")

    payment = Payment(
        transaction_id=transaction.id,
        direction="charge",
        amount=transaction.gross_amount,
        provider=provider,
        status="pending",
    )

    if provider == "mock":
        payment.provider_reference = f"mock_charge_{transaction.id[:8]}"
        payment.status = "succeeded"
        transaction.status = TransactionStatus.HELD_IN_ESCROW
    else:
        # Real provider integration point. Keep this branch isolated so a
        # future Razorpay/Stripe integration only needs to change this block.
        raise NotImplementedError(
            f"Live payment provider '{provider}' is not yet configured. "
            "Set PAYMENT_PROVIDER=mock for local development."
        )

    db.session.add(payment)
    db.session.commit()
    return payment


def release_payout_to_student(transaction: Transaction) -> Payment:
    """
    Releases the student's payout once the business has approved the
    completed work. Only call this after project status becomes COMPLETED.
    """
    provider = current_app.config.get("PAYMENT_PROVIDER", "mock")

    payment = Payment(
        transaction_id=transaction.id,
        direction="payout",
        amount=transaction.student_payout_amount,
        provider=provider,
        status="pending",
    )

    if provider == "mock":
        payment.provider_reference = f"mock_payout_{transaction.id[:8]}"
        payment.status = "succeeded"
        transaction.status = TransactionStatus.RELEASED
    else:
        raise NotImplementedError(
            f"Live payment provider '{provider}' is not yet configured. "
            "Set PAYMENT_PROVIDER=mock for local development."
        )

    db.session.add(payment)
    db.session.commit()
    return payment
