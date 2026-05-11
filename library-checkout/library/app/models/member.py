import os
from sqlalchemy import Column, Integer, String
from app.database import Base


class Member(Base):
    __tablename__ = os.environ.get("DB_TABLE_MEMBERS", "members")

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
