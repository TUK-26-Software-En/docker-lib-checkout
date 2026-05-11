import pytest
from app.services.book_service import BookService
from app.services.member_service import MemberService
from app.services.loan_service import LoanService
from app.models.loan import LoanStatus


@pytest.fixture
def book_and_member(db):
    book = BookService(db).create_book("테스트 도서", "저자", "출판사")
    member = MemberService(db).create_member("홍길동", "hong@test.com")
    return db, book, member


def test_borrow_book(book_and_member):
    db, book, member = book_and_member
    loan = LoanService(db).borrow_book(member.id, book.id)
    assert loan.id is not None
    assert loan.status == LoanStatus.ACTIVE
    assert loan.return_date is None
    assert BookService(db).get_book(book.id).available is False


def test_borrow_unavailable_book_raises(book_and_member):
    db, book, member = book_and_member
    LoanService(db).borrow_book(member.id, book.id)
    with pytest.raises(ValueError, match="대출 중"):
        LoanService(db).borrow_book(member.id, book.id)


def test_borrow_nonexistent_book_raises(db):
    member = MemberService(db).create_member("홍길동", "hong@test.com")
    with pytest.raises(ValueError):
        LoanService(db).borrow_book(member.id, 9999)


def test_borrow_nonexistent_member_raises(db):
    book = BookService(db).create_book("테스트 도서", "저자", "출판사")
    with pytest.raises(ValueError):
        LoanService(db).borrow_book(9999, book.id)


def test_return_book(book_and_member):
    db, book, member = book_and_member
    loan = LoanService(db).borrow_book(member.id, book.id)
    returned = LoanService(db).return_book(loan.id)
    assert returned.status == LoanStatus.RETURNED
    assert returned.return_date is not None
    assert BookService(db).get_book(book.id).available is True


def test_return_already_returned_raises(book_and_member):
    db, book, member = book_and_member
    loan = LoanService(db).borrow_book(member.id, book.id)
    LoanService(db).return_book(loan.id)
    with pytest.raises(ValueError, match="이미 반납"):
        LoanService(db).return_book(loan.id)


def test_return_nonexistent_loan_raises(db):
    with pytest.raises(ValueError):
        LoanService(db).return_book(9999)


def test_get_all_loans(book_and_member):
    db, book, member = book_and_member
    LoanService(db).borrow_book(member.id, book.id)
    loans = LoanService(db).get_all_loans()
    assert len(loans) == 1
    assert loans[0].status == LoanStatus.ACTIVE
