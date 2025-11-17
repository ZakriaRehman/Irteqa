from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData
from typing import AsyncGenerator
import os

# Determine environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Database URL based on environment
if ENVIRONMENT == "production":
    # Production: Use PostgreSQL
    DATABASE_URL = os.getenv(
        "DATABASE_URL"
        "postgresql+asyncpg://postgres:postgres@localhost:5432/irteqa_health"
    )
    ENGINE_ARGS = {
        "echo": False,  # Disable SQL logging in production
        "future": True,
        "pool_pre_ping": True,  # Verify connections before using
        "pool_size": 10,
        "max_overflow": 20
    }
else:
    # Development: Use SQLite
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./irteqa_health.db"
    )
    ENGINE_ARGS = {
        "echo": True,  # Enable SQL logging in development
        "future": True,
        "connect_args": {"check_same_thread": False}  # SQLite specific
    }

print(f"[*] Environment: {ENVIRONMENT}")
print(f"[DB] Database: {DATABASE_URL.split('@')[0] if '@' in DATABASE_URL else DATABASE_URL}")

engine = create_async_engine(DATABASE_URL, **ENGINE_ARGS)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()