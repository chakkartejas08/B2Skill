from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    SelectField,
    BooleanField,
    DecimalField,
    DateField,
    IntegerField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange


class RegisterForm(FlaskForm):
    role = SelectField(
        "I am a", choices=[("student", "Student"), ("business", "Business")], validators=[DataRequired()]
    )
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=150)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )
    # Business-only optional field, shown/required conditionally in the template/JS
    business_name = StringField("Business name", validators=[Optional(), Length(max=200)])
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Log in")


class BusinessGoalForm(FlaskForm):
    goal_text = TextAreaField(
        "What's your main business goal right now?",
        validators=[DataRequired(), Length(max=1000)],
        render_kw={"placeholder": "e.g. I want more customers finding us online"},
    )
    has_website = BooleanField("We have a dedicated website")
    has_online_ordering = BooleanField("We offer online ordering")
    has_online_booking = BooleanField("We offer online booking/appointments")
    has_google_business = BooleanField("We have an active Google Business profile")
    social_media_activity = SelectField(
        "How active are you on social media?",
        choices=[("none", "Not active"), ("low", "Occasionally"), ("medium", "Regularly"), ("high", "Very active")],
    )
    target_customers = StringField("Who are your target customers?", validators=[Optional(), Length(max=300)])
    submit = SubmitField("Run My Digital Health Check")


class ProjectForm(FlaskForm):
    title = StringField("Project title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[DataRequired()])
    category = StringField("Category", validators=[Optional(), Length(max=100)])
    required_skills = StringField(
        "Required skills (comma separated)", validators=[DataRequired(), Length(max=400)]
    )
    budget_amount = DecimalField("Budget (INR)", validators=[DataRequired(), NumberRange(min=100)])
    deadline = DateField("Deadline", validators=[Optional()])
    submit = SubmitField("Publish Project")


class ApplicationForm(FlaskForm):
    cover_message = TextAreaField("Cover message", validators=[DataRequired(), Length(max=2000)])
    relevant_experience = TextAreaField("Relevant experience", validators=[Optional(), Length(max=2000)])
    proposed_timeline_days = IntegerField("Proposed timeline (days)", validators=[Optional(), NumberRange(min=1)])
    proposed_price = DecimalField("Proposed price (optional)", validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField("Submit Application")


class MessageForm(FlaskForm):
    body = TextAreaField("Message", validators=[DataRequired(), Length(max=3000)])
    submit = SubmitField("Send")


class ReviewForm(FlaskForm):
    rating = SelectField("Rating", choices=[(str(i), f"{i} star{'s' if i != 1 else ''}") for i in range(5, 0, -1)])
    comment = TextAreaField("Comment (optional)", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Submit Review")


class StudentProfileForm(FlaskForm):
    college = StringField("College", validators=[Optional(), Length(max=200)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=1000)])
    location = StringField("Location", validators=[Optional(), Length(max=150)])
    availability = SelectField(
        "Availability", choices=[("available", "Available"), ("busy", "Busy"), ("unavailable", "Unavailable")]
    )
    preferred_categories = StringField("Preferred categories (comma separated)", validators=[Optional()])
    photo = FileField("Profile photo", validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "webp"])])
    submit = SubmitField("Save Profile")


class BusinessProfileForm(FlaskForm):
    business_name = StringField("Business name", validators=[DataRequired(), Length(max=200)])
    business_type = StringField("Business type", validators=[Optional(), Length(max=120)])
    location = StringField("Location", validators=[Optional(), Length(max=150)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=1000)])
    website_url = StringField("Website URL", validators=[Optional(), Length(max=300)])
    social_url = StringField("Social media URL", validators=[Optional(), Length(max=300)])
    submit = SubmitField("Save Profile")


class PlatformSettingForm(FlaskForm):
    commission_percent = DecimalField(
        "Platform commission (%)", validators=[DataRequired(), NumberRange(min=0, max=50)]
    )
    submit = SubmitField("Update Setting")
