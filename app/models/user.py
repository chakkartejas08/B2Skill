from enum import Enum

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models.mixins import TimestampMixin, gen_uuid


class UserRole(str, Enum):
    STUDENT = "student"
    BUSINESS = "business"
    ADMIN = "admin"


class User(db.Model, UserMixin, TimestampMixin):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.STUDENT.value)

    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30))

    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    is_suspended = db.Column(db.Boolean, default=False, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)

    last_login_at = db.Column(db.DateTime)

    student_profile = db.relationship(
        "StudentProfile", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    business_profile = db.relationship(
        "BusinessProfile", backref="user", uselist=False, cascade="all, delete-orphan"
    )

    # Flask-Login required overrides -----------------------------------
    def get_id(self):
        return self.id

    @property
    def is_active(self):
        return self.is_active_account and not self.is_suspended

    # Convenience --------------------------------------------------------
    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def is_student(self):
        return self.role == UserRole.STUDENT.value

    def is_business(self):
        return self.role == UserRole.BUSINESS.value

    def is_admin(self):
        return self.role == UserRole.ADMIN.value

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class StudentProfile(db.Model, TimestampMixin):
    __tablename__ = "student_profiles"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True)

    college = db.Column(db.String(200))
    bio = db.Column(db.Text)
    photo_path = db.Column(db.String(400))

    availability = db.Column(db.String(30), default="available")  # available, busy, unavailable
    preferred_categories = db.Column(db.String(400))  # comma separated for MVP simplicity
    location = db.Column(db.String(150))

    profile_completeness = db.Column(db.Integer, default=10)

    skills = db.relationship("StudentSkill", backref="student", cascade="all, delete-orphan")
    portfolio_projects = db.relationship(
        "PortfolioProject", backref="student", cascade="all, delete-orphan"
    )
    verified_projects = db.relationship(
        "VerifiedProject", backref="student", cascade="all, delete-orphan"
    )

    def average_rating(self):
        from app.models.review import Review

        reviews = Review.query.filter_by(
            reviewee_id=self.user_id, reviewee_role="student"
        ).all()
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)


class BusinessProfile(db.Model, TimestampMixin):
    __tablename__ = "business_profiles"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True)

    business_name = db.Column(db.String(200), nullable=False)
    business_type = db.Column(db.String(120))
    location = db.Column(db.String(150))
    description = db.Column(db.Text)
    website_url = db.Column(db.String(300))
    social_url = db.Column(db.String(300))

    profile_completeness = db.Column(db.Integer, default=10)

    goals = db.relationship("BusinessGoal", backref="business", cascade="all, delete-orphan")
    projects = db.relationship("Project", backref="business", cascade="all, delete-orphan")

    def average_rating(self):
        from app.models.review import Review

        reviews = Review.query.filter_by(
            reviewee_id=self.user_id, reviewee_role="business"
        ).all()
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)
