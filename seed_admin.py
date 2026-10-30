import asyncio
from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.db_models import User, UserGroup
from app.auth import hash_password


async def seed():
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.group == UserGroup.admin))
        if result.scalars().first() is None:
            admin = User(
                username="admin",
                password_hash=hash_password("admin"),
                group=UserGroup.admin,
            )
            session.add(admin)
            await session.commit()
            print("✅ Admin created: username=admin, password=admin")
        else:
            print("ℹ️  Admin already exists")


if __name__ == "__main__":
    asyncio.run(seed())