from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import configs

Base = declarative_base()

engine = create_engine(
    configs.DATABASE_URL,
    pool_timeout=30,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
