from sqlalchemy import Column, Integer, String
from AYLB_LOGIS import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    firstname = Column(String(20), nullable=False)
    lastname = Column(String(20), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    phone_no = Column(String(10), unique=True, nullable=False)
    image_file = Column(String(20), nullable=False, default="default.jpg")
    password = Column(String(255), nullable=False)
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"User('{self.username}', {self.email})"
