from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class UserQuota(Base):
    __tablename__ = "user_quota"
