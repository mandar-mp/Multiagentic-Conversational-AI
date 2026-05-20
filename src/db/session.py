"""Database session and engine configuration."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings

connect_args = {}
if settings.db_type.lower() == "sqlite":
    connect_args["check_same_thread"] = False

engine = create_engine(settings.db_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables."""
    from .models import Base

    Base.metadata.create_all(bind=engine)
