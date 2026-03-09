"""Initialize the database — create all tables.

Run this once after setting up PostgreSQL.
Usage: python scripts/migration/init_db.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from apps.api.database import engine, Base
from apps.api.models import GameSession, StateSnapshot, EventRecord, BattleLog


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init())
