"""Seed script: creates demo admin/participant accounts and a hackathon.

Run with: docker compose exec backend python -m app.scripts.seed
"""
import asyncio
from datetime import datetime, timezone, timedelta
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.hackathon import Hackathon, HackathonStatus
from app.models.criterion import Criterion
from app.core.security import hash_password
from sqlalchemy import select
import structlog

logger = structlog.get_logger()

DEMO_REPOS = [
    "https://github.com/tiangolo/fastapi",
    "https://github.com/django/django",
    "https://github.com/pallets/flask",
]


async def seed():
    async with AsyncSessionLocal() as db:
        # Admin account
        admin_email = "admin@hackeval.dev"
        existing = await db.execute(select(User).where(User.email == admin_email))
        if existing.scalar_one_or_none():
            logger.info("Seed already applied — skipping")
            return

        admin = User(
            email=admin_email,
            hashed_password=hash_password("admin123"),
            full_name="Demo Admin",
            role=UserRole.admin,
        )
        db.add(admin)

        # Participant account
        participant = User(
            email="participant@hackeval.dev",
            hashed_password=hash_password("test123"),
            full_name="Demo Participant",
            role=UserRole.participant,
        )
        db.add(participant)
        await db.flush()

        # Demo hackathon
        hackathon = Hackathon(
            title="AI Hackathon 2025",
            description=(
                "Build something amazing with AI. Submit a GitHub repository "
                "and receive automated evaluation with detailed feedback."
            ),
            admin_id=admin.id,
            status=HackathonStatus.active,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=7),
            max_submissions=50,
            settings={
                "allow_private_repos": False,
                "max_repo_size_mb": 50,
                "evaluation_mode": "standard",
                "show_rankings_before_finalization": False,
            },
        )
        db.add(hackathon)
        await db.flush()

        # Criteria
        criteria = [
            Criterion(
                hackathon_id=hackathon.id,
                name="Code Quality",
                description="Engineering quality, maintainability, and best practices",
                weight=0.40,
                agent_id="code_quality",
                display_order=0,
            ),
            Criterion(
                hackathon_id=hackathon.id,
                name="Innovation",
                description="Originality, creativity, and technical sophistication",
                weight=0.35,
                agent_id="innovation",
                display_order=1,
            ),
            Criterion(
                hackathon_id=hackathon.id,
                name="Project Understanding",
                description="Clarity of purpose, documentation quality, and completeness",
                weight=0.25,
                agent_id="repo_understanding",
                display_order=2,
            ),
        ]
        for c in criteria:
            db.add(c)

        await db.commit()

        logger.info("Seed complete", admin=admin_email, hackathon=hackathon.title)
        print("\n=== Seed Complete ===")
        print(f"Admin:       {admin_email} / admin123")
        print(f"Participant: participant@hackeval.dev / test123")
        print(f"Hackathon:   {hackathon.title} (ID: {hackathon.id})")
        print("\nSuggested demo repos:")
        for r in DEMO_REPOS:
            print(f"  {r}")
        print()


if __name__ == "__main__":
    asyncio.run(seed())
