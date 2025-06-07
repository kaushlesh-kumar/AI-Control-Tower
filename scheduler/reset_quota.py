from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def reset_quotas():
    session = SessionLocal()
    users = session.query(User).all()
    for user in users:
        # Implement logic to reset quotas, e.g., user.quota = default_value
        pass
    session.commit()
    session.close()

if __name__ == "__main__":
    reset_quotas()
    print("Monthly quota reset complete.")

