"""
Run this once to create the initial admin user.
  python scripts/create_admin.py --email admin@example.com --password secret123
"""
import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from core.database import AsyncSessionLocal, engine, Base
from core.security import hash_password
from models.user import User
import uuid


async def create_admin(email: str, password: str, name: str):
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"User {email} already exists.")
            return

        user = User(
            id=str(uuid.uuid4()),
            email=email,
            full_name=name,
            hashed_password=hash_password(password),
            role="admin",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        print(f"✓ Admin user created: {email}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create admin user")
    parser.add_argument("--email",    required=True,  help="Admin email")
    parser.add_argument("--password", required=True,  help="Admin password")
    parser.add_argument("--name",     default="Admin", help="Full name")
    args = parser.parse_args()

    asyncio.run(create_admin(args.email, args.password, args.name))
