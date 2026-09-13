from app.extensions import db
from app.models.mixins import TimestampMixin, gen_uuid


class ProjectStatus(str):
    DRAFT = "draft"
    PUBLISHED = "published"
    STUDENT_SELECTED = "student_selected"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    REVISION_REQUESTED = "revision_requested"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class Project(db.Model, TimestampMixin):
    __tablename__ = "projects"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    business_profile_id = db.Column(db.String(36), db.ForeignKey("business_profiles.id"), nullable=False)
    recommendation_id = db.Column(db.String(36), db.ForeignKey("ai_recommendations.id"), nullable=True)
    selected_student_profile_id = db.Column(
        db.String(36), db.ForeignKey("student_profiles.id"), nullable=True
    )

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    required_skills = db.Column(db.String(400))  # comma separated

    budget_amount = db.Column(db.Numeric(10, 2), nullable=False)
    deadline = db.Column(db.Date)

    status = db.Column(db.String(30), default=ProjectStatus.DRAFT, nullable=False)
    ai_generated = db.Column(db.Boolean, default=False)

    selected_student = db.relationship(
        "StudentProfile", foreign_keys=[selected_student_profile_id]
    )

    requirements = db.relationship(
        "ProjectRequirement", backref="project", cascade="all, delete-orphan"
    )
    applications = db.relationship("Application", backref="project", cascade="all, delete-orphan")
    milestones = db.relationship("ProjectMilestone", backref="project", cascade="all, delete-orphan")
    files = db.relationship("ProjectFile", backref="project", cascade="all, delete-orphan")

    def application_count(self):
        return len(self.applications)


class ProjectRequirement(db.Model, TimestampMixin):
    __tablename__ = "project_requirements"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    is_deliverable = db.Column(db.Boolean, default=False)  # True = deliverable, False = requirement


class ApplicationStatus(str):
    PENDING = "pending"
    SHORTLISTED = "shortlisted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Application(db.Model, TimestampMixin):
    __tablename__ = "applications"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=False)
    student_profile_id = db.Column(db.String(36), db.ForeignKey("student_profiles.id"), nullable=False)

    cover_message = db.Column(db.Text, nullable=False)
    relevant_experience = db.Column(db.Text)
    proposed_timeline_days = db.Column(db.Integer)
    proposed_price = db.Column(db.Numeric(10, 2))

    status = db.Column(db.String(20), default=ApplicationStatus.PENDING, nullable=False)
    match_score = db.Column(db.Integer)  # 0-100, computed by matching_service at apply time

    student = db.relationship("StudentProfile")

    __table_args__ = (
        db.UniqueConstraint("project_id", "student_profile_id", name="uq_project_student_application"),
    )


class ProjectMilestone(db.Model, TimestampMixin):
    __tablename__ = "project_milestones"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date)
    is_completed = db.Column(db.Boolean, default=False)


class ProjectFile(db.Model, TimestampMixin):
    __tablename__ = "project_files"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey("projects.id"), nullable=False)
    uploaded_by_user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    file_path = db.Column(db.String(400), nullable=False)
    original_filename = db.Column(db.String(300), nullable=False)
    file_size_bytes = db.Column(db.Integer)
