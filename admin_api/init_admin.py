import os
from sqlalchemy.orm import Session
from models import User
from db import SessionLocal
from passlib.hash import bcrypt
from dotenv import load_dotenv


def create_default_admin():
    db: Session = SessionLocal()
    admin_email = os.environ.get("ADMIN_USERNAME", "admin@example.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    admin = db.query(User).filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            name="admin",
            email=admin_email,
            hashed_password=bcrypt.hash(admin_password),
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(admin)
        db.commit()
        print("Default admin created.")
    else:
        print("Admin already exists.")
    db.close()

if __name__ == "__main__":
    create_default_admin()