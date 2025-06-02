
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DB_URL
engine=create_engine(DB_URL,echo=False,future=True)
SessionLocal=sessionmaker(bind=engine,expire_on_commit=False,future=True)
Base=declarative_base()
