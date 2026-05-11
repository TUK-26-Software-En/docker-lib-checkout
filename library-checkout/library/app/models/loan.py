import os
import enum
from sqlalchemy import Column, Integer, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class LoanStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"


class Loan(Base):
    __tablename__ = os.environ.get("DB_TABLE_LOANS", "loans")

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey(f"{os.environ.get('DB_TABLE_BOOKS', 'books')}.id"), nullable=False)
    member_id = Column(Integer, ForeignKey(f"{os.environ.get('DB_TABLE_MEMBERS', 'members')}.id"), nullable=False)
    loan_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    status = Column(Enum(LoanStatus), default=LoanStatus.ACTIVE, nullable=False)

    book = relationship("Book")
    member = relationship("Member")
