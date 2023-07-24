from sqlalchemy import Column, Integer, String
from database import Base


class Contact(Base):
    __tablename__ = "Contacts"
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    surname = Column(String(256))
    phone = Column(String(256), nullable=False)
    email = Column(String(256))
