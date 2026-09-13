import random
from datetime import date, timedelta

import click

from app.extensions import db


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Create all tables directly from models (quick local setup, no Alembic needed): flask init-db"""
        from app.extensions import db

        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("ensure-admin")
    def ensure_admin():
        """
        Non-interactive admin bootstrap, safe to run on every deploy: reads
        ADMIN_EMAIL / ADMIN_PASSWORD / ADMIN_NAME from the environment and
        creates that admin only if it doesn't already exist. Does nothing
        (and doesn't fail) if those variables aren't set. Use this instead
        of `create-admin` on hosts without shell access: flask ensure-admin
        """
        import os
        from app.models.user import User, UserRole

        email = os.environ.get("ADMIN_EMAIL")
        password = os.environ.get("ADMIN_PASSWORD")
        name = os.environ.get("ADMIN_NAME", "Platform Admin")

        if not email or not password:
            click.echo("ADMIN_EMAIL / ADMIN_PASSWORD not set — skipping admin bootstrap.")
            return

        existing = User.query.filter_by(email=email.lower()).first()
        if existing:
            click.echo(f"Admin '{email}' already exists — skipping.")
            return

        admin = User(email=email.lower(), full_name=name, role=UserRole.ADMIN.value, email_verified=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Admin account created for {email}.")

    @app.cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    @click.option("--name", prompt="Full name", default="Platform Admin")
    def create_admin(email, password, name):
        """Create an admin user: flask create-admin"""
        from app.models.user import User, UserRole

        if User.query.filter_by(email=email.lower()).first():
            click.echo("A user with that email already exists.")
            return

        admin = User(email=email.lower(), full_name=name, role=UserRole.ADMIN.value, email_verified=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Admin account created for {email}.")

    @app.cli.command("seed-data")
    def seed_data():
        """Populate the database with realistic fictional demo data: flask seed-data"""
        from app.models.user import User, StudentProfile, BusinessProfile, UserRole
        from app.models.skill import Skill, StudentSkill
        from app.models.project import Project, ProjectStatus

        click.echo("Seeding demo data for B2Skill AI...")

        skill_names = {
            "Development": ["Python", "Flask", "HTML/CSS", "JavaScript", "SQL"],
            "Design": ["UI/UX Design", "Graphic Design", "Figma"],
            "Media": ["Video Editing", "Photography"],
            "Marketing": ["Digital Marketing", "SEO", "Social Media Marketing"],
            "Data": ["Data Analysis", "Automation"],
        }
        skill_objs = {}
        for category, names in skill_names.items():
            for n in names:
                existing = Skill.query.filter_by(name=n).first()
                skill_objs[n] = existing or Skill(name=n, category=category)
                if not existing:
                    db.session.add(skill_objs[n])
        db.session.flush()

        students_data = [
            ("Aarav Sharma", "aarav.student@example.com", "Government Engineering College", ["Python", "Flask", "SQL"]),
            ("Priya Nair", "priya.student@example.com", "NIT Trichy", ["UI/UX Design", "Figma", "Graphic Design"]),
            ("Rohan Mehta", "rohan.student@example.com", "Delhi University", ["Graphic Design", "Photography"]),
            ("Sneha Iyer", "sneha.student@example.com", "VIT Vellore", ["Video Editing", "Photography"]),
            ("Karan Verma", "karan.student@example.com", "IIT Guwahati", ["Digital Marketing", "SEO", "Social Media Marketing"]),
        ]
        student_profiles = []
        for name, email, college, skills in students_data:
            if User.query.filter_by(email=email).first():
                continue
            u = User(email=email, full_name=name, role=UserRole.STUDENT.value, email_verified=True)
            u.set_password("password123")
            db.session.add(u)
            db.session.flush()
            sp = StudentProfile(
                user_id=u.id, college=college, bio=f"Aspiring {skills[0].lower()} specialist.",
                availability="available", location="Pune, India", profile_completeness=80,
            )
            db.session.add(sp)
            db.session.flush()
            for s in skills:
                db.session.add(StudentSkill(student_profile_id=sp.id, skill_id=skill_objs[s].id, level=random.randint(60, 95)))
            student_profiles.append(sp)

        businesses_data = [
            ("Maple & Wheat Bakery", "bakery@example.com", "Bakery", "Pune"),
            ("PowerHouse Gym", "gym@example.com", "Fitness", "Mumbai"),
            ("Spice Route Restaurant", "restaurant@example.com", "Restaurant", "Bengaluru"),
            ("Glow Salon & Spa", "salon@example.com", "Salon", "Pune"),
            ("BrightMinds Tuition Center", "tuition@example.com", "Education", "Hyderabad"),
            ("Lensview Photography", "photo@example.com", "Photography Studio", "Delhi"),
        ]
        business_profiles = []
        for name, email, btype, location in businesses_data:
            if User.query.filter_by(email=email).first():
                continue
            u = User(email=email, full_name=f"{name} Owner", role=UserRole.BUSINESS.value, email_verified=True)
            u.set_password("password123")
            db.session.add(u)
            db.session.flush()
            bp = BusinessProfile(
                user_id=u.id, business_name=name, business_type=btype, location=location,
                description=f"{name} is a growing local {btype.lower()} looking to expand digitally.",
                profile_completeness=75,
            )
            db.session.add(bp)
            db.session.flush()
            business_profiles.append(bp)

        db.session.commit()

        sample_projects = [
            ("Restaurant website with online menu", "Web Development", "HTML, CSS, JavaScript, Flask", 5000),
            ("Gym landing page with class booking", "Web Development", "HTML, CSS, JavaScript", 4000),
            ("Social media design pack (20 posts)", "Design", "Graphic Design, Figma", 2500),
            ("Digital menu design for restaurant", "Design", "Graphic Design", 1500),
            ("Online appointment enquiry form", "Web Development", "HTML, CSS, Flask", 2000),
            ("Product catalogue photography & editing", "Photography", "Photography, Video Editing", 3000),
        ]
        if business_profiles:
            for i, (title, category, skills_csv, budget) in enumerate(sample_projects):
                biz = business_profiles[i % len(business_profiles)]
                db.session.add(
                    Project(
                        business_profile_id=biz.id,
                        title=title,
                        description=f"We need help with: {title}. Looking for a reliable student to deliver quality work on time.",
                        category=category,
                        required_skills=skills_csv,
                        budget_amount=budget,
                        deadline=date.today() + timedelta(days=14),
                        status=ProjectStatus.PUBLISHED,
                    )
                )
            db.session.commit()

        click.echo("Seed data created.")
        click.echo("Demo login: any seeded email above with password 'password123'.")
