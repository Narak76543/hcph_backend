from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import configs

engine = create_engine(
    configs.DATABASE_URL, 
    pool_timeout=30, 
    pool_pre_ping=True
)

Session = sessionmaker(bind=engine)
db = Session()

