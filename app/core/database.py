from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> None:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Connected to Supabase successfully")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
