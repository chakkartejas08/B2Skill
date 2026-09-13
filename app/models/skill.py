from app.extensions import db
from app.models.mixins import TimestampMixin, gen_uuid


class Skill(db.Model, TimestampMixin):
    __tablename__ = "skills"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(80))  # e.g. Development, Design, Marketing

    def __repr__(self):
        return f"<Skill {self.name}>"


class StudentSkill(db.Model, TimestampMixin):
    __tablename__ = "student_skills"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    student_profile_id = db.Column(db.String(36), db.ForeignKey("student_profiles.id"), nullable=False)
    skill_id = db.Column(db.String(36), db.ForeignKey("skills.id"), nullable=False)

    level = db.Column(db.Integer, default=50)  # 0-100 self-rated proficiency

    skill = db.relationship("Skill")

    __table_args__ = (
        db.UniqueConstraint("student_profile_id", "skill_id", name="uq_student_skill"),
    )
