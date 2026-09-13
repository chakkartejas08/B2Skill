# B2Skill AI

An AI-powered platform that helps small local businesses identify their digital
problems and connects them with students who can solve those problems through
affordable, real-world digital projects.

Businesses don't need to know what digital service they need. They describe a
goal, an AI Digital Health Check turns that into a prioritized, explainable
plan, and each recommendation can become a real project — reviewed and
published by the business, matched against students by an explainable score,
and paid out through a transparent 9% platform commission.

## Problem it solves

- **Businesses** often know they need to "go digital" but not what that means —
  a website? online booking? social media? B2Skill AI runs an AI Digital
  Health Check and turns the gaps into a prioritized action plan.
- **Students** learn real skills (Python, Flask, design, marketing, video,
  photography, data) but struggle to find real projects to build experience
  with. B2Skill AI connects them to funded, real business projects and
  gives them **verified project history** — not just certificates.

## Core workflow

```
Business goal → AI analysis → Digital Health Score → Prioritized plan
→ AI-generated project brief (business reviews & edits) → Publish
→ Student applications with AI match score → Business selects
→ Project funded → In progress → Submitted → Approved → Paid out
→ Verified project experience + mutual reviews
```

## Features

- Role-based accounts: **Student**, **Business**, **Admin**
- AI Digital Health Check with a 0–100 score across 6 categories, prioritized
  recommendations (HIGH/MEDIUM/LOW), and one-click "Create Project" from any
  recommendation (business always reviews/edits before publishing)
- Explainable student–project matching (skills, ratings, history,
  availability — never a black box, never an automatic hiring decision)
- Full project workflow: draft → published → student selected → in progress
  → submitted → revision requested → completed (or cancelled/disputed)
- Escrow-style payments: business funds the project, platform holds it,
  releases the student payout on business approval
- **9% platform commission**, admin-configurable at runtime (not hardcoded)
- Internal messaging, notifications, reviews & ratings, verified project
  history, reports/disputes, and a full admin dashboard
- AI service is a swappable abstraction (`app/services/ai_service.py`) —
  runs in deterministic **mock mode** out of the box; a live LLM provider can
  be plugged in later without touching route code
- Payments are similarly abstracted (`app/services/payment_service.py`) —
  mock provider for local dev, isolated integration point for
  Razorpay/Stripe later. No raw card data is ever handled or stored.
- All monetary math uses `Decimal`, never `float`

## Architecture

```
biz2skill/
├── app/
│   ├── __init__.py          # application factory
│   ├── extensions.py        # db, migrate, login_manager, csrf
│   ├── forms.py             # all WTForms forms
│   ├── cli.py                # flask init-db / create-admin / seed-data
│   ├── models/               # one file per model group
│   ├── routes/                # one blueprint per area
│   │   ├── auth.py, main.py, student.py, business.py,
│   │   └── projects.py, messages.py, notifications.py, admin.py
│   ├── services/
│   │   ├── ai_service.py            # analyze_business, generate_recommendations,
│   │   │                            # generate_project, analyze_skill_gap, improve_proposal
│   │   ├── matching_service.py      # compute_match (explainable 0-100 score)
│   │   ├── payment_service.py       # commission calc, mock charge/payout
│   │   └── notification_service.py
│   ├── templates/             # one folder per area, base.html + partials
│   ├── static/css/app.css     # small hand-written layer on top of Tailwind CDN
│   └── utils/                 # role_required decorator, file upload validation
├── migrations/                 # Alembic migrations (flask db init/migrate/upgrade)
├── tests/
├── config.py
├── run.py
├── requirements.txt
├── .env.example
└── .gitignore
```

## Technology stack

- **Backend:** Flask 3, Flask-SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF
- **Database:** SQLite for local development, PostgreSQL-ready for production
- **Frontend:** Server-rendered Jinja templates, Tailwind CSS (CDN), vanilla JS
- **Auth:** Flask-Login sessions, hashed passwords (Werkzeug), CSRF protection

## Installation

```bash
git clone <your-repo-url> biz2skill
cd biz2skill

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# edit .env if needed — the defaults work for local development out of the box
```

## Environment variables

See `.env.example`. Key ones:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session signing — set a real random value in production |
| `DATABASE_URL` | SQLite by default; set a `postgresql://...` URL in production |
| `PLATFORM_COMMISSION_PERCENT` | Default commission (%) — the authoritative, admin-editable value lives in the `PlatformSetting` table once the app has run once |
| `AI_PROVIDER` / `AI_API_KEY` / `AI_MODEL` | Leave `AI_PROVIDER=mock` for local dev — no key needed. Set to `live` + a key to call a real model |
| `PAYMENT_PROVIDER` | Leave as `mock` for local dev — simulates instant charges/payouts, no real money moves |
| `UPLOAD_FOLDER` / `MAX_CONTENT_LENGTH_MB` | Where portfolio/project files are stored, and the upload size cap |

## Database setup

Quickest path for local development (no Alembic setup required):

```bash
flask init-db
```

Or, for a proper migration history (recommended before production):

```bash
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

## Seed data & admin account

```bash
flask seed-data
# creates fictional students, businesses, and published projects.
# every seeded account's password is: password123

flask create-admin
# interactive prompt for an admin email/password
```

## Running locally

```bash
python run.py
# or
flask run
```

Visit **http://127.0.0.1:5000**

## AI setup

`AI_PROVIDER=mock` (the default) uses a fully deterministic, transparent
scoring and recommendation engine in `app/services/ai_service.py` — no API
key, no cost, no external calls. It's intentionally rule-based rather than a
black box, which keeps Digital Health Scores explainable.

To use a live LLM instead, set `AI_PROVIDER=live`, `AI_API_KEY`, and
`AI_MODEL` in `.env`. The network call is isolated in `_call_llm()` in
`ai_service.py` — that's the only function you'd need to change to swap
providers.

## Payment setup

`PAYMENT_PROVIDER=mock` (the default) simulates an instant, successful charge
and payout — nothing real happens, safe for local development and demos. To
integrate a real provider (Razorpay, Stripe, etc.), implement that branch in
`app/services/payment_service.py` (`charge_business()` /
`release_payout_to_student()`); every other part of the app already calls
through this abstraction, so nothing else needs to change.

## Testing

```bash
pytest
```

Test coverage should include (see `tests/`): registration, login,
authorization/role checks, profile creation, project creation, applications,
project status transitions, **commission math** (₹1,000 × 9% = ₹90 → student
payout ₹910; ₹5,000 × 9% = ₹450 → student payout ₹4,550), reviews, the AI
service, and the matching service.

## Deployment notes

- Set `FLASK_ENV=production`, a strong `SECRET_KEY`, and a PostgreSQL
  `DATABASE_URL`.
- Run behind `gunicorn` (included in `requirements.txt`):
  `gunicorn -w 4 -b 0.0.0.0:8000 run:app`
- Set `PAYMENT_PROVIDER` to a real provider once `payment_service.py` has a
  live integration implemented, and switch `AI_PROVIDER=live` if desired.
- Serve uploaded files from outside the web root / through a CDN in
  production rather than directly from `instance/uploads`.

## Future improvements

- Real-time messaging (WebSockets) instead of polling/refresh
- Milestone-based partial payouts instead of single lump-sum release
- Richer AI narrative generation layered on top of the deterministic scorer
- Student skill verification/testing
- Government ID verification tier for higher-trust businesses (optional,
  not required for MVP per the platform's trust-system design)

## Important product & safety principles baked into the code

- AI recommendations are phrased as possibilities ("may help"), never
  guarantees — see `ai_service.py`.
- The AI never auto-hires or auto-publishes anything; every AI-generated
  project draft must be reviewed and confirmed by a human before it goes live.
- Matching uses only legitimate, project-relevant signals (skills, ratings,
  availability, portfolio, completion history) — see `matching_service.py`.
- No subscriptions, no paid plans, no pay-to-boost — the platform only earns
  through the commission on successfully funded projects.
