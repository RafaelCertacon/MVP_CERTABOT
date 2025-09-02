from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from br.com.certacon.certabot.api.core.config import settings

# SQLite precisa do check_same_thread=False
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
