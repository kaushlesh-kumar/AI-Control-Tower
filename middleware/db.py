from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

DB_URL = os.getenv("DATABASE_URL", "mysql+pymysql://admin:dbmlflow@db:3306/mlflow")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
