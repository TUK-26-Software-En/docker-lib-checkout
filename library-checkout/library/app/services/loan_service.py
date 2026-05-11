from datetime import date
from sqlalchemy.orm import Session
from app.models.loan import Loan, LoanStatus
from app.repositories.book_repository import BookRepository
from app.repositories.member_repository import MemberRepository
from app.repositories.loan_repository import LoanRepository


class LoanService:
    def __init__(self, db: Session):
        self.book_repo = BookRepository(db)
        self.member_repo = MemberRepository(db)
        self.loan_repo = LoanRepository(db)

    def get_all_loans(self) -> list[Loan]:
        return self.loan_repo.find_all()

    def borrow_book(self, member_id: int, book_id: int) -> Loan:
        book = self.book_repo.find_by_id(book_id)
        if not book:
            raise ValueError("도서를 찾을 수 없습니다.")
        if not book.available:
            raise ValueError(f"'{book.title}'은(는) 현재 대출 중입니다.")

        member = self.member_repo.find_by_id(member_id)
        if not member:
            raise ValueError("회원을 찾을 수 없습니다.")

        book.available = False
        self.book_repo.save(book)

        loan = Loan(
            book_id=book_id,
            member_id=member_id,
            loan_date=date.today(),
            status=LoanStatus.ACTIVE,
        )
        return self.loan_repo.save(loan)

    def return_book(self, loan_id: int) -> Loan:
        loan = self.loan_repo.find_by_id(loan_id)
        if not loan:
            raise ValueError("대출 기록을 찾을 수 없습니다.")
        if loan.status == LoanStatus.RETURNED:
            raise ValueError("이미 반납된 도서입니다.")

        loan.status = LoanStatus.RETURNED
        loan.return_date = date.today()
        self.loan_repo.save(loan)

        book = self.book_repo.find_by_id(loan.book_id)
        book.available = True
        self.book_repo.save(book)

        return loan
