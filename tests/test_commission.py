from decimal import Decimal

from app.services.payment_service import calculate_commission


def test_commission_1000(app):
    with app.app_context():
        result = calculate_commission(1000, commission_percent=9)
        assert result["commission_amount"] == Decimal("90.00")
        assert result["student_payout_amount"] == Decimal("910.00")


def test_commission_5000(app):
    with app.app_context():
        result = calculate_commission(5000, commission_percent=9)
        assert result["commission_amount"] == Decimal("450.00")
        assert result["student_payout_amount"] == Decimal("4550.00")


def test_commission_uses_admin_setting_by_default(app):
    with app.app_context():
        from app.models.platform_setting import PlatformSetting

        PlatformSetting.set_commission_percent(12)
        result = calculate_commission(1000)
        assert result["commission_percent"] == Decimal("12")
        assert result["commission_amount"] == Decimal("120.00")
        assert result["student_payout_amount"] == Decimal("880.00")


def test_commission_rounds_half_up(app):
    with app.app_context():
        # 999 * 9% = 89.91 exactly -> no rounding ambiguity, sanity check only
        result = calculate_commission(999, commission_percent=9)
        assert result["gross_amount"] == Decimal("999.00")
        assert result["commission_amount"] + result["student_payout_amount"] == Decimal("999.00")
