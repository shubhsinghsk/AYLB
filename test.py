"""Manual database smoke script: run with ``python test.py`` after installing dependencies."""

from sqlalchemy import select
from werkzeug.security import generate_password_hash

from AYLB_LOGIS import Base, SessionLocal, engine
from AYLB_LOGIS.models import User


def main():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "test_user"))
        if user is None:
            user = User(
                username="test_user",
                firstname="Test",
                lastname="User",
                email="test@example.com",
                phone_no="9999999999",
                password=generate_password_hash("test123"),
            )
            db.add(user)
            db.commit()
            print("Added test user")
        users = db.scalars(select(User)).all()
        print(f"Total users: {len(users)}")
        print(f"Found: {user.username} - {user.email}")


if __name__ == "__main__":
    main()
