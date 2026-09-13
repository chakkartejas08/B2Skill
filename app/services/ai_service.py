"""
AI service abstraction for B2Skill AI.

Every AI-powered feature in the platform goes through this module so the
underlying provider can be swapped without touching route/view code.

Two modes:
  - "mock"  : deterministic, rule-based responses. Used automatically when
              AI_API_KEY is not configured. Safe for local development,
              demos, and tests (no external calls, no cost).
  - "live"  : calls a real LLM provider. The HTTP call is isolated in
              `_call_llm()` below — swap that one function to change provider.

IMPORTANT — AI safety rules enforced throughout this module:
  * Recommendations are phrased as possibilities ("may help"), never guarantees.
  * The AI never auto-hires or auto-publishes; it only proposes content that a
    human (business or student) must review and confirm.
  * Matching considers only legitimate, project-relevant signals (skills,
    ratings, availability, portfolio, completion history) — never protected
    characteristics.
"""
import json
import os
from dataclasses import dataclass, field
from typing import Optional

from flask import current_app


def _provider_is_live():
    return current_app.config.get("AI_PROVIDER", "mock") == "live" and current_app.config.get(
        "AI_API_KEY"
    )


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Isolated network call to the configured AI provider.
    Only reached when AI_PROVIDER=live and AI_API_KEY is set.
    Returns raw text content from the model.
    """
    import urllib.request

    api_key = current_app.config["AI_API_KEY"]
    model = current_app.config.get("AI_MODEL", "claude-sonnet-4-6")

    payload = json.dumps(
        {
            "model": model,
            "max_tokens": 1200,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    blocks = data.get("content", [])
    return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


# ---------------------------------------------------------------------------
# Digital Health Check
# ---------------------------------------------------------------------------

CATEGORY_KEYS = [
    "website",
    "online_presence",
    "social_media",
    "customer_accessibility",
    "digital_marketing",
    "online_conversion",
]


@dataclass
class DiagnosisResult:
    overall_score: int
    category_scores: dict
    problems: list
    provider_used: str = "mock"


def analyze_business(goal) -> DiagnosisResult:
    """
    goal: a BusinessGoal model instance (not yet committed is fine).
    Returns a DiagnosisResult. Currently always uses the deterministic mock
    scorer — it's transparent, explainable, and appropriate for an MVP where
    "AI" should augment rather than obscure the underlying business logic.
    A live LLM call can be layered on top later to turn these scores into
    richer natural-language narrative without changing this scoring core.
    """
    scores = {}

    scores["website"] = 85 if goal.has_website else 20

    scores["online_presence"] = (
        (30 if goal.has_google_business else 0)
        + (30 if goal.has_website else 0)
        + (20 if goal.social_media_activity in ("medium", "high") else 5)
        + 10
    )
    scores["online_presence"] = min(scores["online_presence"], 100)

    social_map = {"none": 10, "low": 40, "medium": 65, "high": 90}
    scores["social_media"] = social_map.get((goal.social_media_activity or "none"), 10)

    scores["customer_accessibility"] = (
        (35 if goal.has_online_booking else 5)
        + (35 if goal.has_online_ordering else 5)
        + (30 if goal.has_google_business else 5)
    )
    scores["customer_accessibility"] = min(scores["customer_accessibility"], 100)

    scores["digital_marketing"] = social_map.get((goal.social_media_activity or "none"), 10) - 5
    scores["digital_marketing"] = max(scores["digital_marketing"], 5)

    scores["online_conversion"] = (
        (25 if goal.has_website else 0)
        + (25 if goal.has_online_ordering else 0)
        + (25 if goal.has_online_booking else 0)
        + (25 if goal.has_google_business else 0)
    )

    overall = round(sum(scores.values()) / len(scores))

    problems = []
    if not goal.has_website:
        problems.append("No dedicated website for the business")
    if not goal.has_google_business:
        problems.append("Google Business profile is missing or unoptimized")
    if (goal.social_media_activity or "none") in ("none", "low"):
        problems.append("Weak or inconsistent social media presence")
    if not goal.has_online_booking and not goal.has_online_ordering:
        problems.append("No online booking or ordering system for customers")
    if not problems:
        problems.append("No major gaps detected — focus on optimization and growth")

    return DiagnosisResult(overall_score=overall, category_scores=scores, problems=problems)


@dataclass
class RecommendationDraft:
    priority: str
    problem: str
    why_it_matters: str
    suggested_solution: str
    estimated_complexity: str
    suggested_budget_min: int
    suggested_budget_max: int
    required_skills: str


def generate_recommendations(goal, diagnosis: DiagnosisResult) -> list:
    """Rule-based recommendation generator, prioritized HIGH/MEDIUM/LOW."""
    recs = []

    if not goal.has_website:
        recs.append(
            RecommendationDraft(
                priority="HIGH",
                problem="No dedicated website",
                why_it_matters=(
                    "A website is often the first place potential customers look for "
                    "hours, location, and services. Without one, the business may "
                    "depend entirely on foot traffic or social media reach."
                ),
                suggested_solution=(
                    "A simple, mobile-friendly business website with an about page, "
                    "services/menu, contact details, and a way to reach the business."
                ),
                estimated_complexity="medium",
                suggested_budget_min=2000,
                suggested_budget_max=6000,
                required_skills="HTML, CSS, JavaScript, Flask",
            )
        )

    if not goal.has_google_business:
        recs.append(
            RecommendationDraft(
                priority="HIGH",
                problem="Google Business profile missing or unoptimized",
                why_it_matters=(
                    "A complete Google Business profile may improve visibility for "
                    "customers searching nearby, and can support map listings and reviews."
                ),
                suggested_solution="Set up and optimize a Google Business profile with photos, hours, and categories.",
                estimated_complexity="low",
                suggested_budget_min=500,
                suggested_budget_max=1500,
                required_skills="Digital Marketing, SEO",
            )
        )

    if (goal.social_media_activity or "none") in ("none", "low"):
        recs.append(
            RecommendationDraft(
                priority="MEDIUM",
                problem="Weak social media consistency",
                why_it_matters=(
                    "Regular, consistent posting may help keep the business top-of-mind "
                    "with existing customers and reach new ones organically."
                ),
                suggested_solution="A one-month content calendar and templated post designs for consistent posting.",
                estimated_complexity="low",
                suggested_budget_min=1000,
                suggested_budget_max=3000,
                required_skills="Graphic Design, Social Media Marketing",
            )
        )

    if not goal.has_online_booking and not goal.has_online_ordering:
        recs.append(
            RecommendationDraft(
                priority="MEDIUM",
                problem="No online booking or ordering system",
                why_it_matters=(
                    "An online enquiry, booking, or ordering form may reduce friction for "
                    "customers who prefer not to call, especially outside business hours."
                ),
                suggested_solution="A simple online enquiry/booking form embedded on the website or a linked page.",
                estimated_complexity="medium",
                suggested_budget_min=1500,
                suggested_budget_max=4000,
                required_skills="HTML, CSS, JavaScript, Flask, UI/UX",
            )
        )

    if not recs:
        recs.append(
            RecommendationDraft(
                priority="LOW",
                problem="Refresh and optimize existing digital presence",
                why_it_matters="Even a strong digital presence may benefit from periodic content and design refreshes.",
                suggested_solution="A content and photography refresh across the website and social channels.",
                estimated_complexity="low",
                suggested_budget_min=800,
                suggested_budget_max=2000,
                required_skills="Photography, Graphic Design",
            )
        )

    return recs


@dataclass
class ProjectDraft:
    title: str
    description: str
    requirements: list
    deliverables: list
    required_skills: str
    suggested_budget: int
    suggested_deadline_days: int
    category: str


def generate_project(recommendation) -> ProjectDraft:
    """
    recommendation: an AIRecommendation model instance.
    Produces an editable draft — the business must review and confirm before
    publishing (enforced in the route layer, not here).
    """
    title = f"{recommendation.problem}".strip().capitalize()
    if not title.lower().startswith(("build", "create", "design", "set up", "improve")):
        title = f"Fix: {title}"

    requirements = [
        f"Address the core problem: {recommendation.problem}",
        f"Follow the suggested approach: {recommendation.suggested_solution}",
        "Deliver work that matches the business's brand and target customers.",
    ]
    deliverables = [
        "Final working deliverable (site/content/asset as scoped)",
        "Short handover notes explaining what was built and how to maintain it",
    ]

    budget_min = float(recommendation.suggested_budget_min or 1000)
    budget_max = float(recommendation.suggested_budget_max or 3000)
    suggested_budget = round((budget_min + budget_max) / 2)

    complexity_days = {"low": 5, "medium": 10, "high": 21}
    deadline_days = complexity_days.get(recommendation.estimated_complexity or "medium", 10)

    return ProjectDraft(
        title=title,
        description=(
            f"{recommendation.why_it_matters or ''}\n\n"
            f"Suggested approach: {recommendation.suggested_solution or ''}"
        ).strip(),
        requirements=requirements,
        deliverables=deliverables,
        required_skills=recommendation.required_skills or "",
        suggested_budget=suggested_budget,
        suggested_deadline_days=deadline_days,
        category=_guess_category(recommendation.required_skills or ""),
    )


def _guess_category(skills_csv: str) -> str:
    skills = skills_csv.lower()
    if "flask" in skills or "html" in skills or "javascript" in skills:
        return "Web Development"
    if "design" in skills:
        return "Design"
    if "marketing" in skills or "seo" in skills:
        return "Digital Marketing"
    if "photography" in skills:
        return "Photography"
    return "General"


# ---------------------------------------------------------------------------
# Skill-gap analysis / proposal improvement (AI Student Assistant)
# ---------------------------------------------------------------------------

def analyze_skill_gap(project_required_skills: list, student_skills: list) -> dict:
    """
    project_required_skills: list[str]
    student_skills: list[tuple[str, int]]  (skill name, level 0-100)
    """
    student_skill_names = {name.lower() for name, _level in student_skills}
    required_lower = {s.strip().lower() for s in project_required_skills if s.strip()}

    missing = sorted(s for s in required_lower if s not in student_skill_names)
    matching = sorted(s for s in required_lower if s in student_skill_names)

    return {
        "missing_skills": missing,
        "matching_skills": matching,
        "recommended_learning_areas": missing[:3],
    }


def improve_proposal(cover_message: str) -> str:
    """
    Lightweight, deterministic proposal tightening for mock mode: trims
    filler openers and reminds the student to mention specific experience.
    In live mode this would call the LLM for a genuine rewrite.
    """
    if _provider_is_live():
        try:
            return _call_llm(
                system_prompt=(
                    "You help students on B2Skill AI tighten project proposals. "
                    "Keep the same meaning, be concise and specific, and never invent "
                    "experience the student did not mention."
                ),
                user_prompt=cover_message,
            ).strip() or cover_message
        except Exception:
            pass  # fall through to mock behavior on any provider error

    text = cover_message.strip()
    fillers = ["Hi, ", "Hello, ", "Hi there, ", "Hey, "]
    for f in fillers:
        if text.startswith(f):
            text = text[len(f):]
    if len(text) < 40:
        text += " I've reviewed the project requirements closely and believe my relevant skills and past project experience make me a strong fit — happy to share examples."
    return text
