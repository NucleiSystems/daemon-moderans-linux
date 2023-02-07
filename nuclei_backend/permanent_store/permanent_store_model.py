from sqlalchemy import (
    Table,
    create_engine,
    DateTime,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from ..database import Base, engine


class PermanentStore(Base):
    __tablename__ = "permanent_store"

    id = Column(Integer, primary_key=True, index=True)
    ccif_name = Column(String)
    username = Column(String)
    filename = Column(String)
    file_hash = Column(String)
    upload_date = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.id"))
    user_relationship = relationship("User", back_populates="permanent_store")
