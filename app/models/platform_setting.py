from decimal import Decimal

from app.extensions import db
from app.models.mixins import TimestampMixin, gen_uuid

COMMISSION_KEY = "platform_commission_percent"


class PlatformSetting(db.Model, TimestampMixin):
    __tablename__ = "platform_settings"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(300), nullable=False)
    description = db.Column(db.String(300))

    @staticmethod
    def get_commission_percent():
        """Returns the current platform commission as a Decimal, e.g. Decimal('9')."""
        setting = PlatformSetting.query.filter_by(key=COMMISSION_KEY).first()
        if setting is None:
            from flask import current_app

            return Decimal(str(current_app.config["PLATFORM_COMMISSION_PERCENT_DEFAULT"]))
        return Decimal(setting.value)

    @staticmethod
    def set_commission_percent(new_percent):
        setting = PlatformSetting.query.filter_by(key=COMMISSION_KEY).first()
        if setting is None:
            setting = PlatformSetting(
                key=COMMISSION_KEY,
                value=str(new_percent),
                description="Platform commission percentage taken from each funded project.",
            )
            db.session.add(setting)
        else:
            setting.value = str(new_percent)
        db.session.commit()
        return setting
