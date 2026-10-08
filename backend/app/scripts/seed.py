"""Seed default roles + a demo agent. Idempotent: safe to run repeatedly.

Usage: `make seed`  (or `python -m app.scripts.seed`)
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.logging import get_logger
from app.db.models import Role
from app.db.session import get_sessionmaker, init_models
from app.permissions.defaults import DEFAULT_ROLES
from app.services.agent_service import ensure_default_agent

logger = get_logger("app.seed")


async def seed() -> None:
    await init_models()
    maker = get_sessionmaker()
    async with maker() as db:
        for name, cfg in DEFAULT_ROLES.items():
            exists = (
                await db.execute(select(Role).where(Role.name == name))
            ).scalar_one_or_none()
            if not exists:
                db.add(Role(name=name, description=cfg["description"],
                            scopes=cfg["scopes"]))
        await db.commit()
        agent = await ensure_default_agent(db)
        logger.info("seed complete agent=%s roles=%s", agent.name,
                    list(DEFAULT_ROLES))
    print("Seeded roles:", ", ".join(DEFAULT_ROLES))
    print("Default agent ready.")


if __name__ == "__main__":
    asyncio.run(seed())
