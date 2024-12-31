# db/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base
from config.config import config


DATABASE_URL = config.DATABASE_URL

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
