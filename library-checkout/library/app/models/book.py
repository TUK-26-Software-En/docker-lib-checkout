import os
from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class Book(Base):
    __tablename__ = os.environ.get("DB_TABLE_BOOKS", "books")

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    publisher = Column(String, nullable=False)
    available = Column(Boolean, default=True, nullable=False)
