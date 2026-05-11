from sqlalchemy.orm import Session, joinedload
from app.models.loan import Loan, LoanStatus


class LoanRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> list[Loan]:
        return self.db.query(Loan).options(
            joinedload(Loan.book), joinedload(Loan.member)
        ).all()

    def find_by_id(self, loan_id: int) -> Loan | None:
        return self.db.query(Loan).options(
            joinedload(Loan.book), joinedload(Loan.member)
        ).filter(Loan.id == loan_id).first()

    def find_active_by_book_id(self, book_id: int) -> Loan | None:
        return self.db.query(Loan).filter(
            Loan.book_id == book_id,
            Loan.status == LoanStatus.ACTIVE,
        ).first()

    def find_by_member_id(self, member_id: int) -> list[Loan]:
        return self.db.query(Loan).options(
            joinedload(Loan.book)
        ).filter(Loan.member_id == member_id).all()

    def save(self, loan: Loan) -> Loan:
        self.db.add(loan)
        self.db.commit()
        self.db.refresh(loan)
        return loan
