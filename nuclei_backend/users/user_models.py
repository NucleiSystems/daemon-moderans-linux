from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from ..database import Base, engine

# iterate through the table and print the column names


class User(Base):

    # The User class is a Python class that inherits from the Base class. It has a bunch of columns that
    # are defined as class attributes

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    data = relationship("DataStorage", back_populates="owner")
    permanent_store = relationship("PermanentStore", back_populates="user_relationship")
